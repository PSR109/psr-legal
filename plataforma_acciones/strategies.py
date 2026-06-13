"""Librería de estrategias de trading.

Cada estrategia transforma una serie de precios en una serie de *posición
objetivo* en el rango [-1, 1]:

  * +1  = completamente largo (long)
  *  0  = en liquidez (flat)
  * -1  = completamente corto (short)

Las posiciones se calculan SIN mirar el futuro: la señal en el periodo ``t``
usa únicamente información disponible hasta ``t``. El backtester desplaza
además la señal un periodo para evitar sesgo de anticipación.

Cada estrategia expone ``param_space`` (rangos para el optimizador automático)
y se construye desde un diccionario de parámetros, de modo que el módulo de
aprendizaje pueda generar y mutar variantes libremente.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import indicators as ind


class Strategy:
    """Clase base. Las subclases implementan ``generate_signal``."""

    name = "base"
    #: rangos de búsqueda para el optimizador: {param: (low, high, is_int)}
    param_space: dict[str, tuple] = {}

    def __init__(self, **params):
        self.params = {**self.defaults(), **params}

    @classmethod
    def defaults(cls) -> dict:
        return {k: (v[0] + v[1]) / 2 if not v[2] else int((v[0] + v[1]) // 2)
                for k, v in cls.param_space.items()}

    def generate_signal(self, prices: pd.Series) -> pd.Series:  # pragma: no cover
        raise NotImplementedError

    def __repr__(self) -> str:
        ps = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.name}({ps})"


class MovingAverageCross(Strategy):
    """Cruce de medias móviles: largo cuando la rápida supera a la lenta."""

    name = "ma_cross"
    param_space = {
        "fast": (5, 50, True),
        "slow": (30, 200, True),
        "allow_short": (0, 1, True),
    }

    def generate_signal(self, prices: pd.Series) -> pd.Series:
        fast = int(self.params["fast"])
        slow = int(self.params["slow"])
        if fast >= slow:
            fast = max(2, slow // 2)
        f = ind.ema(prices, fast)
        s = ind.ema(prices, slow)
        sig = np.where(f > s, 1.0, -1.0 if self.params["allow_short"] else 0.0)
        return pd.Series(sig, index=prices.index)


class MeanReversion(Strategy):
    """Reversión a la media vía z-score: compra barato, vende caro."""

    name = "mean_reversion"
    param_space = {
        "window": (10, 60, True),
        "entry": (0.8, 2.5, False),
        "exit": (0.0, 0.6, False),
    }

    def generate_signal(self, prices: pd.Series) -> pd.Series:
        window = int(self.params["window"])
        entry = float(self.params["entry"])
        exit_z = float(self.params["exit"])
        z = ind.zscore(prices, window)
        pos = np.zeros(len(prices))
        state = 0.0
        zv = z.to_numpy()
        for i in range(len(zv)):
            if state == 0.0:
                if zv[i] < -entry:
                    state = 1.0
                elif zv[i] > entry:
                    state = -1.0
            elif state == 1.0 and zv[i] >= -exit_z:
                state = 0.0
            elif state == -1.0 and zv[i] <= exit_z:
                state = 0.0
            pos[i] = state
        return pd.Series(pos, index=prices.index)


class MomentumStrategy(Strategy):
    """Momentum de precio: sigue la tendencia reciente."""

    name = "momentum"
    param_space = {
        "lookback": (20, 180, True),
        "threshold": (0.0, 0.05, False),
        "allow_short": (0, 1, True),
    }

    def generate_signal(self, prices: pd.Series) -> pd.Series:
        lookback = int(self.params["lookback"])
        thr = float(self.params["threshold"])
        mom = ind.momentum(prices, lookback)
        sig = np.where(mom > thr, 1.0,
                       np.where(mom < -thr, -1.0 if self.params["allow_short"] else 0.0, 0.0))
        return pd.Series(sig, index=prices.index).fillna(0.0)


class RSIReversal(Strategy):
    """Reversión basada en RSI: largo en sobreventa, corto en sobrecompra."""

    name = "rsi_reversal"
    param_space = {
        "window": (7, 28, True),
        "low": (15, 40, False),
        "high": (60, 85, False),
    }

    def generate_signal(self, prices: pd.Series) -> pd.Series:
        window = int(self.params["window"])
        low = float(self.params["low"])
        high = float(self.params["high"])
        r = ind.rsi(prices, window)
        pos = np.zeros(len(prices))
        state = 0.0
        rv = r.to_numpy()
        for i in range(len(rv)):
            if rv[i] < low:
                state = 1.0
            elif rv[i] > high:
                state = -1.0
            elif 45 < rv[i] < 55:
                state = 0.0
            pos[i] = state
        return pd.Series(pos, index=prices.index)


class BollingerBreakout(Strategy):
    """Ruptura de bandas de Bollinger (seguimiento de tendencia)."""

    name = "bollinger_breakout"
    param_space = {
        "window": (10, 50, True),
        "num_std": (1.0, 3.0, False),
        "allow_short": (0, 1, True),
    }

    def generate_signal(self, prices: pd.Series) -> pd.Series:
        window = int(self.params["window"])
        num_std = float(self.params["num_std"])
        _, upper, lower = ind.bollinger(prices, window, num_std)
        long_sig = (prices > upper).astype(float)
        short_sig = (prices < lower).astype(float) if self.params["allow_short"] else 0.0
        sig = long_sig - short_sig
        return sig.replace(0.0, np.nan).ffill().fillna(0.0)


class TrendFollowing(Strategy):
    """Seguimiento de tendencia con sesgo largo y filtro de tendencia lenta.

    Mantiene exposición larga mientras el precio esté por encima de su media
    lenta y el momentum sea positivo; reduce a liquidez en caso contrario. Es
    robusta y de bajo turnover, pensada para capturar la deriva de largo plazo
    del activo sin pelearse con ella.
    """

    name = "trend_following"
    param_space = {
        "trend_window": (50, 200, True),
        "mom_window": (20, 120, True),
        "scale_down": (0, 1, True),
    }

    def generate_signal(self, prices: pd.Series) -> pd.Series:
        tw = int(self.params["trend_window"])
        mw = int(self.params["mom_window"])
        trend_up = prices > ind.sma(prices, tw)
        mom = ind.momentum(prices, mw).fillna(0.0)
        if self.params["scale_down"]:
            # Exposición proporcional a la fuerza del momentum (0..1), solo largo.
            strength = (mom.clip(lower=0) / (mom.abs().rolling(mw, min_periods=1).mean() + 1e-9))
            sig = trend_up.astype(float) * strength.clip(0, 1.0)
        else:
            sig = (trend_up & (mom > 0)).astype(float)
        return sig.fillna(0.0)


#: Registro de estrategias disponibles por nombre.
STRATEGY_REGISTRY: dict[str, type[Strategy]] = {
    cls.name: cls
    for cls in (MovingAverageCross, MeanReversion, MomentumStrategy,
                RSIReversal, BollingerBreakout, TrendFollowing)
}


def build(name: str, **params) -> Strategy:
    """Construye una estrategia por nombre desde parámetros arbitrarios."""
    if name not in STRATEGY_REGISTRY:
        raise KeyError(f"Estrategia desconocida: {name!r}. "
                       f"Disponibles: {list(STRATEGY_REGISTRY)}")
    return STRATEGY_REGISTRY[name](**params)
