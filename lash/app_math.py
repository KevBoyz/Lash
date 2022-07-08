from lash.Exportables.exportable_math import *
import click
import cmath
import math
import numpy as np
from matplotlib import pyplot as plt


@click.group('calc', help='Math utilities')
def calc():
    ...


@calc.command(help='Probability calculator')
@click.argument('pc', type=click.FLOAT, metavar='<possible_cases>')
@click.argument('fc', type=click.FLOAT, metavar='<favorable_cases>')
@click.option('-d', is_flag=True, help='[Flag] Decimal output, more accurate result')
def prob(pc, fc, d):
    if fc > pc:
        try:
            raise Exception('[fc > pc], Operation not possible')
        except Exception as e:
            click.echo(e)
    if d:
        click.echo(f'{fc / pc}')
    else:
        r = (fc / pc) * 100
        if r <= 0.01:
            print('[0.0%] For better result, use -d (flag)')
        else:
            click.echo(f'{r:.1f}%')


@calc.command()
@click.argument('coefs', nargs=3, type=click.STRING)
@click.option('-d', is_flag=True, default=True, help='plot function graph', show_default=True)
@click.option('-r', is_flag=True, default=True, help='plot function roots', show_default=True)
@click.option('-v', is_flag=True, default=True, help='plot function vertices', show_default=True)
@click.option('-xm', type=click.INT, default=5, help='x axis interval', show_default=True)
@click.option('-t', type=click.INT, default=40, help='times calculated', show_default=True)
def trinomial(coefs, d, r, v, xm, t):
    """
       Calculate a quadratic function

       \b
       Example: calc trinomial n3 4 7
       use (n) to mark an coef value as negative
       """
    letters = get_signal(coefs)
    a = letters[0]
    b = letters[1]
    c = letters[2]

    delta = (b ** 2) - (4 * a * c)
    if delta < 0:
        x1 = (-b + cmath.sqrt(delta)) / (2 * a)
        x2 = (-b - cmath.sqrt(delta)) / (2 * a)
    else:
        x1 = (-b + math.sqrt(delta)) / (2 * a)
        x2 = (-b - math.sqrt(delta)) / (2 * a)
    xv = -b / (2 * a)
    yv = -delta / (4 * a)

    if d:
        cartesian_plan()
        x = np.linspace(xm * (-1), xm, t)
        y = a * x ** 2 + b * x + c
        plt.plot(x, y, 'r')
        if delta > 0:
            if r:
                plt.plot(x1, 0, 'ro')
                plt.plot(x2, 0, 'ro')
            if v:
                plt.plot(xv, yv, 'ro', color='b')
        plt.show()
    print(f'\nx1: {x1}\nx2: {x2}\nxv: {xv}\nyv: {yv}\ndelta: {delta}')


@calc.command(help='Calculate a affine function')
@click.argument('coefs', nargs=2, type=click.STRING)
@click.option('-xm', type=click.INT, default=5)
@click.option('-t', type=click.INT, default=40)
def binomial(coefs, xm, t):
    letters = get_signal(coefs)
    a = letters[0]
    b = letters[1]
    x = np.linspace(xm * (-1), xm, t)
    y = a*x + b
    cartesian_plan()
    plt.plot(x, y, 'r')
    plt.plot(0, b, 'ro')
    plt.show()
