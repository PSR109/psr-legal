"""Simulation engine.

Orchestrates the data feed, the ensemble of strategy agents, the risk
manager and the paper broker over time, and records the equity curve.
"""
from __future__ import annotations


class PortfolioCoordinator:
    """Blends an ensemble of agents into one target weight per symbol."""

    def __init__(self, agents):
        self.agents = agents

    def blended_weights(self, market) -> dict:
        agg: dict[str, float] = {}
        for agent in self.agents:
            for symbol, weight in agent.target_weights(market).items():
                agg[symbol] = agg.get(symbol, 0.0) + weight
        n = len(self.agents)
        return {s: v / n for s, v in agg.items()} if n else {}


class SimulationEngine:
    def __init__(self, market, broker, coordinator, risk,
                 warmup: int = 60, rebalance_every: int = 5):
        self.market = market
        self.broker = broker
        self.coordinator = coordinator
        self.risk = risk
        self.warmup = warmup
        self.rebalance_every = rebalance_every
        self.equity_curve: list[float] = []
        self.peak = broker.starting_cash

    def _rebalance(self):
        prices = self.market.prices()
        equity = self.broker.equity(prices)
        self.peak = max(self.peak, equity)
        drawdown = 0.0 if self.peak <= 0 else 1 - equity / self.peak
        weights = self.coordinator.blended_weights(self.market)
        target = self.risk.constrain(weights, drawdown)
        for symbol in self.market.symbols:
            price = prices[symbol]
            target_qty = target.get(symbol, 0.0) * equity / price
            delta = target_qty - self.broker.position(symbol)
            self.broker.market_order(self.market.t, symbol, delta, price)

    def run(self, days: int):
        for _ in range(days):
            self.market.step()
            if self.market.t >= self.warmup and self.market.t % self.rebalance_every == 0:
                self._rebalance()
            self.equity_curve.append(self.broker.equity(self.market.prices()))
        return self.equity_curve
