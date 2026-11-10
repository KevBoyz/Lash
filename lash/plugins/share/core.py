import io
import json
import os
import re
import shutil
import socket
import socketserver
import sys
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import BinaryIO
from urllib.parse import parse_qs, urlsplit
from lash.plugins.share.helpers import (
    content_disposition,
    device_name_from_ua,
    format_size,
    resolve_hostname,
    safe_filename,
)

DEFAULT_PORT = 8765
CHUNK = 65536
ONLINE_TIMEOUT = 10.0
RELAY_TIMEOUT = 60.0
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

    def __init__(self, host_ip: str = "", p2p: bool = False) -> None:
        self._lock = threading.Lock()
        self._host_ip = host_ip
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
        return device.name if device else ip

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
        self.app.seen(ip, self.headers.get("User-Agent", ""))
        return parts.path, query, ip

    def _is_host(self, ip: str) -> bool:
        return self.app.p2p and ip == self.app.host_ip

    def do_GET(self):
        path, query, ip = self._route()
        if path == "/":
            self._send(200, _PAGE.read_bytes(), "text/html; charset=utf-8")
        elif path == "/api/state":
            self._state(query.get("page", ""), ip)
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

    def _state(self, page: str, ip: str) -> None:
        state = self.app.state
        if page and self._is_host(ip):
            state.set_host_page(page)
        now = time.monotonic()
        state.prune_offers(now)
        self._send_json(200, state.snapshot(ip, now))

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
        app.on_event(f"[>] {app.state.device_name(ip)} shared {shared.name} ({format_size(size)})")
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
        if not app.relay.send(shared.id, self.rfile, length, app.relay_timeout):
            app.state.remove_file(shared.id)
            self._send_json(504, {"error": "PC offline"})
            return
        app.on_event(f"[>] {app.state.device_name(ip)} sent {shared.name} ({format_size(length)})")
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
        app.on_event(f"[>] {app.state.device_name(ip)} sent {shared.name} ({format_size(length)})")
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
        if shared.kind == "stored":
            self._send_file_headers(shared.name, shared.size)
            try:
                with shared.path.open("rb") as src:
                    shutil.copyfileobj(src, self.wfile, CHUNK)
            except ConnectionError:
                return
        elif not self._pipe_download(shared, ip):
            return
        self.app.on_event(f"[<] {state.device_name(ip)} downloaded {shared.name}")

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
            return pipe.copy_to(self.wfile)
        except ConnectionError:
            return False
        finally:
            pipe.close()

    def _send_file_headers(self, name: str, size: int) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(size))
        self.send_header("Content-Disposition", content_disposition(name))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _send(self, status: int, body: bytes, content_type: str) -> None:
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
                 on_event: Callable[[str], None] | None = None,
                 resolve_name: Callable[[str], str | None] | None = None,
                 p2p: bool = False, relay_timeout: float = RELAY_TIMEOUT):
        self.host_ip = host_ip
        self.p2p = p2p
        self.storage = None if p2p else storage
        self.on_event = on_event or (lambda message: None)
        self.resolve_name = resolve_name or resolve_hostname
        self.relay_timeout = relay_timeout
        self.relay = Relay()
        self.state = ShareState(host_ip, p2p)
        self._httpd = _HttpServer(("0.0.0.0", port), self)
        self.port = self._httpd.server_address[1]
        if self.storage is not None:
            reset_storage(self.storage)

    @property
    def url(self) -> str:
        return f"http://{self.host_ip}:{self.port}"

    def seen(self, ip: str, user_agent: str) -> None:
        """Register a request from `ip`; new devices get their name resolved."""
        if self.state.touch(ip, device_name_from_ua(user_agent), time.monotonic()):
            threading.Thread(target=self._announce, args=(ip,), daemon=True).start()

    def _announce(self, ip: str) -> None:
        name = socket.gethostname() if ip == self.host_ip else self.resolve_name(ip)
        if name:
            self.state.set_name(ip, name)
        self.on_event(f"[+] {self.state.device_name(ip)} ({ip}) connected")

    def serve_forever(self) -> None:
        self._httpd.serve_forever()

    def shutdown(self) -> None:
        self._httpd.shutdown()

    def close(self) -> None:
        self._httpd.server_close()
        if self.storage is not None:
            cleanup_storage(self.storage)
