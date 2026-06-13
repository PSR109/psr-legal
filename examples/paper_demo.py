"""Demo de paper trading: opera con dinero ficticio y guarda resultados.

    python examples/paper_demo.py

Genera:
  * examples/paper_equity.png  — curva de patrimonio de la cuenta ficticia
  * examples/paper_trades.csv  — registro de todas las operaciones
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from plataforma_acciones import data, metrics, paper

HERE = os.path.dirname(__file__)


def main(seed=42):
    prices = data.load_prices(period_days=252 * 6, seed=seed)
    cfg = paper.PaperConfig(initial_cash=100_000, target_vol=0.15, max_leverage=1.5)
    res = paper.PaperTrader(prices, cfg).run(verbose=True)
    eq = res.equity_curve

    print("\n=== CUENTA DE PAPER TRADING (dinero ficticio) ===")
    print(f"  Capital inicial : {cfg.initial_cash:14,.2f}")
    print(f"  Patrimonio final: {eq.iloc[-1]:14,.2f}")
    print(f"  Operaciones      : {len(res.trades):14,d}")
    print(f"  Costes pagados  : {res.total_costs:14,.2f}")
    print(metrics.format_summary(res.stats))

    # Curva de patrimonio.
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(eq.index, eq.values, linewidth=2, color="#0066cc",
            label=f"Cuenta ficticia (CAGR {res.stats['cagr']:.1%}, "
                  f"max DD {res.stats['max_drawdown']:.1%})")
    ax.axhline(cfg.initial_cash, color="gray", linestyle="--", alpha=0.6,
               label="Capital inicial")
    ax.set_title(f"Paper trading — patrimonio de la cuenta ficticia (seed={seed})")
    ax.set_ylabel("Patrimonio (€)")
    ax.legend(); ax.grid(True, alpha=0.3)
    fig.tight_layout()
    eq_path = os.path.join(HERE, "paper_equity.png")
    fig.savefig(eq_path, dpi=120)
    print(f"\nGráfico guardado en {eq_path}")

    # Registro de operaciones.
    csv_path = os.path.join(HERE, "paper_trades.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["fecha", "activo", "unidades", "precio", "coste"])
        for t in res.trades:
            w.writerow([t.date.date(), t.asset, f"{t.units:.4f}",
                        f"{t.price:.4f}", f"{t.cost:.4f}"])
    print(f"Registro de {len(res.trades)} operaciones en {csv_path}")


if __name__ == "__main__":
    main()
