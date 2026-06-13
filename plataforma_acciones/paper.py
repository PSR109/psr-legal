"""Paper trading: simulación de operativa con dinero ficticio.

A diferencia del backtest vectorizado (`backtest.py`), este módulo simula una
cuenta real paso a paso, como si operase en vivo:

  * Un "broker" mantiene un libro mayor explícito: caja, posiciones en unidades
    (acciones/contratos/monedas) y patrimonio valorado a mercado cada día.
  * Cada día el sistema decide posiciones objetivo usando SOLO información
    disponible hasta ese momento (las señales son causales) y, en los días de
    rebalanceo, envía órdenes que pagan comisiones y slippage reales.
  * El aprendizaje online (algoritmo Hedge) sigue actualizándose CADA día con el
    rendimiento realizado: el sistema aprende mientras opera.

Es la forma honesta de probar el funcionamiento antes de arriesgar dinero real:
mismo flujo de eventos que una cuenta en producción, pero con capital ficticio.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import indicators, learning, metrics
from .strategies import STRATEGY_REGISTRY


@dataclass
class Trade:
    date: pd.Timestamp
    asset: str
    units: float          # +compra / -venta
    price: float
    cost: float           # comisión + slippage pagados


@dataclass
class PaperBroker:
    """Cuenta de corretaje simulada con libro mayor explícito."""

    cash: float
    cost_per_trade: float = 0.0005
    slippage: float = 0.0002
    positions: dict[str, float] = field(default_factory=dict)
    trades: list[Trade] = field(default_factory=list)

    def equity(self, prices: pd.Series) -> float:
        """Patrimonio = caja + valor de mercado de las posiciones."""
        mv = sum(u * prices[a] for a, u in self.positions.items())
        return self.cash + mv

    def gross_exposure(self, prices: pd.Series) -> float:
        eq = self.equity(prices)
        if eq <= 0:
            return 0.0
        return sum(abs(u * prices[a]) for a, u in self.positions.items()) / eq

    def rebalance(self, date, prices: pd.Series, target_weights: dict[str, float]):
        """Lleva la cartera a los pesos objetivo (en fracción de patrimonio)."""
        eq = self.equity(prices)
        if eq <= 0:
            return
        for asset, w in target_weights.items():
            price = prices[asset]
            if price <= 0 or not np.isfinite(price):
                continue
            target_units = (w * eq) / price
            current = self.positions.get(asset, 0.0)
            delta = target_units - current
            if abs(delta * price) < 1e-6 * eq:   # ignora micro-órdenes
                continue
            cost = abs(delta * price) * (self.cost_per_trade + self.slippage)
            self.cash -= delta * price + cost
            self.positions[asset] = target_units
            self.trades.append(Trade(date, asset, delta, price, cost))


@dataclass
class PaperConfig:
    initial_cash: float = 100_000.0
    warmup_periods: int = 252          # historia inicial para "calentar" señales
    rebalance_days: int = 5            # rebalanceo semanal
    target_vol: float = 0.15
    max_leverage: float = 2.0
    vol_window: int = 20
    strategy_eta: float = 12.0
    asset_eta: float = 6.0
    hedge_decay: float = 0.985
    cost_per_trade: float = 0.0005
    slippage: float = 0.0002
    periods_per_year: int = 252
    risk_off: bool = False             # reduce exposición en mercado bajista
    risk_off_window: int = 80
    risk_off_floor: float = 0.25


@dataclass
class PaperResult:
    equity_curve: pd.Series
    returns: pd.Series
    trades: list[Trade]
    stats: dict
    broker: PaperBroker
    total_costs: float


def _precompute_signals(prices: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Señales causales de cada estrategia por activo, sobre todo el histórico.

    Como todas las estrategias son causales (la señal en t solo usa datos <= t),
    calcular la serie completa y luego indexar día a día es equivalente a
    recalcular cada día, sin introducir sesgo de anticipación, y mucho más rápido.
    """
    out = {}
    for asset in prices.columns:
        cols = {name: STRATEGY_REGISTRY[name]().generate_signal(prices[asset])
                for name in STRATEGY_REGISTRY}
        out[asset] = pd.DataFrame(cols, index=prices.index)
    return out


