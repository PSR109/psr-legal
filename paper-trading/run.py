#!/usr/bin/env python3
"""Multi-agent paper-trading simulator — entrypoint.

Runs a strategy ensemble (momentum + mean-reversion) over a synthetic
multi-asset market (stocks, ETFs, crypto, FX) and prints an honest
performance report against an equal-weight buy & hold benchmark.

This is a SIMULATION for research and education only. It uses no real money,
sends no real orders, and does NOT guarantee any rate of return. Nothing here
is financial advice.

Usage:
    python3 run.py                 # default 3-year run
    python3 run.py --days 1260     # 5 years
    python3 run.py --seed 7
"""
from __future__ import annotations

import argparse

from paper_trading.agents import MeanReversionAgent, MomentumAgent, RiskManager
from paper_trading.broker import PaperBroker
from paper_trading.engine import PortfolioCoordinator, SimulationEngine
from paper_trading.market import (
    GBMProcess,
    Instrument,
    MomentumGBMProcess,
    OUProcess,
    SyntheticMarket,
)
from paper_trading.metrics import summarize

_DISCLAIMER = (
    "DESCARGO: Esto es una SIMULACION educativa. No usa dinero real, no envia\n"
    "ordenes reales y NO garantiza ninguna rentabilidad. El rendimiento pasado\n"
    "o simulado no predice resultados futuros. Esto no es asesoria financiera."
)


def build_universe():
    """A diversified basket across asset classes. Drifts/vols are the *true*
    parameters of the simulated world and are unknown to the agents."""
    return [
        Instrument("SPY", "etf", 450.0, GBMProcess(mu=0.07, sigma=0.15)),
        Instrument("GLD", "etf", 190.0, GBMProcess(mu=0.04, sigma=0.13)),
        Instrument("AAPL", "stock", 190.0, MomentumGBMProcess(base_sigma=0.28)),
        Instrument("NVDA", "stock", 120.0, MomentumGBMProcess(base_sigma=0.45)),
        Instrument("BTC", "crypto", 42000.0, MomentumGBMProcess(base_sigma=0.70)),
        Instrument("ETH", "crypto", 2300.0, MomentumGBMProcess(base_sigma=0.80)),
        Instrument("EURUSD", "fx", 1.09, OUProcess(sigma=0.08)),
        Instrument("USDJPY", "fx", 150.0, OUProcess(sigma=0.10)),
    ]


def run_strategy(args):
    market = SyntheticMarket(build_universe(), seed=args.seed)
    broker = PaperBroker(cash=args.cash, commission_bps=args.commission_bps,
                         slippage_bps=args.slippage_bps)
    agents = [MomentumAgent(lookback=50), MeanReversionAgent(lookback=20)]
    coordinator = PortfolioCoordinator(agents)
    risk = RiskManager(max_gross=1.0, max_per_name=0.25, max_drawdown=0.20)
    engine = SimulationEngine(market, broker, coordinator, risk,
                              warmup=60, rebalance_every=args.rebalance_every)
    equity = engine.run(args.days)
    return summarize(equity), broker


def run_benchmark(args):
    """Equal-weight buy & hold on the same price paths (same seed)."""
    market = SyntheticMarket(build_universe(), seed=args.seed)
    broker = PaperBroker(cash=args.cash, commission_bps=args.commission_bps,
                         slippage_bps=args.slippage_bps)
    symbols = market.symbols
    curve = []
    bought = False
    for _ in range(args.days):
        market.step()
        if not bought:
            prices = market.prices()
            per_name_cash = broker.cash / len(symbols)
            for s in symbols:
                broker.market_order(market.t, s, per_name_cash / prices[s], prices[s])
            bought = True
        curve.append(broker.equity(market.prices()))
    return summarize(curve)


def _pct(x):
    return f"{x * 100:7.2f}%" if x == x else "    n/a"


def _fmt(x):
    return f"{x:6.2f}" if x == x else "  n/a"


def _print_stats(s):
    if not s:
        print("   (datos insuficientes)")
        return
    print(f"   Retorno total : {_pct(s['total_return'])}")
    print(f"   CAGR          : {_pct(s['cagr'])}")
    print(f"   Volatilidad   : {_pct(s['annual_vol'])}")
    print(f"   Sharpe        : {_fmt(s['sharpe'])}")
    print(f"   Max drawdown  : {_pct(s['max_drawdown'])}")
    print(f"   Equity final  : ${s['final_equity']:,.0f}")


def main():
    p = argparse.ArgumentParser(description="Multi-agent paper-trading simulator")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--days", type=int, default=252 * 3, help="trading days to simulate")
    p.add_argument("--cash", type=float, default=100_000.0)
    p.add_argument("--rebalance-every", type=int, default=5)
    p.add_argument("--commission-bps", type=float, default=1.0)
    p.add_argument("--slippage-bps", type=float, default=2.0)
    args = p.parse_args()

    stats, broker = run_strategy(args)
    bench = run_benchmark(args)

    bar = "=" * 60
    print(bar)
    print(" SIMULADOR DE PAPER-TRADING — REPORTE")
    print(bar)
    print(f" Semilla {args.seed} | {args.days} dias (~{args.days / 252:.1f} anios) "
          f"| capital ${args.cash:,.0f}")
    print(f" Rebalanceo c/{args.rebalance_every}d | comision "
          f"{args.commission_bps}bps | slippage {args.slippage_bps}bps")
    print("-" * 60)
    print(" Estrategia multi-agente (momentum + mean-reversion):")
    _print_stats(stats)
    print(f"   Operaciones   : {len(broker.trades)}")
    print("-" * 60)
    print(" Benchmark buy & hold (equiponderado):")
    _print_stats(bench)
    print(bar)
    print(_DISCLAIMER)


if __name__ == "__main__":
    main()
