# Plataforma acciones

Plataforma de **trading algorítmico cuantitativo con auto-aprendizaje**. Opera
de forma simulada sobre varias clases de activo (ETFs, acciones, cripto,
divisas y futuros), hace *backtesting* riguroso con costes y *slippage*, y
aprende online qué estrategias y activos funcionan mejor, adaptándose con el
tiempo. Su función objetivo apunta a una rentabilidad del **15 % anual ajustada
por riesgo**.

> ## ⚠️ Lee esto antes que nada (honestidad sobre el 15 %)
>
> **El 15 % anual es un OBJETIVO DE OPTIMIZACIÓN, no una rentabilidad
> garantizada.** Ningún software puede garantizar rentabilidades futuras en
> mercados reales; cualquiera que lo prometa miente.
>
> Esta plataforma alcanza y supera el 15 % **en escenarios de mercado
> favorables**, pero al evaluarla con honestidad sobre **muchos escenarios
> independientes**, su esperanza realista es **muy inferior** y pierde dinero en
> una fracción nada despreciable de ellos (ver
> [«La prueba honesta»](#la-prueba-honesta)).
>
> Es una herramienta de **investigación y educación cuantitativa**. **No es
> asesoramiento financiero.** No operes con dinero real basándote en estos
> resultados. Úsala bajo tu responsabilidad.

---

## Qué hace

1. **Datos multi-mercado.** Genera precios sintéticos realistas (movimiento
   browniano geométrico con cambios de régimen, tendencias, saltos y
   correlaciones) para un universo de 10 activos de 5 clases. Opcionalmente
   descarga datos reales vía `yfinance` (`--real SPY,QQQ,BTC-USD,...`); si no
   hay red, cae automáticamente a datos sintéticos.

2. **Librería de estrategias** (`strategies.py`): cruce de medias, reversión a
   la media, *momentum*, reversión por RSI, ruptura de Bollinger y seguimiento
   de tendencia. Todas parametrizables y sin sesgo de anticipación.

3. **Motor de backtest** (`backtest.py`): vectorizado, con desfase de señal
   (anti *look-ahead*), costes de transacción, *slippage* y control de
   volatilidad objetivo.

4. **Auto-aprendizaje** (`learning.py`, `engine.py`):
   - **Aprendizaje online de dos niveles** con el algoritmo de pesos
     multiplicativos (*Hedge*): nivel 1 aprende, por activo, qué estrategia
     funciona en el régimen actual; nivel 2 reparte capital entre activos.
     Los pesos se conservan entre ventanas, así que el sistema **mejora con el
     tiempo**.
   - **Clasificador de régimen de mercado** (KMeans) para diagnóstico.
   - **Optimizador walk-forward** opcional de parámetros (ver nota sobre
     sobreajuste más abajo).

5. **Validación walk-forward**: todas las cifras de rendimiento se calculan
   **fuera de muestra** (out-of-sample). Es la única forma honesta de estimar
   el comportamiento sobre datos no vistos.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso rápido

```bash
# Backtest walk-forward sobre datos sintéticos (escenario seed=42, favorable)
python -m plataforma_acciones backtest --seed 42 --verbose

# La prueba honesta: evalúa muchos escenarios independientes
python -m plataforma_acciones robustness --seeds 12

# Diagnóstico del régimen de mercado actual
python -m plataforma_acciones regime --seed 42

# Demo de extremo a extremo con gráfico de la curva de capital
python examples/run_demo.py
```

Desde Python:

```python
from plataforma_acciones import data, engine, metrics

prices = data.load_prices(period_days=252 * 6, seed=42)
res = engine.WalkForwardEngine(prices, engine.EngineConfig()).run()
print(metrics.format_summary(res.stats))
```

## Resultados

### Escenario favorable (seed = 42)

| Métrica | Valor |
|---|---|
| CAGR (out-of-sample) | **17.95 %** |
| Volatilidad | 13.63 % |
| Sharpe | 1.28 |
| Sortino | 2.05 |
| Máxima caída | −18.59 % |
| Calmar | 0.97 |

![Curva de capital](examples/equity_curve.png)

### La prueba honesta

El mismo sistema, **misma configuración**, evaluado sobre 12 realizaciones de
mercado independientes:

| Métrica entre escenarios | Valor |
|---|---|
| CAGR medio | **3.22 %** |
| CAGR mediana | 3.26 % |
| CAGR mínimo / máximo | −7.75 % / 17.95 % |
| Sharpe medio | 0.26 |
| Escenarios que alcanzan ≥ 15 % | **2 / 12** |
| Escenarios con rentabilidad positiva | 7 / 12 |

**Conclusión:** el 17.95 % del seed 42 es un escenario afortunado, no una
habilidad reproducible. La esperanza realista del sistema ronda un CAGR de un
solo dígito con un Sharpe modesto, y puede perder dinero. Esto **no es un
defecto del código**: es la realidad de los mercados. Batir al mercado de forma
fiable es extraordinariamente difícil y **un 15 % garantizado no existe**.

Reproduce esta tabla tú mismo:

```bash
python -m plataforma_acciones robustness --seeds 12
```

## Sobre la optimización de parámetros (`--optimize`)

El sistema incluye un optimizador walk-forward, pero **está desactivado por
defecto** porque, sobre datos limitados, **sobreajusta**: afina parámetros que
brillan en el pasado y fallan en el futuro, empeorando el resultado real fuera
de muestra. El modo robusto por defecto usa parámetros sensatos fijos y deja que
el **aprendizaje online** decida los pesos: generaliza mucho mejor. Puedes
comparar ambos con `--optimize`.

## Arquitectura

```
plataforma_acciones/
├── data.py         # generación de datos (sintéticos + real opcional)
├── indicators.py   # indicadores técnicos vectorizados
├── strategies.py   # librería de estrategias
├── backtest.py     # motor de backtest con costes y control de riesgo
├── metrics.py      # CAGR, Sharpe, Sortino, drawdown, Calmar...
├── learning.py     # Hedge online, optimizador, clasificador de régimen
├── engine.py       # orquestador walk-forward de dos niveles
└── cli.py          # interfaz de línea de comandos
tests/              # 34 tests (pytest)
examples/           # demo con gráfico
```

## Pruebas

```bash
pytest -q   # 34 tests
```

## Limitaciones y honestidad metodológica

- Por defecto opera sobre datos **sintéticos**: útiles para validar la
  ingeniería y la lógica de aprendizaje, pero **no son el mercado real**.
- Costes, *slippage* y liquidez reales pueden ser peores que los modelados.
- Resultados pasados (reales o simulados) **no predicen** resultados futuros.
- El objetivo del 15 % es una **meta de diseño**, no una promesa.

## Licencia

MIT. Software «tal cual», sin garantías. **No es asesoramiento financiero.**
