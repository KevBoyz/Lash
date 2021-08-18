import click
from random import randint


# Groups


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
