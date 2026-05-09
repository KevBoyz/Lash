def get_last(path):
    if path.rfind('\\') != -1:
        last = path[1 + path.rfind('\\'):]
    else:
        last = path[1 + path.rfind('/'):]
    if last.rfind('"'):
        last = last.replace('"', '')
    return last


def path_no_file(path):
    filename = get_last(path)
    return path.replace(filename, '')
