"""Honest performance metrics computed from an equity curve.

These describe what happened in *this particular simulation*. Simulated or
past performance does not predict — and certainly does not guarantee —
future results.
"""
from __future__ import annotations

import math
import statistics


def _period_returns(equity):
    return [equity[i] / equity[i - 1] - 1
            for i in range(1, len(equity)) if equity[i - 1] > 0]


def max_drawdown(equity) -> float:
    peak = equity[0]
    worst = 0.0
    for v in equity:
        peak = max(peak, v)
        if peak > 0:
            worst = max(worst, 1 - v / peak)
    return worst


def summarize(equity, periods_per_year: int = 252) -> dict:
    if len(equity) < 2 or equity[0] <= 0:
        return {}
    rets = _period_returns(equity)
    years = len(equity) / periods_per_year
    cagr = (equity[-1] / equity[0]) ** (1 / years) - 1 if years > 0 else float("nan")
    vol = statistics.pstdev(rets) * math.sqrt(periods_per_year) if len(rets) > 1 else 0.0
    mean_annual = statistics.fmean(rets) * periods_per_year if rets else 0.0
    sharpe = mean_annual / vol if vol > 0 else float("nan")
    dd = max_drawdown(equity)
    calmar = cagr / dd if dd > 0 else float("nan")
    return {
        "total_return": equity[-1] / equity[0] - 1,
        "cagr": cagr,
        "annual_vol": vol,
        "sharpe": sharpe,
        "max_drawdown": dd,
        "calmar": calmar,
        "final_equity": equity[-1],
    }
