"""Fuentes de datos de mercado.

Soporta dos modos:

1. ``SyntheticMarket``: genera precios sintéticos realistas (movimiento
   browniano geométrico con cambios de régimen, tendencias y saltos). Esto
   permite que toda la plataforma —backtest, aprendizaje, tests— funcione de
   forma totalmente reproducible y sin depender de servicios externos.

2. ``load_prices``: intenta descargar datos reales vía ``yfinance`` si está
   instalado y hay red; si falla, cae automáticamente al generador sintético.
   Así el usuario puede pasar a datos reales sin cambiar el resto del código.

Todas las funciones devuelven un ``pandas.DataFrame`` de precios de cierre con
un ``DatetimeIndex`` y una columna por activo.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class AssetSpec:
    """Parámetros del proceso generador de un activo sintético."""

    name: str
    mu: float          # deriva anual (drift) esperada
    sigma: float       # volatilidad anual
    asset_class: str = "equity"   # equity | etf | crypto | fx | future | option
    jump_intensity: float = 0.0   # prob. diaria de un salto
    jump_size: float = 0.0        # magnitud típica del salto


# Universo por defecto que cubre varias clases de activo, tal como pide el
# objetivo: ETFs, acciones, cripto, divisas y futuros. Los parámetros son
# verosímiles pero NO son predicciones de mercados reales.
DEFAULT_UNIVERSE: list[AssetSpec] = [
    AssetSpec("SPY_ETF",   mu=0.08, sigma=0.16, asset_class="etf"),
    AssetSpec("QQQ_ETF",   mu=0.11, sigma=0.22, asset_class="etf"),
    AssetSpec("AAPL",      mu=0.12, sigma=0.28, asset_class="equity"),
    AssetSpec("MSFT",      mu=0.11, sigma=0.26, asset_class="equity"),
    AssetSpec("NVDA",      mu=0.18, sigma=0.45, asset_class="equity",
              jump_intensity=0.01, jump_size=0.05),
    AssetSpec("BTC",       mu=0.20, sigma=0.65, asset_class="crypto",
              jump_intensity=0.02, jump_size=0.08),
    AssetSpec("ETH",       mu=0.22, sigma=0.75, asset_class="crypto",
              jump_intensity=0.02, jump_size=0.09),
    AssetSpec("EURUSD",    mu=0.01, sigma=0.08, asset_class="fx"),
    AssetSpec("GOLD_FUT",  mu=0.05, sigma=0.14, asset_class="future"),
    AssetSpec("OIL_FUT",   mu=0.04, sigma=0.35, asset_class="future",
              jump_intensity=0.01, jump_size=0.06),
]


@dataclass
class SyntheticMarket:
    """Generador de precios sintéticos con regímenes de mercado.

    El mercado alterna entre regímenes (alcista, bajista, lateral) que modulan
    la deriva y la volatilidad de *todos* los activos simultáneamente, creando
    correlaciones realistas y oportunidades para estrategias adaptativas.
    """

    universe: list[AssetSpec] = field(default_factory=lambda: list(DEFAULT_UNIVERSE))
    periods_per_year: int = 252
    seed: int | None = 42

    def generate(self, n_periods: int = 252 * 6, start: str = "2018-01-01") -> pd.DataFrame:
        rng = np.random.default_rng(self.seed)
        dt = 1.0 / self.periods_per_year

        # Cadena de Markov de regímenes: 0=alcista, 1=bajista, 2=lateral.
        regime_drift_mult = np.array([1.3, -1.1, 0.2])
        regime_vol_mult = np.array([0.9, 1.8, 0.7])
        # Matriz de transición persistente (los regímenes duran semanas/meses).
        trans = np.array([
            [0.985, 0.008, 0.007],
            [0.020, 0.965, 0.015],
            [0.020, 0.010, 0.970],
        ])
        regimes = np.empty(n_periods, dtype=int)
        regimes[0] = 0
        for t in range(1, n_periods):
            regimes[t] = rng.choice(3, p=trans[regimes[t - 1]])

        # Factor de mercado común que induce correlación entre activos.
        market_shock = rng.standard_normal(n_periods)

        index = pd.bdate_range(start=start, periods=n_periods)
        prices = {}
        for spec in self.universe:
            mu_t = spec.mu * regime_drift_mult[regimes]
            sigma_t = spec.sigma * regime_vol_mult[regimes]

            idio = rng.standard_normal(n_periods)
            beta = 0.6 if spec.asset_class in ("etf", "equity") else 0.3
            shock = beta * market_shock + np.sqrt(max(1e-9, 1 - beta**2)) * idio

            log_ret = (mu_t - 0.5 * sigma_t**2) * dt + sigma_t * np.sqrt(dt) * shock

            if spec.jump_intensity > 0:
                jumps = rng.random(n_periods) < spec.jump_intensity
                jump_dir = rng.choice([-1.0, 1.0], size=n_periods)
                log_ret += jumps * jump_dir * spec.jump_size

            price = 100.0 * np.exp(np.cumsum(log_ret))
            prices[spec.name] = price

        df = pd.DataFrame(prices, index=index)
        # Régimen "verdadero" disponible aparte (no en df.attrs, que rompería
        # pd.concat al contener objetos no comparables con ==).
        self.last_regimes = pd.Series(regimes, index=index)
        return df


def load_prices(
    symbols: list[str] | None = None,
    period_days: int = 252 * 6,
    use_real: bool = False,
    start: str = "2018-01-01",
    seed: int | None = 42,
) -> pd.DataFrame:
    """Carga precios de cierre.

    Si ``use_real`` es True intenta ``yfinance``; ante cualquier fallo (sin red,
    paquete ausente, símbolo inválido) cae al generador sintético para que el
    sistema nunca se quede sin datos.
    """
    if use_real and symbols:
        try:  # pragma: no cover - depende de red y de un paquete opcional
            import yfinance as yf

            data = yf.download(symbols, period="max", auto_adjust=True, progress=False)
            close = data["Close"] if "Close" in data else data
            close = close.dropna(how="all").ffill().dropna()
            if not close.empty:
                return close
        except Exception:
            pass  # fallback silencioso a datos sintéticos

    market = SyntheticMarket(seed=seed)
    if symbols:
        market.universe = [s for s in DEFAULT_UNIVERSE if s.name in symbols] or list(DEFAULT_UNIVERSE)
    return market.generate(n_periods=period_days, start=start)


def to_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Retornos simples por periodo a partir de precios."""
    return prices.pct_change().fillna(0.0)
