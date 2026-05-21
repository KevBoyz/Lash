import click
import zipfile
import time
from lash.plugins.crack.core import brute, _next, path_no_file, total_combinations


def _fmt_eta(seconds):
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"


@click.group('crack', short_help='Brute-force password cracking')
def crack():
    """
    Set of commands to crack passwords
    """
    ...


@crack.command(short_help='Crack a ZIP archive password')
@click.argument('path', metavar='<path>', type=click.Path(exists=True))
@click.option('-ln', type=click.INT, default=10, show_default=True, help='Max password length to try')
@click.option('-r', 'r', flag_value=False, default=True, show_default=True,
              help='Disable ramp (by default tries lengths 1 through -ln)')
@click.option('-n', is_flag=True, default=False, show_default=True, help='Include numbers')
@click.option('-l', 'letters', flag_value=False, default=True, show_default=True, help='Disable letters')
@click.option('-s', is_flag=True, default=False, show_default=True, help='Include symbols')
@click.option('-sp', is_flag=True, default=False, show_default=True, help='Include spaces')
def azip(path, ln, r, n, letters, s, sp):
    """Crack the password of a ZIP archive using brute force.

    \b
    By default tries letter-only combinations, ramping from 1 to -ln characters.
    Ramp off (-r): tries only combinations of exactly -ln characters.

    \b
    Enable more character sets to expand the search space:
      -n  numbers    -s  symbols    -sp spaces

    \b
    Example:
      lash crack azip secrets.zip
      lash crack azip secrets.zip -ln 6 -n -s
    """
    total = total_combinations(ln, r, letters, n, s, sp)
    attempt_count = 0
    start_time = time.time()
    permutations = brute(ln, r, letters, n, s, sp)
    zip_arch = zipfile.ZipFile(path)
    while True:
        try:
            nx = _next(permutations)
            pm = bytes(nx, encoding='utf-8')
            try:
                zip_arch.extractall(path=path_no_file(path), pwd=pm)
                print(f'\nPassword is: {nx}')
                break
            except (RuntimeError, zipfile.BadZipFile):
                attempt_count += 1
                elapsed = time.time() - start_time
                if elapsed > 0 and attempt_count > 0:
                    remaining = max(total - attempt_count, 0)
                    eta = _fmt_eta(remaining * elapsed / attempt_count)
                else:
                    eta = "..."
                print(f'Attempts: {attempt_count} | Trying: {nx} | ETA: {eta}', end='\r')
        except StopIteration:
            print('\nPassword not found')
            break
