import numpy as np

from plataforma_acciones import data, paper


def test_broker_buy_updates_cash_and_position():
    import pandas as pd
    prices = pd.Series({"A": 10.0, "B": 20.0})
    broker = paper.PaperBroker(cash=1000.0, cost_per_trade=0.0, slippage=0.0)
    broker.rebalance("2020-01-01", prices, {"A": 0.5, "B": 0.0})
    # 50% de 1000 = 500 en A a 10 -> 50 unidades; caja baja a 500.
    assert abs(broker.positions["A"] - 50.0) < 1e-9
    assert abs(broker.cash - 500.0) < 1e-9
    assert abs(broker.equity(prices) - 1000.0) < 1e-9


def test_broker_costs_reduce_equity():
    import pandas as pd
    prices = pd.Series({"A": 10.0})
    free = paper.PaperBroker(cash=1000.0, cost_per_trade=0.0, slippage=0.0)
    paid = paper.PaperBroker(cash=1000.0, cost_per_trade=0.01, slippage=0.01)
    free.rebalance("d", prices, {"A": 1.0})
    paid.rebalance("d", prices, {"A": 1.0})
    assert paid.equity(prices) < free.equity(prices)


def test_paper_trader_runs_and_conserves_accounting():
    prices = data.load_prices(period_days=252 * 3, seed=42)
    cfg = paper.PaperConfig(initial_cash=100_000, warmup_periods=252)
    res = paper.PaperTrader(prices, cfg).run()
    assert len(res.equity_curve) > 0
    assert np.isfinite(res.equity_curve.iloc[-1])
    # El patrimonio nunca debe ser NaN ni negativo de forma espuria.
    assert (res.equity_curve > 0).all()
    # Debe haberse ejecutado algún rebalanceo.
    assert len(res.trades) > 0
    assert res.total_costs >= 0


def test_paper_no_lookahead_equity_is_causal():
    # Cambiar precios despues del final no debe alterar la curva ya simulada.
    prices = data.load_prices(period_days=252 * 3, seed=7)
    cfg = paper.PaperConfig(initial_cash=100_000, warmup_periods=252)
    res1 = paper.PaperTrader(prices, cfg).run()
    perturbed = prices.copy()
    perturbed.iloc[-1] *= 1.2  # solo el último día
    res2 = paper.PaperTrader(perturbed, cfg).run()
    # Las curvas deben coincidir salvo, como mucho, el último punto.
    a = res1.equity_curve.iloc[:-1].to_numpy()
    b = res2.equity_curve.iloc[:-1].to_numpy()
    assert np.allclose(a, b)
