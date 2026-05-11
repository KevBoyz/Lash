# pytest lash/plugins/calc/tests/test_core.py
import pytest
from lash.plugins.calc.core import get_signal, probability, solve_quadratic, solve_affine


class TestGetSignal:
    def test_positive_coefs(self):
        assert get_signal(['3', '4', '7']) == [3, 4, 7]

    def test_n_prefix_negates(self):
        assert get_signal(['n3', '4', 'n7']) == [-3, 4, -7]

    def test_all_negative(self):
        assert get_signal(['n1', 'n2', 'n3']) == [-1, -2, -3]

    def test_two_coefs(self):
        assert get_signal(['n5', '3']) == [-5, 3]

    def test_large_values(self):
        assert get_signal(['100', 'n200']) == [100, -200]


class TestProbability:
    def test_half(self):
        assert probability(2, 1) == pytest.approx(0.5)

    def test_certainty(self):
        assert probability(10, 10) == pytest.approx(1.0)

    def test_small_probability(self):
        assert probability(100, 1) == pytest.approx(0.01)

    def test_returns_float(self):
        assert isinstance(probability(4, 1), float)


class TestSolveQuadratic:
    def test_positive_delta_two_real_roots(self):
        # x^2 - 5x + 6 = 0 → x1=3, x2=2
        result = solve_quadratic(1, -5, 6)
        assert result['delta'] == pytest.approx(1.0)
        assert result['x1'] == pytest.approx(3.0)
        assert result['x2'] == pytest.approx(2.0)

    def test_zero_delta_one_root(self):
        # x^2 - 2x + 1 = 0 → x=1
        result = solve_quadratic(1, -2, 1)
        assert result['delta'] == pytest.approx(0.0)
        assert result['x1'] == pytest.approx(1.0)
        assert result['x2'] == pytest.approx(1.0)

    def test_negative_delta_complex_roots(self):
        # x^2 + 1 = 0 → complex roots
        result = solve_quadratic(1, 0, 1)
        assert result['delta'] == -4
        assert result['x1'].imag != 0
        assert result['x2'].imag != 0

    def test_vertex_values(self):
        # x^2 - 4x + 3 = 0 → vertex at x=2, y=-1
        result = solve_quadratic(1, -4, 3)
        assert result['xv'] == pytest.approx(2.0)
        assert result['yv'] == pytest.approx(-1.0)

    def test_returns_all_keys(self):
        result = solve_quadratic(1, 0, -1)
        assert {'x1', 'x2', 'xv', 'yv', 'delta'} == set(result.keys())


class TestSolveAffine:
    def test_returns_a_and_b(self):
        result = solve_affine(2, 3)
        assert result == {'a': 2, 'b': 3}

    def test_negative_values(self):
        result = solve_affine(-5, 0)
        assert result['a'] == -5
        assert result['b'] == 0
