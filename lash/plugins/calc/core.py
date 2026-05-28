from cmath import sqrt as csqrt
import math


# ── shared ────────────────────────────────────────────────────────────────────


def get_signal(coefs):
    letters = []
    for c in range(len(coefs)):
        if coefs[c][0] == 'n':
            letters.append(int(coefs[c][1:]) * (-1))
        else:
            letters.append(int(coefs[c]))
    return letters


# ── prob ──────────────────────────────────────────────────────────────────────


def probability(fc: float, pc: float) -> float:
    return fc / pc


# ── trinomial ─────────────────────────────────────────────────────────────────


def solve_quadratic(a: float, b: float, c: float) -> dict:
    delta = (b ** 2) - (4 * a * c)
    if delta < 0:
        x1 = (-b + csqrt(delta)) / (2 * a)
        x2 = (-b - csqrt(delta)) / (2 * a)
    else:
        x1 = (-b + math.sqrt(delta)) / (2 * a)
        x2 = (-b - math.sqrt(delta)) / (2 * a)
    xv = -b / (2 * a)
    yv = -delta / (4 * a)
    return {'x1': x1, 'x2': x2, 'xv': xv, 'yv': yv, 'delta': delta}


# ── binomial ──────────────────────────────────────────────────────────────────


def solve_affine(a: float, b: float) -> dict:
    return {'a': a, 'b': b}
