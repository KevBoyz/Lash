import io
import json
import os
import re
import shutil
import socket
import socketserver
import sys
import tempfile
import threading
import time
import uuid
import zipfile
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import BinaryIO
from urllib.parse import parse_qs, urlsplit
from lash.plugins.share.helpers import (
    ShareEvent,
    content_disposition,
    device_name_from_ua,
    resolve_hostname,
    safe_filename,
)

DEFAULT_PORT = 8765
CHUNK = 65536
ONLINE_TIMEOUT = 10.0
RELAY_TIMEOUT = 60.0
LOG_LIMIT = 200
_DRAIN_LIMIT = 1 << 20
_PAGE = Path(__file__).parent / "static" / "index.html"
_LOOPBACK = {"127.0.0.1", "::1"}
_FILE_ROUTE = re.compile(r"^/api/files/([0-9a-f]{12})$")
_RELAY_ROUTE = re.compile(r"^/api/relay/([0-9a-f]{12})$")


def storage_dir() -> Path:
    return Path.home() / ".lash" / "data" / "share" / "files"


def reset_storage(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def cleanup_storage(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def new_file_id() -> str:
    return uuid.uuid4().hex[:12]


def zip_folder(folder: Path, target: Path) -> str:
    """Zip the files of `folder` without compression, under a root named after it.

    Same layout as the zip the page builds. Returns the zip name, e.g. 'photos.zip'.
    """
    root = folder.resolve()
    name = root.name or "folder"
    files = sorted(path for path in root.rglob("*") if path.is_file())
    with zipfile.ZipFile(target, "w", zipfile.ZIP_STORED, strict_timestamps=False) as zf:
        for path in files:
            zf.write(path, f"{name}/{path.relative_to(root).as_posix()}")
    return name + ".zip"


@dataclass
class Device:
    ip: str
    name: str
    last_seen: float


@dataclass
class SharedFile:
    id: str
    name: str
    size: int
    uploader_ip: str
    path: Path | None
    kind: str = "stored"  # "stored" (normal mode), "offer" (p2p host), "relay" (p2p device)
    page: str = ""        # page token of the host page that made an offer
    downloaded_by: set[str] = field(default_factory=set)


class ShareState:
    """Devices, files and who downloaded what in one share session. Thread-safe."""

    def __init__(self, host_ip: str = "", p2p: bool = False, host_name: str = "") -> None:
        self._lock = threading.Lock()
        self._host_ip = host_ip
        self._host_name = host_name
        self._p2p = p2p
        self._host_page = ""
        self._devices: dict[str, Device] = {}
        self._files: dict[str, SharedFile] = {}
        self._pulls: dict[str, str] = {}  # transfer id -> offered file id

    def touch(self, ip: str, fallback_name: str, now: float) -> bool:
        """Mark the device as seen. Returns True the first time it shows up."""
        with self._lock:
            device = self._devices.get(ip)
            if device is not None:
                device.last_seen = now
                return False
            self._devices[ip] = Device(ip, fallback_name, now)
            return True

    def set_name(self, ip: str, name: str) -> None:
        with self._lock:
            if ip in self._devices:
                self._devices[ip].name = name

    def device_name(self, ip: str) -> str:
        with self._lock:
            return self._name(ip)

    def _name(self, ip: str) -> str:
        device = self._devices.get(ip)
        if device is not None:
            return device.name
        # Files shared from the terminal come from the host before its page ever connects.
        return self._host_name if ip == self._host_ip and self._host_name else ip

    def add_file(self, file_id: str, name: str, size: int, uploader_ip: str,
                 path: Path | None, kind: str = "stored", page: str = "") -> SharedFile:
        with self._lock:
            shared = SharedFile(file_id, name, size, uploader_ip, path, kind, page)
            self._files[file_id] = shared
            return shared

    def get_file(self, file_id: str) -> SharedFile | None:
        with self._lock:
            return self._files.get(file_id)

    def remove_file(self, file_id: str) -> None:
        with self._lock:
            self._drop_files({file_id})

    def _drop_files(self, file_ids: set[str]) -> None:
        for file_id in file_ids:
            self._files.pop(file_id, None)
        self._pulls = {t: f for t, f in self._pulls.items() if f not in file_ids}

    def set_host_page(self, token: str) -> None:
        """A new host page lost the old page's files: drop its offers."""
        with self._lock:
            if token == self._host_page:
                return
            self._host_page = token
            self._drop_files({f.id for f in self._files.values()
                              if f.kind == "offer" and f.page != token})

    def prune_offers(self, now: float) -> None:
        """Drop the offers when the host page is gone."""
        with self._lock:
            host = self._devices.get(self._host_ip)
            if host is None or now - host.last_seen > ONLINE_TIMEOUT:
                self._drop_files({f.id for f in self._files.values() if f.kind == "offer"})

    def add_pull(self, transfer_id: str, file_id: str) -> None:
        with self._lock:
            self._pulls[transfer_id] = file_id

    def drop_pull(self, transfer_id: str) -> bool:
        with self._lock:
            return self._pulls.pop(transfer_id, None) is not None

    def release_download(self, file_id: str, ip: str) -> None:
        """Undo claim_download, so the device can try again."""
        with self._lock:
            shared = self._files.get(file_id)
            if shared is not None:
                shared.downloaded_by.discard(ip)

    def claim_download(self, file_id: str, ip: str) -> SharedFile | None:
        """Reserve the single download of a file for this device."""
        with self._lock:
            shared = self._files.get(file_id)
            if shared is None or ip == shared.uploader_ip or ip in shared.downloaded_by:
                return None
            shared.downloaded_by.add(ip)
            return shared

    def snapshot(self, ip: str, now: float) -> dict:
        """Everything the page of the device `ip` needs to render."""
        with self._lock:
            is_host = ip == self._host_ip
            files = [f for f in reversed(self._files.values())
                     if f.kind != "relay" or is_host or f.uploader_ip == ip]
            return {
                "mode": "p2p" if self._p2p else "normal",
                "me": {"ip": ip, "name": self._name(ip), "host": is_host},
                "pulls": [{"transfer": t, "file": f} for t, f in self._pulls.items()]
                if is_host else [],
                "devices": [
                    {"ip": d.ip, "name": d.name, "me": d.ip == ip}
                    for d in self._devices.values()
                    if now - d.last_seen <= ONLINE_TIMEOUT
                ],
                "available": [
                    {"id": f.id, "name": f.name, "size": f.size,
                     "from": self._name(f.uploader_ip), "downloaded": ip in f.downloaded_by}
                    for f in files if f.uploader_ip != ip
                ],
                "uploads": [
                    {"id": f.id, "name": f.name, "size": f.size,
                     "downloads": len(f.downloaded_by)}
                    for f in files if f.uploader_ip == ip
                ],
            }


class EventLog:
    """Last log lines of the session with growing ids, for the page's terminal. Thread-safe."""

    def __init__(self, limit: int = LOG_LIMIT) -> None:
        self._lock = threading.Lock()
        self._lines: deque[tuple[int, str]] = deque(maxlen=limit)
        # Ids start at the clock (ms), so they keep growing across runs:
        # a page left open from an earlier run still gets the new lines.
        self._next = time.time_ns() // 1_000_000

    def add(self, text: str) -> None:
        with self._lock:
            self._lines.append((self._next, text))
            self._next += 1

    def since(self, after: int) -> list[dict]:
        """Lines with an id greater than `after` (0 = all)."""
        with self._lock:
            return [{"id": i, "text": text} for i, text in self._lines if i > after]


class _PendingSend:
    def __init__(self, stream: BinaryIO, size: int):
        self.stream = stream
        self.size = size
        self.picked = False
        self.ok = False
        self.done = threading.Event()


class RelayPipe:
    """A sender handed to a receiver: copy_to moves the sender's bytes out."""

    def __init__(self, pending: _PendingSend):
        self._pending = pending
        self.size = pending.size

    def copy_to(self, out: BinaryIO) -> bool:
        """Copy exactly `size` bytes; False if the sender ended early or a side failed."""
        ok = False
        try:
            remaining = self.size
            while remaining:
                chunk = self._pending.stream.read(min(CHUNK, remaining))
                if not chunk:
                    return False
                out.write(chunk)
                remaining -= len(chunk)
            out.flush()
            ok = True
            return True
        except OSError:
            return False
        finally:
            self._finish(ok)

    def close(self) -> None:
        """Release the sender without copying (no-op after copy_to)."""
        self._finish(False)

    def _finish(self, ok: bool) -> None:
        if not self._pending.done.is_set():
            self._pending.ok = ok
            self._pending.done.set()


class Relay:
    """Meeting point that pipes one request body into another request's response."""

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._senders: dict[str, _PendingSend] = {}

    def send(self, key: str, stream: BinaryIO, size: int, timeout: float) -> bool:
        """Wait for a receiver of `key` and block until it copied the stream."""
        pending = _PendingSend(stream, size)
        with self._cond:
            self._senders[key] = pending
            self._cond.notify_all()
            if not self._cond.wait_for(lambda: pending.picked, timeout):
                if self._senders.get(key) is pending:
                    del self._senders[key]
                return False
        pending.done.wait()
        return pending.ok

    def receive(self, key: str, timeout: float) -> RelayPipe | None:
        """Wait for a sender of `key` and take it."""
        with self._cond:
            if not self._cond.wait_for(lambda: key in self._senders, timeout):
                return None
            pending = self._senders.pop(key)
            pending.picked = True
            self._cond.notify_all()
        return RelayPipe(pending)


def render_qr(url: str) -> str:
    """QR code of the url drawn with text blocks, ready to print in a terminal."""
    import qrcode
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make(fit=True)
    buf = io.StringIO()
    qr.print_ascii(out=buf, invert=True)
    return buf.getvalue()


def qr_svg(url: str) -> str:
    """QR code of the url as an SVG image: the page's green modules on black."""
    import qrcode
    qr = qrcode.QRCode(border=1)  # the page's black around it completes the quiet zone
    qr.add_data(url)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    size = len(matrix)
    modules = "".join(f"M{x} {y}h1v1h-1z"
                      for y, row in enumerate(matrix) for x, dark in enumerate(row) if dark)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
            f'shape-rendering="crispEdges"><rect width="{size}" height="{size}" fill="#000"/>'
            f'<path d="{modules}" fill="#00ff41"/></svg>')


class _HttpServer(ThreadingHTTPServer):
    daemon_threads = True
    # On Windows SO_REUSEADDR lets a second server bind a port already in use.
    allow_reuse_address = sys.platform != "win32"

    def __init__(self, address, app: "ShareServer"):
        self.app = app
        super().__init__(address, _Handler)

    def server_bind(self):
        # HTTPServer.server_bind resolves the FQDN of 0.0.0.0, which takes ~1 s on Windows.
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], ConnectionError):
            return
        super().handle_error(request, client_address)


