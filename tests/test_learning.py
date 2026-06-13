import numpy as np
import pandas as pd

from plataforma_acciones import data, learning


def test_hedge_concentrates_on_winner():
    alloc = learning.HedgeAllocator(n_experts=3, eta=10.0, decay=1.0)
    # El experto 1 gana siempre; el resto pierde.
    for _ in range(200):
        alloc.update(np.array([-0.01, 0.02, -0.01]))
    w = alloc.allocate()
    assert w[1] > 0.8
    assert np.argmax(w) == 1


def test_hedge_weights_are_simplex():
    alloc = learning.HedgeAllocator(n_experts=4)
    alloc.update(np.array([0.01, -0.02, 0.0, 0.03]))
    w = alloc.allocate()
    assert abs(w.sum() - 1.0) < 1e-9
    assert (w >= 0).all()


def test_optimize_strategy_returns_valid_params():
    prices = data.load_prices(period_days=600, seed=4)["QQQ_ETF"]
    res = learning.optimize_strategy(prices, "trend_following", n_random=8, n_refine=4)
    cls_space = learning.STRATEGY_REGISTRY["trend_following"].param_space
    for k, (low, high, _) in cls_space.items():
        assert low <= res.params[k] <= high
    assert np.isfinite(res.score)


def test_regime_classifier_fit_predict():
    prices = data.load_prices(period_days=600, seed=6)["SPY_ETF"]
    clf = learning.RegimeClassifier(n_regimes=3).fit(prices)
    labels = clf.predict(prices)
    assert len(labels) == len(prices)
    assert set(labels.unique()).issubset({0, 1, 2})


def test_objective_prefers_target_over_shortfall():
    # Una estrategia que alcanza el objetivo debe puntuar más que una a medias,
    # manteniendo el riesgo comparable.
    from plataforma_acciones import backtest, metrics

    idx = pd.date_range("2020-01-01", periods=252)
    good = pd.Series(np.full(252, 0.15 / 252 + 0.0001), index=idx)
    weak = pd.Series(np.full(252, 0.03 / 252 + 0.0001), index=idx)
    rg = backtest.BacktestResult(good, good * 0, metrics.summary(good))
    rw = backtest.BacktestResult(weak, weak * 0, metrics.summary(weak))
    assert learning.risk_adjusted_objective(rg, 0.15) > learning.risk_adjusted_objective(rw, 0.15)
