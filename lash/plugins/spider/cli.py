import socket
import sys

import click

from lash.plugins.spider.core import port_verify, run_web_client, run_server


@click.group("spider", help="Remote web shell and auto-discovery tools")
def spider():
    pass


@spider.command("web", help="Remote web shell — host a server or connect as passive client")
@click.option("-h", "--host", "h", type=str, default=None,
              help="Host this machine. Pass port: -h 8080")
@click.option("-c", "--connect", "c", type=str, nargs=2, default=None,
              help="Connect passively to host. Pass IP and port: -c 192.168.1.1 8080")
def web(h, c):
    if h:
        host = socket.gethostbyname(socket.gethostname())
        try:
            port = port_verify(h)
        except ValueError as e:
            click.echo(str(e), err=True)
            sys.exit(1)
        run_server(host, port)
    elif c:
        host_ip, port_str = c
        try:
            port = port_verify(port_str)
        except ValueError as e:
            click.echo(str(e), err=True)
            sys.exit(1)
        run_web_client(host_ip, port)
    else:
        click.echo("Error: pass -h <port> to host or -c <ip> <port> to connect", err=True)
        sys.exit(1)


@spider.command("seeker")
@click.argument("addresses", required=False)
@click.argument("ports", required=False)
@click.option("-s", "--stop", "do_stop", is_flag=True, help="Stop the running seeker daemon")
@click.option("-p", "--ping", "ping_interval", default=10, type=int,
              help="Scan interval in seconds")
@click.option("--_daemon", "is_daemon", is_flag=True, hidden=True)
def seeker(addresses, ports, do_stop, ping_interval, is_daemon):
    """Background daemon — auto-discovers and connects to Spider servers.

    \b
    Scans the given addresses and ports for active Spider hosts.
    When a server is found, connects automatically as a passive client.
    Runs in the background; use --stop to terminate it.

    \b
    ADDRESSES  Comma-separated IPs (e.g. "192.168.1.1,192.168.1.2")
    PORTS      Comma-separated ports (e.g. "8080,9090")

    \b
    Example:
      lash spider seeker 192.168.1.1,192.168.1.2 8080,9090
      lash spider seeker --stop
    """
    from lash.plugins.spider.core import (
        read_pid, write_pid, is_pid_alive, spawn_daemon,
        stop_seeker as _stop_seeker, seeker_scan_loop,
    )
    import os

    if do_stop:
        click.echo(_stop_seeker())
        return

    if is_daemon:
        if not addresses or not ports:
            return
        write_pid(os.getpid())
        addr_list = [a.strip() for a in addresses.split(",")]
        port_list = [int(p.strip()) for p in ports.split(",")]
        seeker_scan_loop(addr_list, port_list, ping_interval)
        return

    if not addresses or not ports:
        click.echo("Error: ADDRESSES and PORTS required", err=True)
        sys.exit(1)

    pid = read_pid()
    if pid and is_pid_alive(pid):
        click.echo(f"Seeker already running (PID: {pid})")
        sys.exit(1)

    spawn_daemon(addresses, ports, ping_interval)
    click.echo("Seeker started")
