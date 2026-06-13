import numpy as np
import pandas as pd
import pytest

from plataforma_acciones import data
from plataforma_acciones.strategies import STRATEGY_REGISTRY, build


@pytest.fixture
def prices():
    return data.load_prices(period_days=500, seed=3)["AAPL"]


@pytest.mark.parametrize("name", list(STRATEGY_REGISTRY))
def test_signal_shape_and_range(prices, name):
    strat = STRATEGY_REGISTRY[name]()
    sig = strat.generate_signal(prices)
    assert len(sig) == len(prices)
    assert sig.index.equals(prices.index)
    assert sig.abs().max() <= 1.0 + 1e-9
    assert not sig.isna().any()


@pytest.mark.parametrize("name", list(STRATEGY_REGISTRY))
def test_defaults_within_param_space(name):
    cls = STRATEGY_REGISTRY[name]
    defaults = cls.defaults()
    for k, (low, high, _) in cls.param_space.items():
        assert low <= defaults[k] <= high


def test_build_unknown_raises():
    with pytest.raises(KeyError):
        build("no_existe")


def test_no_lookahead_signal_only_depends_on_past(prices):
    # Cambiar un precio futuro no debe alterar la señal en periodos anteriores.
    strat = STRATEGY_REGISTRY["trend_following"]()
    base = strat.generate_signal(prices)
    perturbed = prices.copy()
    perturbed.iloc[-1] *= 1.5
    new = strat.generate_signal(perturbed)
    # Las señales hasta el penúltimo periodo deben coincidir.
    assert np.allclose(base.iloc[:-1].to_numpy(), new.iloc[:-1].to_numpy())