class PaperTrader:
    """Motor de paper trading dirigido por eventos (día a día)."""

    def __init__(self, prices: pd.DataFrame, cfg: PaperConfig | None = None):
        self.prices = prices
        self.cfg = cfg or PaperConfig()
        self.assets = list(prices.columns)
        self.strategy_names = list(STRATEGY_REGISTRY)

    def run(self, verbose: bool = False) -> PaperResult:
        cfg = self.cfg
        prices = self.prices
        signals = _precompute_signals(prices)
        asset_rets = prices.pct_change().fillna(0.0)

        # Filtro risk-off precomputado (causal): exposición en [floor, 1].
        if cfg.risk_off:
            idx = (prices / prices.iloc[0]).mean(axis=1)
            up = (idx > indicators.sma(idx, cfg.risk_off_window)).astype(float)
            risk_gate = (cfg.risk_off_floor + (1.0 - cfg.risk_off_floor) * up).shift(1).fillna(1.0)
        else:
            risk_gate = pd.Series(1.0, index=prices.index)

        broker = PaperBroker(cash=cfg.initial_cash,
                             cost_per_trade=cfg.cost_per_trade, slippage=cfg.slippage)
        n_strat = len(self.strategy_names)
        strat_alloc = {a: learning.HedgeAllocator(n_strat, cfg.strategy_eta, cfg.hedge_decay)
                       for a in self.assets}
        asset_alloc = learning.HedgeAllocator(len(self.assets), cfg.asset_eta, cfg.hedge_decay)

        dates = prices.index
        equity_hist, eq_dates = [], []
        # Retornos UNapalancados de la cartera, para calibrar el control de vol.
        # (Estimar la vol sobre los retornos ya apalancados crea un bucle de
        #  control mal calibrado y la vol realizada se dispara por encima del
        #  objetivo; por eso seguimos la vol de la señal SIN apalancar.)
        unlev_rets: list[float] = []
        prev_unlev_weights = np.zeros(len(self.assets))
        start = cfg.warmup_periods

        for i in range(start, len(dates)):
            date = dates[i]
            today = prices.iloc[i]
            ret_vec = np.array([asset_rets[a].iloc[i] for a in self.assets])

            # Retorno unapalancado realizado de AYER -> hoy (para la vol objetivo).
            unlev_rets.append(float(np.dot(prev_unlev_weights, np.nan_to_num(ret_vec))))

            # --- Aprendizaje online con el rendimiento realizado de AYER (causal) ---
            combined_sig_prev = {}
            for a in self.assets:
                sig_prev = signals[a].iloc[i - 1][self.strategy_names].to_numpy()
                ret_today = asset_rets[a].iloc[i]
                strat_realized = np.nan_to_num(sig_prev * ret_today)
                strat_alloc[a].update(strat_realized)
                ws = strat_alloc[a].allocate()
                combined_sig_prev[a] = float(np.dot(ws, np.nan_to_num(sig_prev)))
            asset_realized = np.array([combined_sig_prev[a] * asset_rets[a].iloc[i]
                                       for a in self.assets])
            asset_alloc.update(asset_realized)

            # --- Decisión de HOY (señales hasta hoy) ---
            wa = asset_alloc.allocate()
            sig_today = {}
            for j, a in enumerate(self.assets):
                s = signals[a].iloc[i][self.strategy_names].to_numpy()
                ws = strat_alloc[a].allocate()
                sig_today[a] = float(np.dot(ws, np.nan_to_num(s)))

            # Control de volatilidad calibrado sobre la vol UNapalancada reciente.
            if len(unlev_rets) >= cfg.vol_window:
                rv = np.std(unlev_rets[-cfg.vol_window:], ddof=0) * np.sqrt(cfg.periods_per_year)
                lev = min(cfg.max_leverage, cfg.target_vol / rv) if rv > 1e-9 else 1.0
            else:
                lev = 1.0
            lev *= float(risk_gate.iloc[i])   # risk-off solo reduce exposición

            # Pesos unapalancados de hoy (para la vol de mañana).
            prev_unlev_weights = np.array([wa[j] * sig_today[a]
                                           for j, a in enumerate(self.assets)])

            target_weights = {a: float(np.clip(wa[j] * sig_today[a] * lev,
                                               -cfg.max_leverage, cfg.max_leverage))
                              for j, a in enumerate(self.assets)}

            # --- Rebalanceo según calendario ---
            if (i - start) % cfg.rebalance_days == 0:
                broker.rebalance(date, today, target_weights)

            eq = broker.equity(today)
            equity_hist.append(eq); eq_dates.append(date)

            if verbose and (i - start) % 63 == 0:
                print(f"{date.date()} | patrimonio {eq:12,.0f} | "
                      f"exposición {broker.gross_exposure(today):4.2f}x | "
                      f"operaciones {len(broker.trades):4d}", flush=True)

        equity_curve = pd.Series(equity_hist, index=pd.DatetimeIndex(eq_dates))
        returns = equity_curve.pct_change().fillna(0.0)
        stats = metrics.summary(returns, cfg.periods_per_year)
        total_costs = sum(t.cost for t in broker.trades)
        return PaperResult(equity_curve, returns, broker.trades, stats, broker, total_costs)
