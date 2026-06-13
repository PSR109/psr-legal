"""Motor de backtesting vectorizado.

Convierte una serie de posiciones objetivo en una serie de retornos de la
estrategia, aplicando:

  * Desfase de la señal un periodo (evita sesgo de anticipación / look-ahead).
  * Costes de transacción proporcionales al cambio de posición (turnover).
  * Slippage por operación.
  * Escalado por volatilidad objetivo (volatility targeting) opcional, una
    forma sencilla de control de riesgo: reduce exposición cuando la
    volatilidad sube y la aumenta (con tope de apalancamiento) cuando baja.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import metrics


@dataclass
class BacktestConfig:
    cost_per_trade: float = 0.0005      # 5 pbs por unidad de turnover
    slippage: float = 0.0002            # 2 pbs de slippage
    target_volatility: float | None = 0.15  # vol anual objetivo; None lo desactiva
    max_leverage: float = 1.5           # apalancamiento máximo del escalado de vol
    vol_window: int = 20
    periods_per_year: int = 252


@dataclass
class BacktestResult:
    returns: pd.Series          # retornos netos de la estrategia por periodo
    positions: pd.Series        # posición efectiva aplicada (tras desfase/escalado)
    stats: dict                 # métricas resumidas

    @property
    def equity(self) -> pd.Series:
        return metrics.equity_curve(self.returns)


def _vol_scaled_positions(positions: pd.Series, asset_returns: pd.Series,
                          cfg: BacktestConfig) -> pd.Series:
    """Escala la posición para apuntar a una volatilidad anual objetivo."""
    if cfg.target_volatility is None:
        return positions.clip(-cfg.max_leverage, cfg.max_leverage)
    realized = asset_returns.rolling(cfg.vol_window, min_periods=5).std(ddof=0)
    realized_annual = realized * np.sqrt(cfg.periods_per_year)
    scale = (cfg.target_volatility / realized_annual.replace(0.0, np.nan))
    scale = scale.clip(upper=cfg.max_leverage).fillna(0.0)
    return (positions * scale).clip(-cfg.max_leverage, cfg.max_leverage)


def run(prices: pd.Series, positions: pd.Series,
        cfg: BacktestConfig | None = None) -> BacktestResult:
    """Ejecuta el backtest de una estrategia sobre un activo."""
    cfg = cfg or BacktestConfig()
    asset_returns = prices.pct_change().fillna(0.0)

    scaled = _vol_scaled_positions(positions, asset_returns, cfg)
    # Desfase: la posición decidida en t se aplica al retorno de t+1.
    applied = scaled.shift(1).fillna(0.0)

    gross = applied * asset_returns

    turnover = applied.diff().abs().fillna(applied.abs())
    costs = turnover * (cfg.cost_per_trade + cfg.slippage)

    net = (gross - costs).fillna(0.0)
    stats = metrics.summary(net, cfg.periods_per_year)
    return BacktestResult(returns=net, positions=applied, stats=stats)


def run_strategy(prices: pd.Series, strategy, cfg: BacktestConfig | None = None) -> BacktestResult:
    """Atajo: genera la señal de una estrategia y la backtestea."""
    signal = strategy.generate_signal(prices)
    return run(prices, signal, cfg)
