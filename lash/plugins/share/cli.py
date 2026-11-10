import webbrowser
import click
from rich.console import Console
from lash.plugins.share.core import DEFAULT_PORT, ShareServer, render_qr, storage_dir
from lash.plugins.share.helpers import detect_lan_ip, format_event

_console = Console()


@click.command("share")
@click.option("-p", "--port", type=click.IntRange(1, 65535), default=DEFAULT_PORT,
              show_default=True, help="Port to listen on")
@click.option("--ip", default=None,
              help="IP used in the link and QR code (default: auto-detect LAN IP)")
@click.option("-p2p", "--p2p", "p2p", is_flag=True,
              help="P2P mode: no server folder, files go straight between browsers")
@click.option("-v", "--verbose", is_flag=True,
              help="Show activity logs (connections, uploads, downloads) in the terminal")
def share(port, ip, p2p, verbose):
    """\b
    Share files between devices on the local network.

    \b
    Opens a web page reachable by the QR code or the link shown here.
    Files sent from one device are downloaded automatically by the others.

    \b
    Ex:
      share
      share -p 9000
      share -p2p        # receive files from the phone straight to this PC
      share -v          # show activity logs
    """
    host_ip = ip or detect_lan_ip()
    on_event = (lambda event: _console.print(format_event(event))) if verbose else None
    try:
        server = ShareServer(None if p2p else storage_dir(), host_ip, port,
                             on_event=on_event, p2p=p2p)
    except OSError as e:
        raise click.ClickException(
            f"Could not start server on port {port}: {e.strerror or e}. "
            "Try another one with --port.") from e

    try:
        click.echo(render_qr(server.url))
    except ImportError:
        click.secho("QR code unavailable: install it with 'lash plugin add share'.",
                    fg="yellow")
    click.secho(server.url, fg="green", bold=True)
    if host_ip == "127.0.0.1":
        click.secho("No network found: only this computer can open the link.", fg="yellow")
    click.echo("Open the link on your devices. If they can't connect, allow Python in the firewall.")
    if p2p:
        webbrowser.open(server.url)
        click.echo("P2P mode: keep this computer's page open to send and receive.")
    click.echo("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        click.echo("Server stopped." if p2p else "Server stopped. Shared files removed.")
