import secrets
import string
import pyaes


def generate_key():
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(16))


def crypt_file(path, bkey, decrypt):
    with open(path, "rb") as src:
        data = src.read()
    crip = pyaes.AESModeOfOperationCTR(bkey)
    out = crip.decrypt(data) if decrypt else crip.encrypt(data)
    with open(path, "wb") as dst:
        dst.write(out)


def bar_template():
    return "%(label)s  %(bar)s  %(info)s"


def get_ext(file="", path=""):
    if path:
        index = path.rfind("\\")
        return path[index + 1:]
    else:
        index = file.rfind(".")
        return file[index:].lower()


def file_types():
    return {
        "midia": {
            "images": (".png", ".jpeg", ".gif", ".bmp", ".tiff", ".svg"),
            "musics": (".mp3", ".waw", ".ogg", ".wma"),
            "videos": (".mp4", ".avi", ".wmv", ".mov", ".avchd"),
        },
        "docs": (".pdf", ".ppt", ".docx", ".txt", ".xls", ".doc"),
    }
