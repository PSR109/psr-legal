"""Componentes de aprendizaje automático y auto-mejora.

Tres piezas trabajan juntas para que la plataforma "aprenda por sí sola":

1. ``optimize_strategy`` — búsqueda adaptativa (random search + hill climbing)
   de los parámetros de una estrategia que maximizan un objetivo ajustado por
   riesgo orientado a la meta del 15% anual. Se entrena SOLO con datos pasados
   (in-sample).

2. ``RegimeClassifier`` — modelo no supervisado (KMeans sobre características de
   mercado) que identifica el régimen actual (tendencia/volatilidad). Permite
   que el sistema elija estrategias distintas según el contexto.

3. ``HedgeAllocator`` — asignador online basado en el algoritmo de pesos
   multiplicativos (Hedge). Tras cada periodo de evaluación reparte más capital
   a las estrategias/activos que mejor rinden y menos a los que fallan; así el
   conjunto "mejora con el tiempo" sin intervención manual.

Filosofía anti-overfitting: la optimización se hace in-sample, pero el juicio
final SIEMPRE es out-of-sample (walk-forward). Es la única forma honesta de
estimar si una mejora es real o es ruido.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from . import backtest, metrics
from .strategies import STRATEGY_REGISTRY, Strategy


# --------------------------------------------------------------------------- #
# Función objetivo orientada al 15% anual                                      #
# --------------------------------------------------------------------------- #
def risk_adjusted_objective(result: backtest.BacktestResult,
                            target_cagr: float = 0.15) -> float:
    """Puntuación a maximizar.

    Combina rentabilidad ajustada por riesgo (Sortino) con la cercanía al
    objetivo de CAGR y una penalización fuerte por caídas profundas. No premia
    superar el objetivo de forma desbocada (eso suele implicar riesgo
    excesivo); premia *alcanzarlo* de forma estable.
    """
    s = result.stats
    cagr = s["cagr"]
    sortino = s["sortino"]
    mdd = abs(s["max_drawdown"])

    # Cercanía al objetivo: máxima cuando cagr == target; cae si te quedas
    # corto y se aplana (sin premio extra) cuando lo superas.
    if cagr >= target_cagr:
        proximity = 1.0
    else:
        proximity = max(0.0, cagr / target_cagr)

    drawdown_penalty = 2.5 * max(0.0, mdd - 0.20)  # tolera hasta ~20% de caída
    return float(proximity * 1.5 + 0.5 * np.tanh(sortino) - drawdown_penalty)


# --------------------------------------------------------------------------- #
# Optimizador de parámetros (random search + hill climbing)                    #
# --------------------------------------------------------------------------- #
def _sample_params(space: dict, rng: np.random.Generator) -> dict:
    params = {}
    for name, (low, high, is_int) in space.items():
        if is_int:
            params[name] = int(rng.integers(int(low), int(high) + 1))
        else:
            params[name] = float(rng.uniform(low, high))
    return params


def _mutate_params(params: dict, space: dict, rng: np.random.Generator,
                   scale: float = 0.2) -> dict:
    out = dict(params)
    for name, (low, high, is_int) in space.items():
        span = high - low
        step = rng.normal(0.0, scale * span)
        val = out[name] + step
        val = min(max(val, low), high)
        out[name] = int(round(val)) if is_int else float(val)
    return out


@dataclass
class OptimizationResult:
    strategy_name: str
    params: dict
    score: float
    train_stats: dict


def _score_candidate(cls, params, train, valid, cfg, target_cagr):
    """Optimiza en ``train`` pero PUNTÚA en ``valid`` (anti-overfitting).

    Si no hay validación, puntúa en el propio train. Cuando hay validación, la
    señal se calcula sobre la serie completa (train+valid) para dar contexto a
    los indicadores y se evalúa solo el tramo de validación.
    """
    strat = cls(**params)
    if valid is None:
        res = backtest.run_strategy(train, strat, cfg)
        return risk_adjusted_objective(res, target_cagr), res.stats
    train = train.copy(); train.attrs = {}
    valid = valid.copy(); valid.attrs = {}
    full = pd.concat([train, valid])
    res_full = backtest.run_strategy(full, strat, cfg)
    valid_ret = res_full.returns.loc[valid.index]
    vres = backtest.BacktestResult(valid_ret, res_full.positions.loc[valid.index],
                                   metrics.summary(valid_ret, cfg.periods_per_year if cfg else 252))
    return risk_adjusted_objective(vres, target_cagr), vres.stats


def optimize_strategy(prices: pd.Series, strategy_name: str,
                      cfg: backtest.BacktestConfig | None = None,
                      target_cagr: float = 0.15,
                      n_random: int = 25, n_refine: int = 12,
                      valid_frac: float = 0.3,
                      seed: int | None = 0) -> OptimizationResult:
    """Busca los mejores parámetros de una estrategia.

    Usa una división interna train/validación: explora parámetros entrenando en
    el tramo inicial y selecciona por su rendimiento en el tramo de validación
    (datos no usados para ajustar). Esto reduce drásticamente el sobreajuste y
    mejora el rendimiento real fuera de muestra.
    """
    rng = np.random.default_rng(seed)
    cls = STRATEGY_REGISTRY[strategy_name]
    space = cls.param_space

    if valid_frac and len(prices) > 60:
        split = int(len(prices) * (1 - valid_frac))
        train, valid = prices.iloc[:split], prices.iloc[split:]
    else:
        train, valid = prices, None

    best_params, best_score, best_stats = None, -np.inf, None

    # Fase 1: exploración aleatoria.
    for _ in range(n_random):
        params = _sample_params(space, rng)
        score, stats = _score_candidate(cls, params, train, valid, cfg, target_cagr)
        if score > best_score:
            best_params, best_score, best_stats = params, score, stats

    # Fase 2: refinamiento local (hill climbing) en torno al mejor candidato.
    for _ in range(n_refine):
        params = _mutate_params(best_params, space, rng)
        score, stats = _score_candidate(cls, params, train, valid, cfg, target_cagr)
        if score > best_score:
            best_params, best_score, best_stats = params, score, stats

    return OptimizationResult(strategy_name, best_params, best_score, best_stats)


def optimize_each_strategy(prices: pd.Series,
                           cfg: backtest.BacktestConfig | None = None,
                           target_cagr: float = 0.15,
                           seed: int | None = 0) -> dict[str, OptimizationResult]:
    """Optimiza CADA estrategia del registro y devuelve todas afinadas.

    Devuelve un menú {nombre: resultado} para que el aprendizaje online decida
    online cuánto peso dar a cada una; no descarta ninguna a priori.
    """
    out = {}
    for i, name in enumerate(STRATEGY_REGISTRY):
        out[name] = optimize_strategy(prices, name, cfg, target_cagr, seed=seed + i)
    return out


def select_best_strategy(prices: pd.Series,
                         cfg: backtest.BacktestConfig | None = None,
                         target_cagr: float = 0.15,
                         seed: int | None = 0) -> OptimizationResult:
    """Optimiza TODAS las estrategias del registro y devuelve la mejor."""
    results = optimize_each_strategy(prices, cfg, target_cagr, seed)
    return max(results.values(), key=lambda r: r.score)


# --------------------------------------------------------------------------- #
# Clasificador de régimen de mercado                                           #
# --------------------------------------------------------------------------- #
@dataclass
class RegimeClassifier:
    """Agrupa el mercado en ``n_regimes`` estados según tendencia y volatilidad."""

    n_regimes: int = 3
    window: int = 20
    _model: KMeans | None = field(default=None, init=False)
    _scaler: StandardScaler | None = field(default=None, init=False)

    def _features(self, prices: pd.Series) -> pd.DataFrame:
        rets = prices.pct_change().fillna(0.0)
        feat = pd.DataFrame({
            "trend": prices.pct_change(self.window).fillna(0.0),
            "vol": rets.rolling(self.window, min_periods=1).std(ddof=0).fillna(0.0),
            "skew": rets.rolling(self.window, min_periods=2).skew().fillna(0.0),
        })
        return feat

    def fit(self, prices: pd.Series) -> "RegimeClassifier":
        feat = self._features(prices)
        self._scaler = StandardScaler().fit(feat)
        self._model = KMeans(n_clusters=self.n_regimes, n_init=5, random_state=0)
        self._model.fit(self._scaler.transform(feat))
        return self

    def predict(self, prices: pd.Series) -> pd.Series:
        if self._model is None:
            raise RuntimeError("Llama a fit() antes de predict().")
        feat = self._features(prices)
        labels = self._model.predict(self._scaler.transform(feat))
        return pd.Series(labels, index=prices.index)


# --------------------------------------------------------------------------- #
# Asignador online de pesos (algoritmo Hedge / pesos multiplicativos)          #
# --------------------------------------------------------------------------- #
@dataclass
class HedgeAllocator:
    """Reparte capital entre N estrategias y aprende de su rendimiento.

    Implementa el algoritmo de pesos multiplicativos: tras observar el retorno
    de cada experto (estrategia/activo) en un periodo, multiplica su peso por
    ``exp(eta * retorno)`` y renormaliza. Con el tiempo concentra capital en los
    que rinden mejor, garantizando un arrepentimiento (regret) acotado frente al
    mejor experto en retrospectiva.
    """

    n_experts: int
    eta: float = 8.0          # tasa de aprendizaje
    decay: float = 0.99       # olvido gradual del pasado (no estacionariedad)
    weights: np.ndarray = field(default=None)

    def __post_init__(self):
        if self.weights is None:
            self.weights = np.ones(self.n_experts) / self.n_experts

    def allocate(self) -> np.ndarray:
        return self.weights / self.weights.sum()

    def update(self, expert_returns: np.ndarray) -> np.ndarray:
        """Actualiza los pesos tras observar el retorno de cada experto."""
        r = np.nan_to_num(np.asarray(expert_returns, dtype=float))
        self.weights = (self.weights ** self.decay) * np.exp(self.eta * r)
        # Suelo de peso para no descartar permanentemente a ningún experto.
        floor = 0.01 / self.n_experts
        self.weights = np.maximum(self.weights, floor)
        self.weights /= self.weights.sum()
        return self.allocate()
