import numpy as np
import pandas as pd

from plataforma_acciones import metrics


def test_cagr_constant_growth():
    # 1% diario durante un año (252 periodos) -> CAGR ~ (1.01)^252 - 1
    r = pd.Series([0.01] * 252)
    expected = 1.01 ** 252 - 1
    assert abs(metrics.cagr(r) - expected) < 1e-6


def test_total_return():
    r = pd.Series([0.1, -0.5, 0.2])
    expected = (1.1 * 0.5 * 1.2) - 1
    assert abs(metrics.total_return(r) - expected) < 1e-9


def test_max_drawdown_is_negative_or_zero():
    r = pd.Series([0.1, -0.2, 0.05, -0.3, 0.1])
    mdd = metrics.max_drawdown(r)
    assert mdd <= 0.0


def test_max_drawdown_monotonic_up_is_zero():
    r = pd.Series([0.01] * 50)
    assert metrics.max_drawdown(r) == 0.0


def test_sharpe_zero_for_constant():
    r = pd.Series([0.005] * 100)
    # volatilidad cero -> Sharpe definido como 0
    assert metrics.sharpe_ratio(r) == 0.0


def test_sharpe_positive_for_upward_noisy():
    rng = np.random.default_rng(0)
    r = pd.Series(rng.normal(0.001, 0.01, 1000))
    assert metrics.sharpe_ratio(r) > 0


def test_summary_keys():
    r = pd.Series(np.random.default_rng(1).normal(0, 0.01, 300))
    s = metrics.summary(r)
    for k in ("cagr", "sharpe", "sortino", "max_drawdown", "calmar", "win_rate", "volatility"):
        assert k in s


def test_equity_curve_starts_above_initial_on_gain():
    r = pd.Series([0.1, 0.1])
    eq = metrics.equity_curve(r, initial=100.0)
    assert eq.iloc[-1] > 100.0
