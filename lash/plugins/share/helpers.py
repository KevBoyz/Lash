import re
import socket
import time
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote
from rich.text import Text

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
_EVENT_TAGS = {
    "connected": ("[+]", "bold green"),
    "renamed": ("[~]", "bold yellow"),
    "sent": ("[>]", "bold cyan"),
    "shared": ("[>]", "bold blue"),
    "downloaded": ("[<]", "bold magenta"),
}


@dataclass(frozen=True)
class ShareEvent:
    """Something that happened in a share session, shown in the terminal log."""
    kind: str  # connected | renamed | sent | shared | downloaded
    device: str
    ip: str
    file: str = ""
    size: int = 0
    previous: str = ""  # old device name, for "renamed"
    at: float = field(default_factory=time.time)  # when it happened (epoch seconds)

    def __str__(self) -> str:
        return format_event(self).plain


def format_event(event: ShareEvent) -> Text:
    """Colored log line of an event, starting with its time: 'hh:mm [+] ...'."""
    clock = time.strftime("%H:%M ", time.localtime(event.at))
    tag, style = _EVENT_TAGS[event.kind]
    ip = (f"({event.ip})", "dim")
    if event.kind == "connected":
        parts = [(event.device, "bold"), " ", ip, " connected"]
    elif event.kind == "renamed":
        parts = [(event.previous, "bold"), " ", ip, " identified as ", (event.device, "bold")]
    elif event.kind == "downloaded":
        parts = [(event.device, "bold"), " downloaded ", (event.file, "bright_white")]
    else:
        parts = [(event.device, "bold"), f" {event.kind} ", (event.file, "bright_white"),
                 " ", (f"({format_size(event.size)})", "dim")]
    return Text.assemble(clock, (tag, style), " ", *parts)


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


def split_paths(values: Iterable[str]) -> list[Path]:
    """Paths of comma-separated option values, without blanks or repeats."""
    parts = (part.strip() for value in values for part in value.split(","))
    return list(dict.fromkeys(Path(part).expanduser() for part in parts if part))


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
