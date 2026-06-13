"""Demo de extremo a extremo: ejecuta el motor y guarda la curva de capital.

    python examples/run_demo.py

Genera ``examples/equity_curve.png`` con la curva de capital out-of-sample y
una comparación frente a comprar-y-mantener equiponderado.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from plataforma_acciones import data, engine, metrics


def main():
    prices = data.load_prices(period_days=252 * 6, seed=42)
    cfg = engine.EngineConfig(optimize=False, portfolio_target_vol=0.15, verbose=True)
    res = engine.WalkForwardEngine(prices, cfg).run()

    print("\n=== CARTERA OUT-OF-SAMPLE (seed=42) ===")
    print(metrics.format_summary(res.stats))

    # Línea base: comprar y mantener equiponderado, alineado al tramo OOS.
    bench = prices.pct_change().fillna(0.0).mean(axis=1).reindex(res.portfolio_returns.index)
    eq_strategy = metrics.equity_curve(res.portfolio_returns, 10_000)
    eq_bench = metrics.equity_curve(bench, 10_000)

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(eq_strategy.index, eq_strategy.values,
            label=f"Plataforma (CAGR {res.stats['cagr']:.1%}, Sharpe {res.stats['sharpe']:.2f})",
            linewidth=2)
    ax.plot(eq_bench.index, eq_bench.values,
            label=f"Comprar y mantener (CAGR {metrics.cagr(bench):.1%})",
            linewidth=1.5, alpha=0.7)
    ax.set_title("Plataforma acciones — capital out-of-sample (10.000 € iniciales, seed=42)")
    ax.set_ylabel("Valor de la cartera (€)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    out = os.path.join(os.path.dirname(__file__), "equity_curve.png")
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    print(f"\nGráfico guardado en {out}")


if __name__ == "__main__":
    main()
