import click
import os
import secrets
import string
import shutil as sh
from rich import print
import pyaes as pya
from lash.plugins.file.core import (
    bar_template,
    file_types,
    get_ext,
)


@click.group()
def file():
    """File organization and encryption tools."""


def _generate_key():
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(16))


def _crypt_file(path, bkey, decrypt):
    with open(path, "rb") as src:
        data = src.read()
    crip = pya.AESModeOfOperationCTR(bkey)
    out = crip.decrypt(data) if decrypt else crip.encrypt(data)
    with open(path, "wb") as dst:
        dst.write(out)


@click.command()
@click.argument(
    "p",
    metavar="path",
    type=click.Path(exists=True),
    required=False,
    default=".",
)
@click.argument("key", metavar="<key>", type=click.STRING, required=False)
@click.option("-dc", is_flag=True, default=False, help="Decrypt instead of encrypt")
@click.option("-ex", is_flag=True, default=False, help="Export key to recovery-key.txt")
@click.option("-ca", is_flag=True, default=False, help="Crypt all files in a folder")
@click.option("-v", is_flag=True, default=False, help="Verbose mode")
def crypt(p, key, dc, ex, ca, v):  # noqa: C901
    """\b
    Encrypt/Decrypt files with AES algorithm

    \b
    Pass a 16-char key or omit to generate one automatically.
    Generated keys are printed at the end — save them to decrypt later.

    \b
    Ex:
      crypt secret.txt                     # auto-generate key
      crypt secret.txt $kvzis1@7y602qsx    # custom key
      crypt mydir -ca                      # encrypt folder (progress bar)
      crypt secret.txt mykey -dc           # decrypt
    """
    if dc and not key:
        raise click.UsageError("Key is required for decryption (-dc).")
    if key is not None and len(key) != 16:
        raise click.UsageError("Key must be exactly 16 characters.")

    generated = key is None
    if generated:
        key = _generate_key()
    bkey = str.encode(key)

    if p.find("\\") == -1 and p.find("/") == -1:
        fp = os.path.join(".", p)
    else:
        fp = p

    if ca:
        if not os.path.isdir(fp):
            raise click.UsageError(f"-ca requires a directory, got: {fp}")
        targets = []
        for root, _, files in os.walk(fp):
            for name in files:
                targets.append(os.path.join(root, name))
        if not targets:
            click.echo("No files to process.")
            return
        with click.progressbar(
            targets,
            label="Decrypting" if dc else "Encrypting",
            empty_char="─",
            fill_char="█",
            bar_template=bar_template(),
        ) as bar:
            for path in bar:
                try:
                    _crypt_file(path, bkey, dc)
                except Exception as e:
                    click.echo(f"\n[skip] {path}: {e}", err=True)
    else:
        if not os.path.isfile(fp):
            raise click.UsageError(f"Expected a file, got: {fp}. Use -ca for folders.")
        _crypt_file(fp, bkey, dc)
        if v:
            print("\nFile decrypted" if dc else "\nFile encrypted")

    if ex:
        if ca:
            key_path = os.path.join(fp, "recovery-key.txt")
        else:
            d = os.path.dirname(fp)
            key_path = os.path.join(d, "recovery-key.txt") if d else "recovery-key.txt"
        open(key_path, "w").write(key)

    if generated and not dc:
        print(f"\n[bold yellow]Generated key:[/bold yellow] [cyan]{key}[/cyan]")
        print("[dim]Save this key — it is required to decrypt.[/dim]")


@click.command()
@click.argument(
    "path",
    metavar="<path>",
    type=click.Path(exists=True),
    required=False,
    default=".",
)
@click.option("-t", type=click.STRING, help="Organize files per type")
@click.option(
    "-m",
    is_flag=True,
    default=False,
    show_default=True,
    help="Group media into Images/, Videos/, Musics/",
)
@click.option(
    "-d",
    is_flag=True,
    default=True,
    show_default=True,
    help="Group documents into Docs/",
)
@click.option(
    "-o",
    is_flag=True,
    default=True,
    show_default=True,
    help="Create ~Others~ folder",
)
@click.option("-v", is_flag=True, default=True, show_default=True, help="Verbose mode")
def organize(path, t, m, d, o, v):  # noqa: C901
    """
    Organize your files (top-level only — subfolders are left untouched).

    \b
    Organize a folder in a simple way, by predefined execution that
    separates files according to their context or in a personalized way
    searching for a specific type.
    [!Important] - Do not use ('') to declare TYPE on -t option set the
    value like: -t pdf
    """
    base = os.path.abspath(path)
    try:
        if t:
            if not t.startswith("."):
                t = "." + t
            dest = os.path.join(base, f"({t}) Files")
            os.makedirs(dest, exist_ok=True)
            for name in os.listdir(base):
                src = os.path.join(base, name)
                if not os.path.isfile(src):
                    continue
                if get_ext(name) != t:
                    continue
                if v:
                    print(f"Moving: {name}")
                try:
                    sh.move(src, os.path.join(dest, name))
                except Exception as e:
                    print(f"[red]Skip[/red] {name}: {e}")
            return

        ft = file_types()
        if m:
            os.makedirs(os.path.join(base, "Media", "Images"), exist_ok=True)
            os.makedirs(os.path.join(base, "Media", "Videos"), exist_ok=True)
            os.makedirs(os.path.join(base, "Media", "Musics"), exist_ok=True)
        if d:
            os.makedirs(os.path.join(base, "Docs"), exist_ok=True)
        if o:
            os.makedirs(os.path.join(base, "Others"), exist_ok=True)

        entries = [n for n in os.listdir(base) if os.path.isfile(os.path.join(base, n))]
        with click.progressbar(
            entries,
            empty_char="─",
            fill_char="█",
            bar_template=bar_template(),
        ) as bar:
            for name in bar:
                src = os.path.join(base, name)
                if not os.path.exists(src):
                    continue
                ext = get_ext(name)
                dest = None
                if m and ext in ft["midia"]["images"]:
                    dest = os.path.join(base, "Media", "Images", name)
                elif m and ext in ft["midia"]["videos"]:
                    dest = os.path.join(base, "Media", "Videos", name)
                elif m and ext in ft["midia"]["musics"]:
                    dest = os.path.join(base, "Media", "Musics", name)
                elif d and ext in ft["docs"]:
                    dest = os.path.join(base, "Docs", name)
                elif o:
                    dest = os.path.join(base, "Others", name)
                if dest is None:
                    continue
                try:
                    sh.move(src, dest)
                except Exception as e:
                    if v:
                        print(f"[red]Skip[/red] {name}: {e}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


file.add_command(crypt)
file.add_command(organize)
