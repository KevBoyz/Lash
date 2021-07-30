import click, zipfile, os, shutil as sh
from .Exportables.fileTools import *


@click.command()
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-t', type=click.STRING, help='[Flag] Organize files per type')
@click.option('-m', is_flag=True, default=False, show_default=True, help='Midia organize             ')
@click.option('-d', is_flag=True, default=True, show_default=True, help='Docs organize              ')
@click.option('-o', is_flag=True, default=True, show_default=True, help='Create ~Others~ folder     ')
@click.option('-s', is_flag=True, default=False, show_default=True, help='Organize sub-folders       ')
def organize(path, t, m, d, o, s):
    """Organize your files
    \b
    Organize a folder in a simple way, by predefined execution that separates files
    according to their context or in a personalized way searching for a specific type.
    """
    os.chdir(path)
    files = os.listdir()
    ft = file_types()
    if t:
        if t.find('.'):
            t = '.' + t
        os.mkdir(f'({t}) Files') if f'({t}) Files' not in files else None
        for root, folders, file in os.walk('.'):
            for c in range(len(file)):
                if get_ext(file[c]) == t:
                    sh.move(os.path.join(root, file[c]), f'({t}) Files')
    else:
        if m:
            os.mkdir('Midia') if 'Midia' not in files else files.remove('Midia')
            os.chdir('Midia')
            if os.listdir('..') == 0:
                os.mkdir('Images')
                os.mkdir('Videos')
                os.mkdir('Musics')
            else:
                os.mkdir('Images') if 'Images' not in os.listdir('..') else None
                os.mkdir('Videos') if 'Videos' not in os.listdir('..') else None
                os.mkdir('Musics') if 'Musics' not in os.listdir('..') else None
            os.chdir(path)
        if d:
            os.mkdir('Docs') if 'Docs' not in files else files.remove('Docs')
        if o:
            os.mkdir('Others') if 'Others' not in files else files.remove('Others')
        if s:
            os.mkdir('Sub-Folders') if 'Sub-Folders' not in files else files.remove('Sub-Folders')

        with click.progressbar(range(len(files)), empty_char='─', fill_char='█', bar_template=bar_template()) as p:
            for c in p:
                if not os.path.isdir(files[c]):
                    if get_ext(files[c]) in ft['midia']['images']:
                        sh.move(os.path.join(path, files[c]), os.path.join('Midia', 'Images', files[c]))
                    elif get_ext(files[c]) in ft['midia']['videos']:
                        sh.move(os.path.join(path, files[c]), os.path.join('Midia', 'Videos', files[c]))
                    elif get_ext(files[c]) in ft['midia']['musics']:
                        sh.move(os.path.join(path, files[c]), os.path.join('Midia', 'Musics', files[c]))
                    elif get_ext(files[c]) in ft['docs']:
                        sh.move(os.path.join(path, files[c]), os.path.join('Docs', files[c]))
                    else:
                        sh.move(os.path.join(path, files[c]), os.path.join('Others', files[c]))
                else:
                    if s:
                        sh.move(os.path.join(path, files[c]), os.path.join('Sub-folders', files[c]))
                    else:
                        continue


# Groups


@click.group('zip', help='Zip tools')
def Zip():
    ...


@Zip.command(help='Compress files in zip archive')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-fn', type=click.STRING, default='ZipFile', help='Output file name')
@click.option('-v', is_flag=True, default=True, show_default=True, help='Verbose mode ')
def compress(path, fn, v):
    os.chdir(path)
    arch = 0
    if fn.rfind('.zip'):
        fn += '.zip'
    zip = zipfile.ZipFile(fn, 'w')
    print(f'Compacting archives, please wait...')
    print() if v else None
    print('  - - Process list - -') if v else None
    for folder, sub_folders, files in os.walk('..'):
        for file in files:
            if file != fn and file and file not in zip.namelist():
                print(f'Compacting: {file}') if v else None
                zip.write(os.path.join(folder, file),
                          os.path.relpath(os.path.join(folder, file), '..'),
                          compress_type=zipfile.ZIP_DEFLATED)
                arch += 1
    print() if v else None
    print(f'process completed, {arch} files compacted')
    zip.close()


@Zip.command(help='Extract zipfile')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.argument('fn', metavar='<file_name>', type=click.STRING)
@click.option('-v', '-verbose', is_flag=True, default=False, show_default=True, help='Verbose mode ')
def extract(path, fn, v, ex=0):
    os.chdir(path)
    if fn.rfind('.zip'):
        fn += '.zip'
    assert zipfile.is_zipfile(fn), f'Assertion error, can\'t find <file> on <path>'
    zip = zipfile.ZipFile(fn, 'r')
    list = zip.namelist()
    click.secho(f'{len(list)} Files founded in {fn}') if v else None  # Verbose
    click.secho(f'{list}\n') if v else None  # Verbose
    assert len(list) >= 0, f'Assertion error, <file> is empty or can\'t be readied>'
    with click.progressbar(range(len(zip.namelist())), empty_char='─', fill_char='█', bar_template=bar_template()) as p:
        for f in p:
            click.secho(f' - Extracting {list[f]}') if v else None  # Verbose
            try:
                zip.extract(list[f])
                ex += 1
            except Exception as e:
                print(e) if v else None
    zip.close()
    click.secho(f'{ex} files extracted')
