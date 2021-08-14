import os


def bar_template():
    return '%(label)s  %(bar)s  %(info)s'


def get_ext(file='', path=''):
    if path:
        index = path.rfind('\\')
        return path[index+1:]
    else:
        index = file.rfind('.')  # Getting the type of file
        return file[index:].lower()


def file_types():
    return {'midia': {'images': ('.png', '.jpeg', '.gif', '.bmp', '.tiff', '.svg'),
                      'musics': ('.mp3', '.waw', '.ogg', '.wma'),
                      'videos': ('.mp4', '.avi', '.wmv', '.mov', '.avchd')},
            'docs': ('.pdf', '.ppt', '.docx', '.txt', '.xls', '.doc')}


def count_files(path, n=0):
    for r, d, f in os.walk(path):
        n += len(d) + len(f)
    print(n)


