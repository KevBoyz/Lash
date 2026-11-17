import json
import socket
import sys

MSG_HEADER = 4


def decode_console(data: bytes) -> str:
    """Decode subprocess output captured from a shell command.

    Windows console builtins (``dir``, ``vol``, ``wmic``) print text in the
    OEM code page (e.g. cp850 on pt-BR Windows), not UTF-8 or ANSI. Decoding
    those bytes as UTF-8/ANSI turns accented characters into mojibake such as
    ``r¢tulo`` / ``informa‡äes``. Try UTF-8 first (modern tools and pure
    ASCII), then fall back to the OEM code page.
    """
    if not data:
        return ""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        fallback = "oem" if sys.platform == "win32" else "latin-1"
        return data.decode(fallback, errors="replace")


def send_msg(sock: socket.socket, data: dict) -> None:
    payload = json.dumps(data).encode("utf-8")
    header = len(payload).to_bytes(MSG_HEADER, "big")
    sock.sendall(header + payload)


def recv_msg(sock: socket.socket, *, max_size: int | None = None) -> dict:
    header = _recv_exact(sock, MSG_HEADER)
    length = int.from_bytes(header, "big")
    if max_size is not None and length > max_size:
        raise ValueError(f"Message exceeds {max_size} bytes")
    payload = _recv_exact(sock, length)
    return json.loads(payload.decode("utf-8"))


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Socket closed mid-read")
        data += chunk
    return data
