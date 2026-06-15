# Simulador de Paper-Trading (multi-agente)

Simulador de *paper trading* (operativa simulada, **sin dinero real**) que opera
varias clases de activo —acciones, ETFs, criptomonedas y divisas— combinando
varios agentes de estrategia, con gestión de riesgo y un broker simulado.

> ⚠️ **Descargo importante.** Esto es una **simulación educativa y de
> investigación**. No usa dinero real, no envía órdenes a ningún mercado y
> **no garantiza ninguna rentabilidad** (ni el 10-12% ni ninguna otra cifra).
> El rendimiento pasado o simulado **no predice** resultados futuros. Esto **no
> es asesoría financiera**. Ningún programa puede garantizar retornos en
> mercados reales: el riesgo es inherente.

## Por qué no hay "rentabilidad garantizada"

El objetivo de "garantizar 10-12% anual iterando hasta lograrlo" no es
alcanzable de forma honesta: ajustar parámetros sobre datos pasados hasta que
el número calce produce **sobreajuste (overfitting)**, y esas estrategias
suelen **fracasar en vivo**. Por eso este proyecto:

- mide y reporta el rendimiento de forma **honesta** (CAGR, volatilidad,
  Sharpe y **máximo drawdown**),
- compara siempre contra un **benchmark buy & hold**, y
- no contiene ningún bucle que "ajuste hasta alcanzar" una cifra objetivo.

## Arquitectura (multi-agente)

| Componente | Archivo | Rol |
|---|---|---|
| Feed de mercado | `paper_trading/market.py` | Genera precios sintéticos reproducibles (GBM, momentum por regímenes, OU mean-reverting). Interfaz lista para enchufar un feed real. |
| Agentes de estrategia | `paper_trading/agents.py` | `MomentumAgent`, `MeanReversionAgent` → emiten *pesos objetivo*. |
| Gestor de riesgo | `paper_trading/agents.py` | `RiskManager`: tope por activo, tope de exposición bruta y *kill-switch* por drawdown. |
| Coordinador | `paper_trading/engine.py` | `PortfolioCoordinator`: combina (ensemble) los agentes en una cartera. |
| Broker simulado | `paper_trading/broker.py` | `PaperBroker`: efectivo, posiciones, comisiones y slippage. |
| Motor | `paper_trading/engine.py` | `SimulationEngine`: orquesta el bucle temporal y registra la curva de equity. |
| Métricas | `paper_trading/metrics.py` | Resumen honesto del desempeño. |

No requiere red ni dependencias externas: **solo Python 3.11+ estándar**.

## Uso

```bash
cd paper-trading
python3 run.py                 # corrida por defecto (~3 años)
python3 run.py --days 1260     # ~5 años
python3 run.py --seed 7 --rebalance-every 10
```

Opciones: `--seed`, `--days`, `--cash`, `--rebalance-every`,
`--commission-bps`, `--slippage-bps`.

## Tests

```bash
cd paper-trading
python3 -m unittest discover -s tests -v
```

## Cómo conectar datos reales (opcional)

Implementá una clase con la misma interfaz que `SyntheticMarket` (método
`step()`, propiedad `prices()` e historial por símbolo en `history`) que lea de
tu fuente de datos, y pasala al `SimulationEngine`. El resto del sistema
—agentes, riesgo, broker, métricas— funciona sin cambios. Aun con datos reales,
sigue siendo paper trading: **nada garantiza rentabilidad**.
