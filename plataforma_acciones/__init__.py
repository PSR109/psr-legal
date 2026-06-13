"""Plataforma acciones — trading algorítmico cuantitativo con auto-aprendizaje.

ADVERTENCIA IMPORTANTE
----------------------
Este software es una herramienta de INVESTIGACIÓN y EDUCACIÓN cuantitativa.
El objetivo del 15% anual es una META DE OPTIMIZACIÓN sobre datos históricos y
simulados, NO una rentabilidad garantizada. Los mercados reales conllevan
riesgo de pérdida total. Ningún sistema puede garantizar rentabilidades
futuras. No es asesoramiento financiero. Úsalo bajo tu responsabilidad.
"""
from __future__ import annotations

__version__ = "1.0.0"

from . import backtest, data, engine, indicators, learning, metrics, strategies

__all__ = [
    "backtest", "data", "engine", "indicators", "learning", "metrics", "strategies",
]
