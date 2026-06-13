"""Métricas de rendimiento y riesgo para series de retornos.

Todas las funciones asumen retornos *simples* por periodo (no logarítmicos),
indexados temporalmente. El número de periodos por año se pasa explícitamente
(``periods_per_year``) para soportar datos diarios (252), semanales (52), etc.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def _as_series(returns) -> pd.Series:
    if isinstance(returns, pd.Series):
        return returns.astype(float).fillna(0.0)
    return pd.Series(np.asarray(returns, dtype=float)).fillna(0.0)


def equity_curve(returns, initial: float = 1.0) -> pd.Series:
    """Curva de capital acumulada a partir de retornos por periodo."""
    r = _as_series(returns)
    return initial * (1.0 + r).cumprod()


def total_return(returns) -> float:
    r = _as_series(returns)
    return float((1.0 + r).prod() - 1.0)


def cagr(returns, periods_per_year: int = TRADING_DAYS) -> float:
    """Tasa de crecimiento anual compuesta (CAGR)."""
    r = _as_series(returns)
    n = len(r)
    if n == 0:
        return 0.0
    growth = (1.0 + r).prod()
    if growth <= 0:
        return -1.0
    years = n / periods_per_year
    if years <= 0:
        return 0.0
    return float(growth ** (1.0 / years) - 1.0)


def annual_volatility(returns, periods_per_year: int = TRADING_DAYS) -> float:
    r = _as_series(returns)
    return float(r.std(ddof=1) * np.sqrt(periods_per_year)) if len(r) > 1 else 0.0


def sharpe_ratio(returns, risk_free: float = 0.0, periods_per_year: int = TRADING_DAYS) -> float:
    """Ratio de Sharpe anualizado. ``risk_free`` es la tasa libre de riesgo anual."""
    r = _as_series(returns)
    if len(r) < 2:
        return 0.0
    rf_per_period = (1.0 + risk_free) ** (1.0 / periods_per_year) - 1.0
    excess = r - rf_per_period
    std = excess.std(ddof=1)
    if std < 1e-12:  # volatilidad efectivamente nula -> Sharpe indefinido
        return 0.0
    return float(excess.mean() / std * np.sqrt(periods_per_year))


def sortino_ratio(returns, risk_free: float = 0.0, periods_per_year: int = TRADING_DAYS) -> float:
    """Ratio de Sortino: solo penaliza la volatilidad a la baja."""
    r = _as_series(returns)
    if len(r) < 2:
        return 0.0
    rf_per_period = (1.0 + risk_free) ** (1.0 / periods_per_year) - 1.0
    excess = r - rf_per_period
    downside = excess[excess < 0]
    dd = downside.std(ddof=1) if len(downside) > 1 else 0.0
    if dd < 1e-12:
        return 0.0
    return float(excess.mean() / dd * np.sqrt(periods_per_year))


def max_drawdown(returns) -> float:
    """Máxima caída desde un pico (valor negativo, p.ej. -0.23 = -23%)."""
    eq = equity_curve(returns)
    if eq.empty:
        return 0.0
    running_max = eq.cummax()
    drawdown = eq / running_max - 1.0
    return float(drawdown.min())


def calmar_ratio(returns, periods_per_year: int = TRADING_DAYS) -> float:
    """CAGR dividido por la máxima caída (en valor absoluto)."""
    mdd = abs(max_drawdown(returns))
    if mdd == 0:
        return 0.0
    return float(cagr(returns, periods_per_year) / mdd)


def win_rate(returns) -> float:
    r = _as_series(returns)
    active = r[r != 0]
    if len(active) == 0:
        return 0.0
    return float((active > 0).mean())


def summary(returns, periods_per_year: int = TRADING_DAYS, risk_free: float = 0.0) -> dict:
    """Diccionario con todas las métricas clave."""
    return {
        "total_return": total_return(returns),
        "cagr": cagr(returns, periods_per_year),
        "volatility": annual_volatility(returns, periods_per_year),
        "sharpe": sharpe_ratio(returns, risk_free, periods_per_year),
        "sortino": sortino_ratio(returns, risk_free, periods_per_year),
        "max_drawdown": max_drawdown(returns),
        "calmar": calmar_ratio(returns, periods_per_year),
        "win_rate": win_rate(returns),
    }


def format_summary(stats: dict) -> str:
    """Formatea el diccionario de métricas como texto legible."""
    return (
        f"  Retorno total : {stats['total_return']:8.2%}\n"
        f"  CAGR          : {stats['cagr']:8.2%}\n"
        f"  Volatilidad   : {stats['volatility']:8.2%}\n"
        f"  Sharpe        : {stats['sharpe']:8.2f}\n"
        f"  Sortino       : {stats['sortino']:8.2f}\n"
        f"  Max drawdown  : {stats['max_drawdown']:8.2%}\n"
        f"  Calmar        : {stats['calmar']:8.2f}\n"
        f"  Win rate      : {stats['win_rate']:8.2%}"
    )
