import click, zipfile, os, shutil as sh
from lash.Exportables.fileTools import *
from random import shuffle
from rich import print


@click.command()
@click.argument('path', metavar='<path>', type=click.Path(exists=True), required=False, default='.')
@click.option('-t', type=click.STRING, help='Organize files per type')
@click.option('-m', is_flag=True, default=False, show_default=True, help='Midia organize')
@click.option('-d', is_flag=True, default=True, show_default=True, help='Docs organize')
@click.option('-o', is_flag=True, default=True, show_default=True, help='Create ~Others~ folder')
@click.option('-s', is_flag=True, default=False, show_default=True, help='Organize sub-folders')
@click.option('-v', is_flag=True, default=True, show_default=True, help='Verbose mode')
def organize(path, t, m, d, o, s, v):
    """
    Organize your files

    \b
    Organize a folder in a simple way, by predefined execution that separates files
    according to their context or in a personalized way searching for a specific type.
    [!Important] - Do not use ('') to declare TYPE on -t option set the value like: -t pdf
    """
    try:
        os.chdir(path)
        files = os.listdir()
        if t:
            if t.find('.'):
                t = '.' + t  # t -> .t
            cfiles = list()
            os.mkdir(f'({t}) Files') if f'({t}) Files' not in files else None
            for root, folders, file in os.walk('.'):
                for c in range(len(file)):
                    if get_ext(file[c]) == t and file[c] not in cfiles:
                        print(f'Moving: {file[c]}') if v else None
                        sh.move(os.path.join(root, file[c]), f'({t}) Files')
                        cfiles.append(file[c])
        else:
            ft = file_types()
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
                    print(c, p)
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
    except:
        pass


# Groups


@click.group('zip', help='Zip tools')
def zip_group():
    ...


@zip_group.command(help='See the files on a zip')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
def view(path):
    fn = get_file(path)
    if not fn.endswith('.zip'):
        fn += '.zip'
    _zip = zipfile.ZipFile(fn, 'r')
    ziplist = _zip.namelist()
    if len(ziplist) <= 0:
        print('Error, no the zip are empty or can\'t be readied')
    else:
        print()
        for file in ziplist:
            print(file)


@zip_group.command(help='Compress a folder in zip archive')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-fn', type=click.STRING, help='Output file name')
@click.option('-v', is_flag=True, default=True, show_default=True, help='Verbose mode ')
@click.option('-fo', is_flag=True, default=False, show_default=True, help='Files only mode')
def compress(path, fn, v, fo):
    if not fn:
        fn = get_last(path=path) + '.zip'
    else:
        if not fn.endswith('.zip'):
            fn += '.zip'
    os.chdir(path)
    arch = 0
    _zip = zipfile.ZipFile(fn, 'w')
    print() if v else None
    if fo:
        way = os.getcwd()
        for folder, sub_folders, files in os.walk('.'):
            for file in files:
                if file != fn:
                    try:
                        os.chdir(folder)
                        print(f'[yellow]Compacting:[/yellow] [dark_orange]{file}[/dark_orange]', end='\r') if v else None
                        _zip.write(file, compress_type=zipfile.ZIP_DEFLATED)
                        arch += 1
                        os.chdir(way)
                    except:
                        pass
    else:
        for folder, sub_folders, files in os.walk('.'):
            for file in files:
                if file != fn:
                    print(f'[yellow]Compacting:[/yellow] [dark_orange]{file}[/dark_orange]', end='\r') if v else None
                    _zip.write(os.path.join(folder, file),
                              os.path.relpath(os.path.join(folder, file), '.'),
                              compress_type=zipfile.ZIP_DEFLATED)
                    arch += 1
    print() if v else None
    print(f'[bright_green]Process completed[/bright_green], {arch} files compacted')
    _zip.close()
    print('[cyan]Moving zipfile to parent folder...[/cyan]')
    if fn == '..zip':  # If the path = '.'
        try:
            dir_name = os.getcwd()[os.getcwd().rfind('\\') + 1:] + '.zip'
            os.rename(fn, dir_name)
        except FileExistsError:
            rlist = [7, 5, 6, 2]
            shuffle(rlist)
            rand = ''.join(str(e) for e in rlist)
            dir_name = os.getcwd()[os.getcwd().rfind('\\') + 1:] + f'_{rand}' + '.zip'
            os.rename(fn, dir_name)
        fn = dir_name
    else:
        os.chdir('..')
        try:
            sh.move(fn, '.')
        except:
            os.chdir(path)
    print(f'[bright_green]Saved in[/bright_green] [bright_blue]{os.path.join(os.getcwd(), fn)}[/bright_blue]\n')


@zip_group.command(help='Extract zipfile')
@click.argument('path', metavar='<file_path>', type=click.Path(exists=True))
@click.option('-to', type=click.Path(exists=True), help='Extract to')
@click.option('-v', is_flag=True, default=False, show_default=True, help='Verbose mode ')
def extract(path, to, v, ex=0):
    fn = get_file(path)
    if not fn.endswith('.zip'):
        fn += '.zip'
    _zip = zipfile.ZipFile(fn, 'r')
    ziplist = _zip.namelist()
    click.secho(f'{len(ziplist)} Files founded in {fn}') if v else None  # Verbose
    if len(ziplist) <= 0:
        print(f'Error, {fn} is empty or can\'t be readied>')
        return
    if to:
        try:
            os.chdir(to)
        except Exception as e:
            print(e)
    with click.progressbar(range(len(_zip.namelist())), empty_char='─', fill_char='█', bar_template=bar_template()) as p:
        for f in p:
            print(f'[yellow]Extracting[/yellow] [green]{ziplist[f]}[/green]', end='\r') if v else None  # Verbose
            try:
                _zip.extract(ziplist[f])
                ex += 1
            except Exception as e:
                print(e) if v else None
    _zip.close()
    print(f'[green]Process completed: {ex} files extracted[/green]')
