"""Orquestador walk-forward de la plataforma con aprendizaje online de dos niveles.

Para cada ventana temporal (rodante):

  1. OPTIMIZA (in-sample): para cada activo afina los parámetros de TODAS las
     estrategias del registro sobre el tramo de entrenamiento, usando una
     división interna train/validación para evitar sobreajuste. No descarta
     ninguna estrategia: construye un "menú" afinado por activo.

  2. APRENDE EN DOS NIVELES (out-of-sample):
       - Nivel 1 (por activo): un ``HedgeAllocator`` reparte peso entre las
         estrategias del menú y, periodo a periodo, concentra capital en las
         que mejor rinden en el régimen actual. Así el sistema *descubre solo*
         que el seguimiento de tendencia funciona, sin tenerlo cableado.
       - Nivel 2 (cartera): otro ``HedgeAllocator`` reparte entre activos.
     Los pesos se conservan entre ventanas: el sistema mejora con el tiempo.

  3. CONTROLA EL RIESGO: la cartera combinada se escala a una volatilidad anual
     objetivo (volatility targeting).

El resultado es una curva de capital 100% out-of-sample, la estimación más
honesta de lo que la estrategia habría hecho sobre datos no vistos.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import backtest, indicators, learning, metrics
from .strategies import STRATEGY_REGISTRY


@dataclass
class EngineConfig:
    train_periods: int = 252 * 2       # 2 años de entrenamiento
    test_periods: int = 63             # ~1 trimestre de evaluación OOS
    target_cagr: float = 0.15
    backtest: backtest.BacktestConfig = field(default_factory=backtest.BacktestConfig)
    optimize: bool = False             # afinar params por ventana (sobreajusta; ver README)
    strategy_eta: float = 12.0         # tasa de aprendizaje nivel 1 (estrategias)
    asset_eta: float = 6.0             # tasa de aprendizaje nivel 2 (activos)
    hedge_decay: float = 0.985
    portfolio_target_vol: float = 0.15
    portfolio_max_leverage: float = 3.0
    vol_window: int = 20
    risk_off: bool = False             # filtro risk-off: reduce exposición en mercado bajista
    risk_off_window: int = 80
    risk_off_floor: float = 0.25       # exposición mínima cuando el mercado cae
    n_workers: int = 4
    opt_seed: int = 0
    verbose: bool = False


@dataclass
class WindowReport:
    start: pd.Timestamp
    end: pd.Timestamp
    chosen: dict             # activo -> {estrategia: (params, score validación)}
    oos_returns: pd.Series    # retorno de cartera (pre vol-target) en OOS


@dataclass
class EngineResult:
    portfolio_returns: pd.Series
    windows: list[WindowReport]
    stats: dict
    final_asset_weights: pd.Series
    final_strategy_weights: pd.DataFrame   # filas=activos, columnas=estrategias

    @property
    def equity(self) -> pd.Series:
        return metrics.equity_curve(self.portfolio_returns)


# Worker a nivel de módulo (serializable por multiprocessing).
def _optimize_asset(args):
    asset, series, cfg_bt, target, seed = args
    menu = learning.optimize_each_strategy(series, cfg_bt, target, seed=seed)
    return asset, menu


class WalkForwardEngine:
    def __init__(self, prices: pd.DataFrame, cfg: EngineConfig | None = None):
        self.prices = prices
        self.cfg = cfg or EngineConfig()
        self.assets = list(prices.columns)
        self.strategy_names = list(STRATEGY_REGISTRY)

    def _default_menu(self) -> dict:
        """Menú con parámetros robustos por defecto (sin optimizar)."""
        menu = {}
        for name in self.strategy_names:
            cls = STRATEGY_REGISTRY[name]
            menu[name] = learning.OptimizationResult(name, cls.defaults(), 0.0, {})
        return {a: dict(menu) for a in self.assets}

    def _optimize_window(self, train: pd.DataFrame, seed: int) -> dict:
        if not self.cfg.optimize:
            return self._default_menu()
        jobs = [
            (asset, train[asset], self.cfg.backtest, self.cfg.target_cagr, seed + i * 7)
            for i, asset in enumerate(self.assets)
        ]
        out: dict = {}
        if self.cfg.n_workers > 1 and len(jobs) > 1:
            with ProcessPoolExecutor(max_workers=self.cfg.n_workers) as ex:
                for asset, menu in ex.map(_optimize_asset, jobs):
                    out[asset] = menu
        else:
            for job in jobs:
                asset, menu = _optimize_asset(job)
                out[asset] = menu
        return out

    def _strategy_returns(self, menu: dict, series: pd.Series, test_index) -> pd.DataFrame:
        """Matriz [periodos OOS x estrategias] de retornos de cada estrategia."""
        cols = {}
        for name, opt in menu.items():
            strat = STRATEGY_REGISTRY[name](**opt.params)
            res = backtest.run_strategy(series, strat, self.cfg.backtest)
            cols[name] = res.returns
        return pd.DataFrame(cols, index=series.index).loc[test_index]

    def _vol_target(self, returns: pd.Series) -> pd.Series:
        cfg = self.cfg
        realized = returns.rolling(cfg.vol_window, min_periods=5).std(ddof=0)
        realized_annual = realized * np.sqrt(cfg.backtest.periods_per_year)
        scale = (cfg.portfolio_target_vol / realized_annual.replace(0.0, np.nan))
        scale = scale.clip(upper=cfg.portfolio_max_leverage).ffill().fillna(1.0)
        return returns * scale.shift(1).fillna(1.0)

    def _risk_off_gate(self, index) -> pd.Series:
        """Factor de exposición en [floor, 1] que solo REDUCE en mercado bajista.

        Cuando el índice equiponderado cae por debajo de su media móvil, recorta
        la exposición hacia ``risk_off_floor``; nunca apalanca. Reduce de forma
        notable las caídas catastróficas a cambio de ceder algo de retorno medio.
        """
        cfg = self.cfg
        idx = (self.prices / self.prices.iloc[0]).mean(axis=1)
        up = (idx > indicators.sma(idx, cfg.risk_off_window)).astype(float)
        gate = cfg.risk_off_floor + (1.0 - cfg.risk_off_floor) * up
        return gate.shift(1).fillna(1.0).reindex(index).fillna(1.0)

    def run(self) -> EngineResult:
        cfg = self.cfg
        n = len(self.prices)
        train_n, test_n = cfg.train_periods, cfg.test_periods
        n_strat = len(self.strategy_names)

        # Asignadores online persistentes (aprenden a lo largo de TODAS las ventanas).
        asset_alloc = learning.HedgeAllocator(len(self.assets), cfg.asset_eta, cfg.hedge_decay)
        strat_alloc = {
            a: learning.HedgeAllocator(n_strat, cfg.strategy_eta, cfg.hedge_decay)
            for a in self.assets
        }

        raw_returns: list[pd.Series] = []
        windows: list[WindowReport] = []
        start, win = 0, 0

        while start + train_n + test_n <= n:
            train = self.prices.iloc[start:start + train_n]
            ctx = self.prices.iloc[start:start + train_n + test_n]
            test_index = ctx.index[train_n:]
            menu_by_asset = self._optimize_window(train, seed=cfg.opt_seed + win * 101)

            # Nivel 1: por activo, combinar estrategias con aprendizaje online.
            asset_oos = {}
            for asset in self.assets:
                menu = menu_by_asset[asset]
                sr = self._strategy_returns(menu, ctx[asset], test_index)
                sr = sr[self.strategy_names]  # orden fijo
                mat = np.nan_to_num(sr.to_numpy())
                alloc = strat_alloc[asset]
                out = np.zeros(len(sr))
                for t in range(len(sr)):
                    w = alloc.allocate()
                    out[t] = float(np.dot(w, mat[t]))
                    alloc.update(mat[t])
                asset_oos[asset] = out

            asset_mat = np.column_stack([asset_oos[a] for a in self.assets])

            # Nivel 2: combinar activos con aprendizaje online.
            port = np.zeros(len(test_index))
            for t in range(len(test_index)):
                w = asset_alloc.allocate()
                port[t] = float(np.dot(w, asset_mat[t]))
                asset_alloc.update(asset_mat[t])

            port_series = pd.Series(port, index=test_index)
            raw_returns.append(port_series)
            windows.append(WindowReport(
                start=test_index[0], end=test_index[-1],
                chosen={a: {n: (o.params, o.score) for n, o in menu_by_asset[a].items()}
                        for a in self.assets},
                oos_returns=port_series,
            ))

            if cfg.verbose:
                ws = metrics.summary(port_series, cfg.backtest.periods_per_year)
                print(f"[ventana {win:>2}] {test_index[0].date()} -> {test_index[-1].date()} "
                      f"| CAGR {ws['cagr']:7.2%} | Sharpe {ws['sharpe']:5.2f}", flush=True)

            start += test_n
            win += 1

        raw = pd.concat(raw_returns) if raw_returns else pd.Series(dtype=float)
        portfolio = self._vol_target(raw)
        if cfg.risk_off and len(portfolio):
            portfolio = portfolio * self._risk_off_gate(portfolio.index)
        stats = metrics.summary(portfolio, cfg.backtest.periods_per_year)

        final_aw = pd.Series(asset_alloc.allocate(), index=self.assets)
        final_sw = pd.DataFrame(
            {a: strat_alloc[a].allocate() for a in self.assets},
            index=self.strategy_names).T
        return EngineResult(portfolio, windows, stats, final_aw, final_sw)
