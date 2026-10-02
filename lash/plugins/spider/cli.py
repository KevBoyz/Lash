import sys

import click

from lash.plugins.spider.core import port_verify, run_web_client, run_server


@click.group("spider", invoke_without_command=True,
             help="Remote web shell. Without a subcommand, start a LAN server.")
@click.pass_context
def spider(ctx):
    if ctx.invoked_subcommand is None:
        ctx.invoke(web)


@spider.command(
    "web",
    help="Remote web shell — host a server or connect as passive client",
)
@click.option(
    "-h",
    "--host",
    "h",
    type=str,
    default=None,
    help="Host on a specific port (default: choose a free port automatically).",
)
@click.option(
    "-c",
    "--connect",
    "c",
    type=str,
    nargs=2,
    default=None,
    help="Connect passively to host. Pass IP and port: -c 192.168.1.1 8080",
)
@click.option("--no-discovery", is_flag=True,
              help="Host without UDP discovery (manual connections only).")
def web(h, c, no_discovery):
    if h is not None and c:
        raise click.UsageError("Use either --host or --connect, not both.")
    try:
        if c:
            host_ip, port_str = c
            run_web_client(host_ip, port_verify(port_str))
        else:
            port = port_verify(h) if h is not None else 0
            if no_discovery:
                run_server("0.0.0.0", port, discoverable=False)
            else:
                run_server("0.0.0.0", port)
    except (ValueError, OSError) as e:
        raise click.ClickException(str(e)) from e


@spider.command("seeker")
@click.argument("addresses", required=False)
@click.argument("ports", required=False)
@click.option("-s", "--stop", "do_stop", is_flag=True,
              help="Stop the running seeker daemon")
@click.option("-p", "--ping", "ping_interval", default=10,
              type=click.IntRange(min=1), show_default=True,
              help="Discovery/scan interval in seconds")
@click.option("--_daemon", "is_daemon", is_flag=True, hidden=True)
def seeker(addresses, ports, do_stop, ping_interval, is_daemon):
    """Background daemon — auto-discovers and connects to Spider servers.

    \b
    With no arguments, discovers Spider hosts on the local IPv4 network.
    Optionally pass both addresses and ports to scan specific hosts.
    When a server is found, connects automatically as a passive client.
    Runs in the background; use --stop to terminate it.

    \b
    ADDRESSES  Comma-separated IPs (e.g. "192.168.1.1,192.168.1.2")
    PORTS      Comma-separated ports (e.g. "8080,9090")

    \b
    Example:
      lash spider seeker
      lash spider seeker 192.168.1.1,192.168.1.2 8080,9090
      lash spider seeker --stop
    """
    from lash.plugins.spider.core import (
        read_pid, is_pid_alive, spawn_daemon,
        stop_seeker as _stop_seeker, run_seeker_daemon,
    )

    if do_stop:
        click.echo(_stop_seeker())
        return

    if (addresses is None) != (ports is None):
        raise click.UsageError(
            "Pass both ADDRESSES and PORTS, or neither for LAN discovery.")
    addr_list = port_list = None
    if addresses is not None:
        addr_list = [a.strip() for a in addresses.split(",")]
        if not all(addr_list):
            raise click.BadParameter("Addresses cannot be empty.",
                                     param_hint="ADDRESSES")
        try:
            port_list = [port_verify(p.strip()) for p in ports.split(",")]
        except ValueError as e:
            raise click.BadParameter(str(e), param_hint="PORTS") from e

    if is_daemon:
        run_seeker_daemon(addr_list, port_list, ping_interval)
        return

    pid = read_pid()
    if pid and is_pid_alive(pid):
        click.echo(f"Seeker already running (PID: {pid})")
        sys.exit(1)

    spawn_daemon(addresses, ports, ping_interval)
    mode = "LAN discovery" if addresses is None else "manual scan"
    click.echo(f"Seeker started ({mode})")
