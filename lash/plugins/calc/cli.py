import ast
import click
import matplotlib
matplotlib.use('Qt5Agg')
from numpy import linspace
from matplotlib import pyplot as plt
from rich import print
from itertools import product
from functools import reduce
from operator import mul
from lash.plugins.calc.core import get_signal, probability, solve_quadratic, solve_affine
from lash.plugins.calc.helpers import cartesian_plan


@click.group('calc', help='Math utilities')
def calc():
    ...


@calc.command(help='Probability calculator')
@click.argument('pc', type=click.FLOAT, metavar='<possible_cases>')
@click.argument('fc', type=click.FLOAT, metavar='<favorable_cases>')
@click.option('-d', is_flag=True, help='[Flag] Decimal output, more accurate result')
def prob(pc, fc, d):
    if fc > pc:
        click.echo('[fc > pc], Operation not possible')
        return
    r = probability(fc, pc)
    if d:
        click.echo(f'{r}')
    else:
        pct = r * 100
        if pct <= 0.01:
            print('[0.0%] For better result, use -d (flag)')
        else:
            click.echo(f'{pct:.1f}%')


@calc.command(help='Cartesian product of multiple sets')
@click.option('-b', help='Build points, e.g. \'[(1,2),(3,4)]\'')
@click.option('-t', help='Get total of sets, e.g. \'[2, 3, 4]\'')
def cartesian(b, t):
    if b:
        try:
            b = ast.literal_eval(b)
            print(list(product(*b)))
        except (ValueError, TypeError) as e:
            print(f'{e}. Correct use: -b \'[(1,2), (2,3)]\'')
    if t:
        try:
            t = ast.literal_eval(t)
            print(reduce(mul, t))
        except (ValueError, TypeError) as e:
            print(f'{e}. Correct use: -t \'[2, 3, 4]\'')


@calc.command()
@click.argument('coefs', nargs=3, type=click.STRING)
@click.option('-d', is_flag=True, default=False, help='Plot function graph')
@click.option('-r', is_flag=True, default=False, help='Plot function roots on graph')
@click.option('-v', is_flag=True, default=False, help='Plot function vertex on graph')
@click.option('-xm', type=click.INT, default=5, help='x axis interval', show_default=True)
@click.option('-t', type=click.INT, default=40, help='Times calculated', show_default=True)
def trinomial(coefs, d, r, v, xm, t):
    """
       Calculate a quadratic function

       \b
       Example: calc trinomial n3 4 7
       use (n) to mark a coef value as negative
       """
    a, b, c = get_signal(coefs)
    result = solve_quadratic(a, b, c)
    x1, x2, xv, yv, delta = result['x1'], result['x2'], result['xv'], result['yv'], result['delta']

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
       Calculate an affine function

       \b
       Example: calc binomial n5 3
       use (n) to mark a coef value as negative
       """
    a, b = get_signal(coefs)
    result = solve_affine(a, b)
    x = linspace(xm * (-1), xm, t)
    y = result['a'] * x + result['b']
    cartesian_plan()
    plt.plot(x, y, 'r')
    plt.plot(0, result['b'], 'ro', label=f'{result["b"]:.2f}')
    plt.legend()
    plt.show()
