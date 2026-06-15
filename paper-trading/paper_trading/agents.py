"""Strategy agents and risk management.

Each strategy agent is independent and emits *target weights* (the fraction
of equity to allocate per symbol; negative = short). The coordinator (see
``engine.py``) blends agents into one portfolio and the risk manager
constrains it before orders are generated.

None of these strategies guarantees profit. On efficient, random-walk price
paths they have no edge and lose money to commissions and slippage. They can
appear profitable only when the data has exploitable structure (trend or
mean-reversion) — which real markets do not reliably provide.
"""
from __future__ import annotations

import statistics


def _sma(series, n):
    if len(series) < n:
        return None
    return sum(series[-n:]) / n


def _normalize(raw):
    """Scale raw scores so the gross (sum of absolute weights) is 1."""
    gross = sum(abs(v) for v in raw.values())
    if gross == 0:
        return {}
    return {s: v / gross for s, v in raw.items()}


class StrategyAgent:
    name = "base"

    def target_weights(self, market) -> dict:
        raise NotImplementedError


class MomentumAgent(StrategyAgent):
    """Long instruments trading above their moving average, short those below."""

    name = "momentum"

    def __init__(self, lookback: int = 50, universe=None):
        self.lookback = lookback
        self.universe = universe

    def target_weights(self, market):
        symbols = self.universe or market.symbols
        raw = {}
        for s in symbols:
            hist = market.history[s]
            sma = _sma(hist, self.lookback)
            if sma is None or sma == 0:
                continue
            raw[s] = (hist[-1] - sma) / sma
        return _normalize(raw)


class MeanReversionAgent(StrategyAgent):
    """Fade short-term deviations: long the cheap, short the rich (z-score)."""

    name = "mean_reversion"

    def __init__(self, lookback: int = 20, universe=None):
        self.lookback = lookback
        self.universe = universe

    def target_weights(self, market):
        symbols = self.universe or market.symbols
        raw = {}
        for s in symbols:
            hist = market.history[s]
            if len(hist) < self.lookback:
                continue
            window = hist[-self.lookback:]
            mean = sum(window) / len(window)
            sd = statistics.pstdev(window)
            if sd == 0:
                continue
            raw[s] = -(hist[-1] - mean) / sd
        return _normalize(raw)


class RiskManager:
    """Constrains blended target weights.

    - ``max_per_name``: cap on any single position's weight.
    - ``max_gross``: cap on total gross exposure (leverage).
    - ``max_drawdown``: kill-switch; if the current drawdown reaches this
      level the book is forced flat.
    """

    def __init__(self, max_gross: float = 1.0,
                 max_per_name: float = 0.25, max_drawdown: float = 0.20):
        self.max_gross = max_gross
        self.max_per_name = max_per_name
        self.max_drawdown = max_drawdown

    def constrain(self, weights: dict, drawdown: float) -> dict:
        if drawdown >= self.max_drawdown:
            return {}  # risk-off: go flat
        cap = self.max_per_name
        capped = {s: max(-cap, min(cap, w)) for s, w in weights.items()}
        gross = sum(abs(w) for w in capped.values())
        if gross > self.max_gross and gross > 0:
            scale = self.max_gross / gross
            capped = {s: w * scale for s, w in capped.items()}
        return capped
