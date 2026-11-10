import re
import socket
import unicodedata
from urllib.parse import quote

_OS_RULES = [
    ("iPhone", "iPhone"),
    ("iPad", "iPad"),
    ("Android", "Android"),
    ("Windows", "Windows"),
    ("Mac OS X", "macOS"),
    ("Linux", "Linux"),
]
_BROWSER_RULES = [
    (("Edg/",), "Edge"),
    (("OPR/",), "Opera"),
    (("Firefox/", "FxiOS"), "Firefox"),
    (("Chrome/", "CriOS"), "Chrome"),
    (("Safari/",), "Safari"),
]
_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_MAX_NAME = 200


def device_name_from_ua(user_agent: str) -> str:
    """Readable device name from a browser User-Agent, e.g. 'Android · Chrome'."""
    os_name = next((name for key, name in _OS_RULES if key in user_agent), "Unknown")
    browser = next((name for keys, name in _BROWSER_RULES
                    if any(k in user_agent for k in keys)), "Browser")
    return f"{os_name} · {browser}"


def resolve_hostname(ip: str) -> str | None:
    """Machine name of an IP via reverse DNS, or None when it can't be found."""
    try:
        name = socket.gethostbyaddr(ip)[0]
    except OSError:
        return None
    name = name.split(".")[0] if name != ip else ""
    return name or None


def detect_lan_ip() -> str:
    """IP of this computer on the local network (no packet is sent)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("10.255.255.255", 1))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def safe_filename(name: str) -> str:
    """Base name safe to show and save on any OS."""
    base = re.split(r"[/\\]", name)[-1]
    base = _FORBIDDEN.sub("_", base).rstrip(". ")
    return (base or "file")[:_MAX_NAME]


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    value = float(size)
    for unit in ("KB", "MB", "GB"):
        value /= 1024
        if value < 1024:
            return f"{value:.1f} {unit}"
    return f"{value / 1024:.1f} TB"


def content_disposition(name: str) -> str:
    """Attachment header keeping non-ASCII names (RFC 5987)."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    ascii_name = ascii_name.replace('"', "_").replace("\\", "_") or "file"
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name, safe='')}"