class _Handler(BaseHTTPRequestHandler):
    server: _HttpServer

    def log_message(self, format, *args):
        pass

    @property
    def app(self) -> "ShareServer":
        return self.server.app

    def _route(self) -> tuple[str, dict[str, str], str]:
        """Path, query and client IP of the request; marks the client as seen."""
        parts = urlsplit(self.path)
        query = {key: values[0] for key, values in parse_qs(parts.query).items()}
        ip = self.client_address[0]
        if ip in _LOOPBACK:
            ip = self.app.host_ip
        self._unread = self._content_length() or 0
        self.app.seen(ip, self.headers.get("User-Agent", ""))
        return parts.path, query, ip

    def _drain(self) -> None:
        """Read what is left of the request body before replying.

        Closing a socket with unread data sends a TCP reset (always on Windows),
        and the client loses the reply. Bodies above the limit are dropped anyway.
        """
        remaining = min(getattr(self, "_unread", 0), _DRAIN_LIMIT)
        self._unread = 0
        try:
            while remaining > 0:
                chunk = self.rfile.read(min(CHUNK, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
        except OSError:
            pass

    def _is_host(self, ip: str) -> bool:
        return self.app.p2p and ip == self.app.host_ip

    def do_GET(self):
        path, query, ip = self._route()
        if path == "/":
            self._send(200, _PAGE.read_bytes(), "text/html; charset=utf-8")
        elif path == "/qr.svg":
            self._qr()
        elif path == "/api/state":
            self._state(query, ip)
        elif match := _FILE_ROUTE.match(path):
            self._download(match.group(1), ip)
        else:
            self._send_json(404, {"error": "not found"})

    def do_PUT(self):
        path, query, ip = self._route()
        if path == "/api/upload":
            if not self.app.p2p:
                self._upload(query.get("name", ""), ip)
            elif self._is_host(ip):
                self._send_json(403, {"error": "the host page offers files in p2p mode"})
            else:
                self._relay_upload(query.get("name", ""), ip)
        elif match := _RELAY_ROUTE.match(path):
            self._relay_offer(match.group(1), ip)
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        path, query, ip = self._route()
        if path == "/api/offer":
            self._offer(query, ip)
        else:
            self._send_json(404, {"error": "not found"})

    def _state(self, query: dict[str, str], ip: str) -> None:
        app = self.app
        page = query.get("page", "")
        if page and self._is_host(ip):
            app.state.set_host_page(page)
        try:
            last_log = int(query.get("log", "0"))
        except ValueError:
            last_log = 0
        now = time.monotonic()
        app.state.prune_offers(now)
        self._send_json(200, {**app.state.snapshot(ip, now), "logs": app.log.since(last_log)})

    def _qr(self) -> None:
        try:
            svg = qr_svg(self.app.url)
        except ImportError:
            self._send_json(404, {"error": "qrcode not installed"})
            return
        self._send(200, svg.encode("utf-8"), "image/svg+xml")

    def _offer(self, query: dict[str, str], ip: str) -> None:
        """p2p host announces a file that stays in its browser until someone asks."""
        app = self.app
        if not self._is_host(ip):
            self._send_json(403, {"error": "only the host page can offer files in p2p mode"})
            return
        name = query.get("name", "")
        try:
            size = int(query.get("size", ""))
        except ValueError:
            size = -1
        if not name or size < 0:
            self._send_json(400, {"error": "name and size are required"})
            return
        page = query.get("page", "")
        app.state.set_host_page(page)
        shared = app.state.add_file(new_file_id(), safe_filename(name), size, ip, None,
                                    kind="offer", page=page)
        app.emit(ShareEvent("shared", app.state.device_name(ip), ip, shared.name, size))
        self._send_json(201, {"id": shared.id, "name": shared.name, "size": shared.size})

    def _relay_upload(self, name: str, ip: str) -> None:
        """p2p device sends a file: hold the request until the host page pulls it."""
        app = self.app
        if not name:
            self._send_json(400, {"error": "missing name"})
            return
        length = self._content_length()
        if length is None:
            self._send_json(411, {"error": "missing Content-Length"})
            return
        shared = app.state.add_file(new_file_id(), safe_filename(name), length, ip, None,
                                    kind="relay")
        # The "sent" event is emitted by the receiving side, right before "downloaded".
        if not app.relay.send(shared.id, self.rfile, length, app.relay_timeout):
            app.state.remove_file(shared.id)
            self._send_json(504, {"error": "PC offline"})
            return
        self._unread = 0
        self._send_json(201, {"id": shared.id, "name": shared.name, "size": shared.size})

    def _relay_offer(self, transfer_id: str, ip: str) -> None:
        """p2p host page sends an offered file to the device waiting for it."""
        app = self.app
        if not self._is_host(ip):
            self._send_json(403, {"error": "only the host page can send offered files"})
            return
        if not app.state.drop_pull(transfer_id):
            self._send_json(404, {"error": "unknown transfer"})
            return
        length = self._content_length()
        if length is None:
            self._send_json(411, {"error": "missing Content-Length"})
            return
        if app.relay.send(transfer_id, self.rfile, length, app.relay_timeout):
            self._unread = 0
            self._send_json(200, {"ok": True})
        else:
            self._send_json(504, {"error": "device gone"})

    def _content_length(self) -> int | None:
        try:
            length = int(self.headers["Content-Length"])
        except (TypeError, ValueError):
            return None
        return length if length >= 0 else None

    def _receive(self, target: Path, length: int) -> bool:
        """Stream the request body to `target` through a .part file."""
        part = target.with_name(target.name + ".part")
        done = False
        self._unread = 0  # the body is consumed here, even when the client gives up
        try:
            with part.open("wb") as out:
                remaining = length
                while remaining:
                    chunk = self.rfile.read(min(CHUNK, remaining))
                    if not chunk:
                        return False
                    out.write(chunk)
                    remaining -= len(chunk)
            os.replace(part, target)
            done = True
            return True
        finally:
            if not done:
                part.unlink(missing_ok=True)

    def _upload(self, name: str, ip: str) -> None:
        app = self.app
        if not name:
            self._send_json(400, {"error": "missing name"})
            return
        length = self._content_length()
        if length is None:
            self._send_json(411, {"error": "missing Content-Length"})
            return
        file_id = new_file_id()
        target = app.storage / file_id
        if not self._receive(target, length):
            self._send_json(400, {"error": "incomplete upload"})
            return
        shared = app.state.add_file(file_id, safe_filename(name), length, ip, target)
        app.emit(ShareEvent("sent", app.state.device_name(ip), ip, shared.name, length))
        self._send_json(201, {"id": shared.id, "name": shared.name, "size": shared.size})

    def _download(self, file_id: str, ip: str) -> None:
        state = self.app.state
        if state.get_file(file_id) is None:
            self._send_json(404, {"error": "not found"})
            return
        shared = state.claim_download(file_id, ip)
        if shared is None:
            self._send_json(410, {"error": "already downloaded"})
            return
        ok = (self._send_stored(shared) if shared.kind == "stored"
              else self._pipe_download(shared, ip))
        if ok:
            self.app.emit(ShareEvent("downloaded", state.device_name(ip), ip, shared.name))

    def _send_stored(self, shared: SharedFile) -> bool:
        """Stream a file from disk. False if it is gone or the client left."""
        try:
            src = shared.path.open("rb")
        except OSError:
            # A file shared from the terminal was moved or deleted after startup.
            self.app.state.remove_file(shared.id)
            self._send_json(404, {"error": "file no longer exists"})
            return False
        with src:
            try:
                self._send_file_headers(shared.name, os.fstat(src.fileno()).st_size)
                shutil.copyfileobj(src, self.wfile, CHUNK)
            except ConnectionError:
                return False
        return True

    def _pipe_download(self, shared: SharedFile, ip: str) -> bool:
        """Stream a p2p file from the browser that holds it. False if it never came."""
        app = self.app
        if shared.kind == "relay":
            key = shared.id
        else:
            key = new_file_id()
            app.state.add_pull(key, shared.id)
        pipe = app.relay.receive(key, app.relay_timeout)
        if pipe is None:
            app.state.drop_pull(key)
            app.state.release_download(shared.id, ip)
            self._send_json(504, {"error": "PC offline"})
            return False
        try:
            self._send_file_headers(shared.name, pipe.size)
            ok = pipe.copy_to(self.wfile)
        except ConnectionError:
            ok = False
        finally:
            pipe.close()
        if ok and shared.kind == "relay":
            uploader = shared.uploader_ip
            app.emit(ShareEvent("sent", app.state.device_name(uploader), uploader,
                                    shared.name, shared.size))
        return ok

    def _send_file_headers(self, name: str, size: int) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(size))
        self.send_header("Content-Disposition", content_disposition(name))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self._drain()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, data: dict) -> None:
        self._send(status, json.dumps(data).encode("utf-8"), "application/json")


