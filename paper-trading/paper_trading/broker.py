"""Simulated broker.

Holds cash and positions and fills market orders with commission and
slippage. No real money and no real venue are involved — every fill is
book-keeping inside this process.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Trade:
    t: int
    symbol: str
    qty: float
    price: float
    commission: float


class PaperBroker:
    def __init__(self, cash: float = 100_000.0,
                 commission_bps: float = 1.0, slippage_bps: float = 2.0):
        self.starting_cash = cash
        self.cash = cash
        self.positions: dict[str, float] = {}
        self.trades: list[Trade] = []
        self.commission_rate = commission_bps / 10_000.0
        self.slippage_rate = slippage_bps / 10_000.0

    def position(self, symbol: str) -> float:
        return self.positions.get(symbol, 0.0)

    def market_order(self, t: int, symbol: str, qty: float, ref_price: float):
        """Fill ``qty`` units (positive = buy, negative = sell/short)."""
        if abs(qty) < 1e-12:
            return
        # Slippage: pay up when buying, receive less when selling.
        if qty > 0:
            fill = ref_price * (1 + self.slippage_rate)
        else:
            fill = ref_price * (1 - self.slippage_rate)
        commission = abs(qty) * fill * self.commission_rate
        self.cash -= qty * fill        # buy reduces cash; sell (qty<0) adds
        self.cash -= commission
        self.positions[symbol] = self.position(symbol) + qty
        self.trades.append(Trade(t, symbol, qty, fill, commission))

    def positions_value(self, prices: dict) -> float:
        return sum(q * prices[s] for s, q in self.positions.items())

    def equity(self, prices: dict) -> float:
        return self.cash + self.positions_value(prices)
