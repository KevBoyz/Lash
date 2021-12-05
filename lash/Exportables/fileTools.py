import os


def bar_template():  # Template for load bar
    return '%(label)s  %(bar)s  %(info)s'


def get_ext(file='', path=''):
    if path:
        index = path.rfind('\\')
        return path[index+1:]
    else:
        index = file.rfind('.')  # Getting the type of file
        return file[index:].lower()


def get_file(path):
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