class ShareServer:
    """HTTP server of the share page, listening on every interface."""

    def __init__(self, storage: Path | None, host_ip: str, port: int = DEFAULT_PORT,
                 on_event: Callable[[ShareEvent], None] | None = None,
                 resolve_name: Callable[[str], str | None] | None = None,
                 p2p: bool = False, relay_timeout: float = RELAY_TIMEOUT):
        self.host_ip = host_ip
        self.p2p = p2p
        self.storage = None if p2p else storage
        self._on_event = on_event or (lambda event: None)
        self.log = EventLog()
        self.resolve_name = resolve_name or resolve_hostname
        self.relay_timeout = relay_timeout
        self.relay = Relay()
        self.state = ShareState(host_ip, p2p, socket.gethostname())
        self._temp: Path | None = None
        self._httpd = _HttpServer(("0.0.0.0", port), self)
        self.port = self._httpd.server_address[1]
        if self.storage is not None:
            reset_storage(self.storage)

    @property
    def url(self) -> str:
        return f"http://{self.host_ip}:{self.port}"

    def emit(self, event: ShareEvent) -> None:
        """Record an event in the page's log and hand it to the on_event callback."""
        self.log.add(str(event))
        self._on_event(event)

    def seen(self, ip: str, user_agent: str) -> None:
        """Register a request from `ip`, logging new devices right away."""
        if not self.state.touch(ip, device_name_from_ua(user_agent), time.monotonic()):
            return
        if ip == self.host_ip:
            self.state.set_name(ip, socket.gethostname())
        self.emit(ShareEvent("connected", self.state.device_name(ip), ip))
        if ip != self.host_ip:
            # Reverse DNS can take seconds on Windows: resolve without holding the request.
            threading.Thread(target=self._identify, args=(ip,), daemon=True).start()

    def _identify(self, ip: str) -> None:
        name = self.resolve_name(ip)
        previous = self.state.device_name(ip)
        if name and name != previous:
            self.state.set_name(ip, name)
            self.emit(ShareEvent("renamed", name, ip, previous=previous))

    def share_file(self, path: Path, name: str = "") -> SharedFile:
        """Send a file of this computer to every device, as if the host page sent it.

        The file is read from where it is: nothing is copied and it is never deleted.
        """
        shared = self.state.add_file(new_file_id(), safe_filename(name or path.name),
                                     path.stat().st_size, self.host_ip, path)
        self.emit(ShareEvent("shared", self.state.device_name(self.host_ip), self.host_ip,
                             shared.name, shared.size))
        return shared

    def share_folder(self, folder: Path) -> SharedFile:
        """Zip a folder of this computer and send the zip to every device."""
        target = self._scratch() / new_file_id()
        return self.share_file(target, zip_folder(folder, target))

    def _scratch(self) -> Path:
        """Folder for generated zips: the storage, or a temp folder in p2p mode."""
        if self.storage is not None:
            return self.storage
        if self._temp is None:
            self._temp = Path(tempfile.mkdtemp(prefix="lash-share-"))
        return self._temp

    def serve_forever(self) -> None:
        self._httpd.serve_forever()

    def shutdown(self) -> None:
        self._httpd.shutdown()

    def close(self) -> None:
        self._httpd.server_close()
        if self.storage is not None:
            cleanup_storage(self.storage)
        if self._temp is not None:
            cleanup_storage(self._temp)
