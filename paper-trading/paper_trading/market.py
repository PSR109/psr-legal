"""Synthetic market data feed.

The simulator needs no network or data files: prices are produced by
stochastic processes, so runs are fully reproducible offline. A real data
feed can be plugged in by implementing the same ``step()`` interface that
``SyntheticMarket`` exposes (advance one bar, expose ``prices()`` and
per-symbol ``history``).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass


class PriceProcess:
    """A price process returns the multiplicative factor for one bar."""

    def step(self, rng: random.Random, dt: float) -> float:
        raise NotImplementedError


@dataclass
class GBMProcess(PriceProcess):
    """Geometric Brownian motion. ``mu``/``sigma`` are the (unknown to the
    agents) annual drift and volatility."""

    mu: float
    sigma: float

    def step(self, rng, dt):
        z = rng.gauss(0.0, 1.0)
        drift = (self.mu - 0.5 * self.sigma ** 2) * dt
        shock = self.sigma * math.sqrt(dt) * z
        return math.exp(drift + shock)


@dataclass
class MomentumGBMProcess(PriceProcess):
    """GBM whose drift persists inside a slowly switching regime. This gives
    the series mild positive autocorrelation that trend-followers can exploit
    (but it is still random — there is no guaranteed edge)."""

    base_sigma: float
    switch_prob: float = 0.02
    drift_scale: float = 0.30
    regime_drift: float = 0.0

    def step(self, rng, dt):
        if rng.random() < self.switch_prob:
            self.regime_drift = rng.gauss(0.0, self.drift_scale)
        z = rng.gauss(0.0, 1.0)
        drift = (self.regime_drift - 0.5 * self.base_sigma ** 2) * dt
        shock = self.base_sigma * math.sqrt(dt) * z
        return math.exp(drift + shock)


@dataclass
class OUProcess(PriceProcess):
    """Ornstein-Uhlenbeck (mean-reverting) process in log-price, suited to
    FX-style series that revert toward a long-run level."""

    sigma: float
    kappa: float = 3.0
    log_level: float = 0.0
    _log_dev: float = 0.0

    def step(self, rng, dt):
        z = rng.gauss(0.0, 1.0)
        new_dev = (
            self._log_dev
            + self.kappa * (self.log_level - self._log_dev) * dt
            + self.sigma * math.sqrt(dt) * z
        )
        factor = math.exp(new_dev - self._log_dev)
        self._log_dev = new_dev
        return factor


@dataclass
class Instrument:
    symbol: str
    asset_class: str
    price: float
    process: PriceProcess


class SyntheticMarket:
    """Advances a basket of instruments one bar at a time and keeps history."""

    def __init__(self, instruments, seed: int = 42, dt: float = 1 / 252):
        self.instruments = {i.symbol: i for i in instruments}
        self.rng = random.Random(seed)
        self.dt = dt
        self.t = 0
        self.history = {s: [i.price] for s, i in self.instruments.items()}

    @property
    def symbols(self):
        return list(self.instruments)

    def prices(self):
        return {s: i.price for s, i in self.instruments.items()}

    def asset_class(self, symbol):
        return self.instruments[symbol].asset_class

    def step(self):
        self.t += 1
        for symbol, inst in self.instruments.items():
            factor = inst.process.step(self.rng, self.dt)
            inst.price = max(1e-9, inst.price * factor)
            self.history[symbol].append(inst.price)
        return self.prices()
