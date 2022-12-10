import click
from cmath import sqrt
import math
from numpy import linspace
from matplotlib import pyplot as plt
from rich import print
from itertools import product
from functools import reduce
from operator import mul


def cartesian_plan():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.spines['left'].set_position('center')
    ax.spines['bottom'].set_position('zero')
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')


def get_signal(coefs):
    letters = []
    for c in range(0, len(coefs)):
        if coefs[c][0] == 'n':
            letters.append(int(coefs[c][1:]) * (-1))
        else:
            letters.append(int(coefs[c]))
    return letters


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


@calc.command(help='Cartesian product of multiple sets')
@click.option('-b', help='Build points')
@click.option('-t',help='Get total of sets')
def cartesian(b, t):
    if b:
        b = eval(b)
        try:
            print(list(product(*b)))
        except TypeError as e:
            print(f'{e}. Correct use: -b \'[(1,2), (2,3)]\'')
    if t:
        t = eval(t)
        print(reduce(mul, t))


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
        x1 = (-b + sqrt(delta)) / (2 * a)
        x2 = (-b - sqrt(delta)) / (2 * a)
    else:
        x1 = (-b + math.sqrt(delta)) / (2 * a)
        x2 = (-b - math.sqrt(delta)) / (2 * a)
    xv = -b / (2 * a)
    yv = -delta / (4 * a)

    if d:
        cartesian_plan()
        x = linspace(xm * (-1), xm, t)
        y = a * x ** 2 + b * x + c
        plt.plot(x, y, 'r')
        if delta > 0:
            if r:
                plt.plot(x1, 0, 'ro', label=f'{x1:.2f}')
                plt.plot(x2, 0, 'go', label=f'{x2:.2f}')
            if v:
                plt.plot(xv, yv, 'ro', color='b', label=f'x{xv:.2f} y{yv:.2f}')
        plt.legend()
        plt.show()
    print(f'\n[red]x1[/red]: {x1:.3f}\n[green]x2[/green]: {x2:.3f}\n[blue]xv[/blue]: {xv:.3f}'
          f'\n[blue]yv[/blue]: {yv:.3f}\n[yellow]dΔ[/yellow]: {delta}\n')


@calc.command()
@click.argument('coefs', nargs=2, type=click.STRING)
@click.option('-xm', type=click.INT, default=5, help='lim for x', show_default=True)
@click.option('-t', type=click.INT, default=40, help='Times resolved to graph')
def binomial(coefs, xm, t):
    """
       Calculate a affine function

       \b
       Example: calc trinomial n5 3
       use (n) to mark an coef value as negative
       """
    letters = get_signal(coefs)
    a = letters[0]
    b = letters[1]
    x = linspace(xm * (-1), xm, t)
    y = a*x + b
    cartesian_plan()
    plt.plot(x, y, 'r')
    plt.plot(0, b, 'ro', label=f'{b:.2f}')
    plt.legend()
    plt.show()
