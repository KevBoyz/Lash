import os
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime
from itertools import product
from pathlib import Path

from lash.plugins.spider.helpers import send_msg, recv_msg


def port_verify(port: str) -> int:
    try:
        return int(port)
    except ValueError:
        raise ValueError(f"Invalid port [{port}], must be an integer like 8080")


def run_web_client(host: str, port: int) -> None:
    local_ip = socket.gethostbyname(socket.gethostname())
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        welcome = recv_msg(s)
        if "lash" not in welcome:
            return
        while True:
            try:
                msg = recv_msg(s)
            except (ConnectionError, OSError):
                break
            if msg.get("type") != "cmd":
                continue
            result = subprocess.run(
                msg["data"], shell=True, capture_output=True, text=True
            )
            output = result.stdout + result.stderr
            send_msg(s, {"type": "result", "data": output, "addr": local_ip})


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
                f" -> lash {server_cmd} -c {ip} {port}\n"
            )

        _spawn_client(server_cmd, ip, port)


def _spawn_client(server_cmd: str, ip: str, port: int) -> None:
    argv = [sys.executable, "-m", "lash", server_cmd, "-c", ip, str(port)]
    if sys.platform == "win32":
        subprocess.Popen(
            argv,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
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
        sys.executable, "-m", "lash", "seeker",
        addresses, ports,
        "--ping", str(ping_interval),
        "--_daemon",
    ]
    if sys.platform == "win32":
        subprocess.Popen(
            argv,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
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
