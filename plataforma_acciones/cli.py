"""Interfaz de línea de comandos de la Plataforma acciones.

Uso:
    python -m plataforma_acciones backtest [--seed 42] [--vol 0.15] [--optimize]
    python -m plataforma_acciones robustness [--seeds 12]
    python -m plataforma_acciones regime [--seed 42]

Todos los comandos operan por defecto sobre datos sintéticos reproducibles.
Pasa ``--real SYM1,SYM2,...`` para intentar datos reales vía yfinance.
"""
from __future__ import annotations

import argparse

import numpy as np

from . import data, engine, learning, metrics


def _load(args):
    symbols = args.real.split(",") if getattr(args, "real", None) else None
    return data.load_prices(
        symbols=symbols, period_days=args.days,
        use_real=bool(symbols), seed=args.seed,
    )


def cmd_backtest(args):
    prices = _load(args)
    cfg = engine.EngineConfig(
        optimize=args.optimize,
        portfolio_target_vol=args.vol,
        verbose=args.verbose,
    )
    res = engine.WalkForwardEngine(prices, cfg).run()
    print("\n=== CARTERA OUT-OF-SAMPLE (walk-forward) ===")
    print(metrics.format_summary(res.stats))
    print("\nPesos finales por activo (top 5):")
    print(res.final_asset_weights.sort_values(ascending=False).head(5).round(3).to_string())
    print("\nPeso medio aprendido por estrategia:")
    print(res.final_strategy_weights.mean().sort_values(ascending=False).round(3).to_string())
    print("\nRecuerda: rendimiento sobre datos simulados, NO es una garantía. "
          "Ejecuta 'robustness' para ver la variabilidad entre escenarios.")


def cmd_robustness(args):
    seeds = list(range(1, args.seeds + 1))
    cagrs, sharpes, dds = [], [], []
    print(f"Evaluando {len(seeds)} escenarios de mercado independientes...\n")
    for s in seeds:
        prices = data.load_prices(period_days=args.days, seed=s)
        cfg = engine.EngineConfig(optimize=args.optimize, portfolio_target_vol=args.vol)
        st = engine.WalkForwardEngine(prices, cfg).run().stats
        cagrs.append(st["cagr"]); sharpes.append(st["sharpe"]); dds.append(st["max_drawdown"])
        print(f"  escenario {s:3d} | CAGR {st['cagr']:7.2%} | Sharpe {st['sharpe']:5.2f} "
              f"| mdd {st['max_drawdown']:7.2%}")
    print("\n=== RESUMEN ENTRE ESCENARIOS (la métrica honesta) ===")
    print(f"  CAGR medio    : {np.mean(cagrs):7.2%}")
    print(f"  CAGR mediana  : {np.median(cagrs):7.2%}")
    print(f"  CAGR min/max  : {np.min(cagrs):7.2%} / {np.max(cagrs):7.2%}")
    print(f"  Sharpe medio  : {np.mean(sharpes):7.2f}")
    print(f"  mdd medio     : {np.mean(dds):7.2%}")
    print(f"  Escenarios >=15%   : {sum(c >= 0.15 for c in cagrs)}/{len(seeds)}")
    print(f"  Escenarios positivos: {sum(c > 0 for c in cagrs)}/{len(seeds)}")
    print("\nLectura honesta: el 15% se alcanza en escenarios favorables, pero "
          "NO de forma garantizada. La esperanza realista es muy inferior.")


def cmd_regime(args):
    prices = _load(args)
    idx = (prices / prices.iloc[0]).mean(axis=1)
    clf = learning.RegimeClassifier().fit(idx)
    labels = clf.predict(idx)
    fwd = idx.pct_change().shift(-1)
    print("=== Régimen de mercado detectado (clustering no supervisado) ===")
    for r in sorted(labels.unique()):
        mask = labels == r
        print(f"  Régimen {r}: {mask.sum():4d} periodos | retorno diario medio "
              f"{fwd[mask].mean():+.4%} | vol {idx.pct_change()[mask].std():.4%}")
    print(f"\nRégimen actual (último periodo): {int(labels.iloc[-1])}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="plataforma_acciones",
                                description="Plataforma de trading algorítmico con auto-aprendizaje.")
    sub = p.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--seed", type=int, default=42)
    common.add_argument("--days", type=int, default=252 * 6)
    common.add_argument("--vol", type=float, default=0.15, help="vol anual objetivo de cartera")
    common.add_argument("--optimize", action="store_true",
                        help="afinar params por ventana (tiende a sobreajustar)")
    common.add_argument("--real", type=str, default=None,
                        help="símbolos reales separados por coma (vía yfinance)")
    common.add_argument("--verbose", action="store_true")

    sp = sub.add_parser("backtest", parents=[common], help="backtest walk-forward")
    sp.set_defaults(func=cmd_backtest)
    sp = sub.add_parser("robustness", parents=[common], help="evaluación multi-escenario")
    sp.add_argument("--seeds", type=int, default=12)
    sp.set_defaults(func=cmd_robustness)
    sp = sub.add_parser("regime", parents=[common], help="diagnóstico de régimen de mercado")
    sp.set_defaults(func=cmd_regime)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
