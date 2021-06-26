def bar_template():
    return '%(label)s  %(bar)s  %(info)s'


def get_ext(file):
    index = file.rfind('.')  # Getting the type of file
    return file[index:].lower()


def file_types():
    return {'midia': {'images': ('.png', '.jpeg', '.gif', '.bmp', '.tiff', '.svg'),
                      'musics': ('.mp3', '.waw', '.ogg', '.wma'),
                      'videos': ('.mp4', '.avi', '.wmv', '.mov', '.avchd')},
            'docs': ('.pdf', '.ppt', '.docx', '.txt', '.xls', '.doc')}
