import numpy as np

from plataforma_acciones import data, engine, metrics


def test_engine_runs_and_produces_oos_curve():
    prices = data.load_prices(period_days=252 * 4, seed=42)
    # n_workers=1 para evitar overhead de procesos en el test.
    cfg = engine.EngineConfig(optimize=False, n_workers=1, train_periods=252,
                              test_periods=63)
    res = engine.WalkForwardEngine(prices, cfg).run()
    assert len(res.portfolio_returns) > 0
    assert abs(res.final_asset_weights.sum() - 1.0) < 1e-9
    # Los pesos de estrategia por activo forman un símplex por fila.
    row_sums = res.final_strategy_weights.sum(axis=1)
    assert np.allclose(row_sums.to_numpy(), 1.0)


def test_engine_stats_are_finite():
    prices = data.load_prices(period_days=252 * 4, seed=7)
    cfg = engine.EngineConfig(optimize=False, n_workers=1)
    res = engine.WalkForwardEngine(prices, cfg).run()
    for v in res.stats.values():
        assert np.isfinite(v)


def test_vol_target_keeps_portfolio_near_target():
    prices = data.load_prices(period_days=252 * 4, seed=11)
    cfg = engine.EngineConfig(optimize=False, n_workers=1, portfolio_target_vol=0.15)
    res = engine.WalkForwardEngine(prices, cfg).run()
    vol = metrics.annual_volatility(res.portfolio_returns)
    # No exigimos exactitud, solo que el control de riesgo mantenga la vol acotada.
    assert 0.05 < vol < 0.30
