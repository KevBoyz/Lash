import click
from random import randint


# Groups


@click.group('calc', help='Math utilities')
def calc():
    ...


@calc.command(help='Calculate simple probability')
@click.argument('pc', type=click.INT)
@click.argument('fc', type=click.INT)
@click.option('-d', '-decimal', is_flag=True, default=False, help='[FLAG] Decimal output')
def prob(pc, fc, d):
    if fc > pc:
        try:
            raise Exception('[fc > pc], Operation not possible')
        except Exception as e:
            click.echo(e)
            return
    if d:
        click.echo(f'{fc / pc}')
    else:
        click.echo(f'{int((fc / pc) * 100)}%')
