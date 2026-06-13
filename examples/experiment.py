"""Banco de pruebas para iterar sobre la configuración del motor."""
import sys
import time

from plataforma_acciones import data, engine, metrics


def main(seed=42, target_vol=0.15):
    t = time.time()
    prices = data.load_prices(period_days=252 * 6, seed=seed)
    cfg = engine.EngineConfig(
        verbose=True,
        portfolio_target_vol=target_vol,
    )
    res = engine.WalkForwardEngine(prices, cfg).run()
    print("--- CARTERA OOS GLOBAL ---")
    print(metrics.format_summary(res.stats))
    print("Pesos finales por activo (top 5):")
    print(res.final_asset_weights.sort_values(ascending=False).head(5).round(3).to_string())
    print("Peso medio aprendido por estrategia:")
    print(res.final_strategy_weights.mean().sort_values(ascending=False).round(3).to_string())
    print(f"tiempo {time.time() - t:.1f}s")
    return res


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    main(seed=seed)
