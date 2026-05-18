import os
import click
import socket
from threading import Thread
from rich import print
from lash.plugins.server.core import (
    port_verify, injection_client_msg,
    handle_connection, custom_client_manager,
)


@click.group('server', help='Server tools')
def server():
    ...


@server.command(help='Remote commands injection host/client')
@click.option('-h', '-host', type=click.STRING, help='Host this machine for remote access, pass the port Ex: -h 8080')
@click.option('-c', '-connect', type=click.STRING, nargs=2, help='Connect to a host by it\' IP, port. Ex: -c 192.168.1.1 8080')
@click.option('-v', is_flag=True, default=False, help='on/off verbose mode for server')
def injection(h, c, v):
    buffer = 1024 ** 2
    if h:
        host = socket.gethostbyname(socket.gethostname())
        port = port_verify(h)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            print(f'Server online [ host: {host}, port: {port} ] Waiting a connection...') if v else None
            while True:
                s.listen()
                conn, addr = s.accept()
                print(f'{addr} connected') if v else None
                Thread(target=handle_connection, args=(conn, buffer,)).start()
    elif c:
        host, port = c
        port = port_verify(port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            print()
            print(injection_client_msg())
            print()
            while True:
                try:
                    path = s.recv(buffer).decode('utf-8')
                except:
                    path = 'undefined'
                    pass
                command = str(input(f'{host}\\{path}> ')).strip()
                if command == '':
                    command = 'snake'
                try:
                    command_arg1 = command.strip().split()[0]
                except IndexError:
                    command_arg1 = command
                if not custom_client_manager(s, buffer, os.getcwd(), command, command_arg1):
                    s.sendall(bytes(command, 'utf-8'))
                    print(s.recv(buffer).decode('utf-8'))
    else:
        print('[red]Error: No option passed[/red]')
