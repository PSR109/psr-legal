import numpy as np
import pandas as pd

from plataforma_acciones import backtest, data
from plataforma_acciones.strategies import MovingAverageCross


def test_no_lookahead_position_is_shifted():
    prices = data.load_prices(period_days=300, seed=5)["SPY_ETF"]
    pos = pd.Series(1.0, index=prices.index)  # siempre largo
    res = backtest.run(prices, pos, backtest.BacktestConfig(target_volatility=None,
                                                            cost_per_trade=0, slippage=0))
    # El primer retorno debe ser 0 porque la posición se aplica con un periodo de retardo.
    assert res.returns.iloc[0] == 0.0


def test_costs_reduce_returns():
    prices = data.load_prices(period_days=300, seed=5)["SPY_ETF"]
    strat = MovingAverageCross(fast=10, slow=30, allow_short=1)
    sig = strat.generate_signal(prices)
    no_cost = backtest.run(prices, sig, backtest.BacktestConfig(cost_per_trade=0, slippage=0,
                                                                target_volatility=None))
    with_cost = backtest.run(prices, sig, backtest.BacktestConfig(cost_per_trade=0.01, slippage=0.01,
                                                                  target_volatility=None))
    assert with_cost.returns.sum() < no_cost.returns.sum()


def test_buy_and_hold_matches_asset_return():
    prices = data.load_prices(period_days=300, seed=8)["GOLD_FUT"]
    pos = pd.Series(1.0, index=prices.index)
    res = backtest.run(prices, pos, backtest.BacktestConfig(target_volatility=None,
                                                            cost_per_trade=0, slippage=0))
    asset_ret = prices.pct_change().fillna(0.0)
    # Comprar y mantener (sin costes, sin escalado) replica el retorno del activo,
    # salvo el primer periodo por el retardo de la posición.
    assert np.allclose(res.returns.iloc[1:].to_numpy(), asset_ret.iloc[1:].to_numpy())


def test_vol_targeting_controls_volatility():
    prices = data.load_prices(period_days=800, seed=2)["NVDA"]
    pos = pd.Series(1.0, index=prices.index)
    res = backtest.run(prices, pos, backtest.BacktestConfig(target_volatility=0.15, max_leverage=3))
    realized = res.returns.std(ddof=1) * np.sqrt(252)
    # El escalado por volatilidad debe acercar la vol realizada al objetivo
    # mucho más que la vol cruda del activo (~0.45 anual para NVDA).
    assert realized < 0.30
