"""Unit tests for the paper-trading simulator.

Run from the project root (paper-trading/):
    python3 -m unittest discover -s tests -v
"""
import math
import unittest

from paper_trading.agents import MomentumAgent, RiskManager, _normalize
from paper_trading.broker import PaperBroker
from paper_trading.engine import PortfolioCoordinator, SimulationEngine
from paper_trading.market import GBMProcess, Instrument, SyntheticMarket
from paper_trading.metrics import max_drawdown, summarize


def _build_market(seed=1):
    instruments = [
        Instrument("A", "stock", 100.0, GBMProcess(mu=0.10, sigma=0.20)),
        Instrument("B", "etf", 50.0, GBMProcess(mu=0.05, sigma=0.10)),
    ]
    return SyntheticMarket(instruments, seed=seed)


class BrokerTests(unittest.TestCase):
    def test_buy_then_sell_no_costs_restores_cash(self):
        b = PaperBroker(cash=10_000.0, commission_bps=0.0, slippage_bps=0.0)
        b.market_order(0, "A", 10, 100.0)
        self.assertAlmostEqual(b.cash, 9_000.0)
        self.assertAlmostEqual(b.position("A"), 10)
        b.market_order(1, "A", -10, 100.0)
        self.assertAlmostEqual(b.cash, 10_000.0)
        self.assertAlmostEqual(b.position("A"), 0.0)

    def test_costs_reduce_cash(self):
        b = PaperBroker(cash=10_000.0, commission_bps=10.0, slippage_bps=10.0)
        b.market_order(0, "A", 10, 100.0)
        # slippage pushes fill above 100, plus commission => spent > 1000
        self.assertLess(b.cash, 9_000.0)

    def test_equity_marks_to_market(self):
        b = PaperBroker(cash=10_000.0, commission_bps=0.0, slippage_bps=0.0)
        b.market_order(0, "A", 10, 100.0)
        self.assertAlmostEqual(b.equity({"A": 120.0}), 10_000.0 + 10 * 20.0)

    def test_short_position_accounting(self):
        b = PaperBroker(cash=10_000.0, commission_bps=0.0, slippage_bps=0.0)
        b.market_order(0, "A", -5, 100.0)
        self.assertAlmostEqual(b.cash, 10_500.0)
        self.assertAlmostEqual(b.equity({"A": 100.0}), 10_000.0)


class MarketTests(unittest.TestCase):
    def test_deterministic_with_seed(self):
        m1 = _build_market(seed=7)
        m2 = _build_market(seed=7)
        for _ in range(100):
            m1.step()
            m2.step()
        self.assertEqual(m1.prices(), m2.prices())

    def test_history_grows(self):
        m = _build_market()
        m.step()
        m.step()
        self.assertEqual(len(m.history["A"]), 3)  # initial + 2 steps


class AgentTests(unittest.TestCase):
    def test_normalize_gross_is_one(self):
        w = _normalize({"A": 3.0, "B": -1.0})
        self.assertAlmostEqual(sum(abs(v) for v in w.values()), 1.0)

    def test_normalize_empty(self):
        self.assertEqual(_normalize({"A": 0.0}), {})

    def test_momentum_caps_handled_when_short_history(self):
        m = _build_market()
        agent = MomentumAgent(lookback=50)
        self.assertEqual(agent.target_weights(m), {})  # not enough history yet

    def test_risk_manager_per_name_cap_and_gross(self):
        rm = RiskManager(max_gross=1.0, max_per_name=0.25, max_drawdown=0.50)
        out = rm.constrain({"A": 0.9, "B": 0.9}, drawdown=0.0)
        self.assertLessEqual(max(abs(v) for v in out.values()), 0.25 + 1e-9)
        self.assertLessEqual(sum(abs(v) for v in out.values()), 1.0 + 1e-9)

    def test_risk_manager_drawdown_killswitch(self):
        rm = RiskManager(max_drawdown=0.20)
        self.assertEqual(rm.constrain({"A": 0.5}, drawdown=0.25), {})


class MetricsTests(unittest.TestCase):
    def test_flat_curve_zero_return(self):
        s = summarize([100.0] * 253)
        self.assertAlmostEqual(s["total_return"], 0.0)
        self.assertAlmostEqual(s["max_drawdown"], 0.0)

    def test_max_drawdown_value(self):
        self.assertAlmostEqual(max_drawdown([100, 120, 60, 90]), 0.5)

    def test_doubling_in_one_year(self):
        s = summarize([100.0] + [200.0] * 251, periods_per_year=252)
        self.assertGreater(s["cagr"], 0.5)


class EngineTests(unittest.TestCase):
    def test_run_is_deterministic_and_produces_metrics(self):
        def run_once():
            market = _build_market(seed=11)
            broker = PaperBroker(cash=100_000.0)
            coord = PortfolioCoordinator([MomentumAgent(lookback=10)])
            risk = RiskManager()
            eng = SimulationEngine(market, broker, coord, risk,
                                   warmup=15, rebalance_every=5)
            return eng.run(200)

        c1 = run_once()
        c2 = run_once()
        self.assertEqual(len(c1), 200)
        self.assertEqual(c1[-1], c2[-1])
        self.assertTrue(all(math.isfinite(v) for v in c1))


if __name__ == "__main__":
    unittest.main()
