import click
from random import randint

from pynput.mouse import Controller, Button
from pynput.keyboard import Key
from keyboard import is_pressed
from time import sleep


@click.command(help='Randomize numbers')
@click.option('-s', type=click.INT, default=0, help='Randomization start number')
@click.option('-e', type=click.INT, default=9, help='Randomization end number')
@click.option('-c', type=click.INT, default=5, help='Number of characters in random output')
def random(s=0, e=9, c=5):
    if s != 0:
        e = s + 9
    randstr = ''
    for r in range(0, c):
        randstr += str((randint(s, e)))
    if len(randstr) > c:
        click.echo(randstr[0:c + 1])
    else:
        click.echo(randstr)


@click.command(help='Auto clicker')
@click.option('-cd', type=click.FLOAT, default=0.0, help='Click delay')
@click.option('-ct', type=click.FLOAT, default=0.0, help='Click time (hold)')
def autoclick(cd, ct):
    mouse = Controller()
    print('Auto Clicker initialized, f4 to start f3 to stop')
    while True:
        if is_pressed('f4'):
            print(f'*clicking* -> {cd} cps')
            while True:
                if is_pressed('f3'):
                    print('- Process suspended -')
                    break
                else:
                    sleep(cd)
                    mouse.press(Button.left)
                    sleep(ct)
                    mouse.release(Button.left)
        else:
            continue
