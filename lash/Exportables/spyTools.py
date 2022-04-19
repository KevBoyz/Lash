import os


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
[-start x]             Start something on host
[-kill]                Kill server all, connections lost
[-cls]                 Clear the client terminal like cls
[-copy path_host]      Copy a file from host to your machine
[-move path_local]     Move a file from your machine to host
Move/Copy, gonna affect the local directory (host or client) 

Caution! if you send a incorrect command, the connection will be lost
        '''


def custom_server_manager(conn, buffer, path, command, command_arg1):
    os.chdir(path)
    if command_arg1 == '-chdir':
        path = command.split()[1]
        os.chdir(path)
        return True
    elif command_arg1 == '-copy':
        print(command)
        print(command_arg1)
        file_name = ''.join(command[len(command_arg1):]).strip()
        print(file_name)
        with open(file_name, 'r') as file:
            content = file.read()
        conn.send(bytes(file_name, 'utf-8'))
        conn.send(bytes(content, 'utf-8'))
        return True
    elif command_arg1 == '-move':
        file_name = conn.recv(buffer).decode('utf-8')
        file_data = conn.recv(buffer).decode('utf-8')
        with open(file_name, 'w') as file:
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
        file_name = s.recv(buffer).decode('utf-8')
        file_data = s.recv(buffer).decode('utf-8')
        with open(file_name, 'w') as file:
            file.write(file_data)
        print(f'{file_name} has been copied to {os.getcwd()}')
        return True
    elif command_arg1 == '-move':
        file_name = ' '.join(command.strip().split()[len(command_arg1):])
        s.send(bytes(command_arg1, 'utf-8'))
        with open(file_name, 'r') as file:
            content = file.read()
        s.send(bytes(file_name, 'utf-8'))
        s.send(bytes(content, 'utf-8'))
        msg = s.recv(buffer).decode('utf-8')
        print(msg)
        return True
    elif command_arg1 == '-kill':
        s.sendall(bytes(command, 'utf-8'))
        quit(0)
    else:
        return False