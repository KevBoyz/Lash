import os


def bar_template():  # Template for load bar (click)
    return '%(label)s  %(bar)s  %(info)s'


def files_range():
    total = 0
    for root, files, folders in os.walk('.'):
        for file in files:
            total += 1
    return total


def get_ext(file='', path=''):
    if path:
        index = path.rfind('\\')
        return path[index+1:]
    else:
        index = file.rfind('.')
        return file[index:].lower()


def get_last(path):
    if path.rfind('\\') != -1:
        last = path[1+path.rfind('\\'):]
    else:
        last = path[1+path.rfind('/'):]
    if last.rfind('"'):
        last = last.replace('"', '')
    return last


def path_no_file(path):
    filename = get_last(path)
    return path.replace(filename, '')



def get_file(path):
    if '\\' not in path:
        return path
    if os.name == 'nt':
        os.chdir(path[:path.rfind('\\')])
        fn = path[path.rfind('\\') + 1:]
    else:
        os.chdir(path[:path.rfind('/')])
        fn = path[path.rfind('/') + 1:]
    return fn


def file_types():
    return {'midia': {'images': ('.png', '.jpeg', '.gif', '.bmp', '.tiff', '.svg'),
                      'musics': ('.mp3', '.waw', '.ogg', '.wma'),
                      'videos': ('.mp4', '.avi', '.wmv', '.mov', '.avchd')},
            'docs': ('.pdf', '.ppt', '.docx', '.txt', '.xls', '.doc')}

