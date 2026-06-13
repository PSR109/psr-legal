"""Indicadores técnicos vectorizados (sin dependencias externas pesadas)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window, min_periods=1).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Índice de fuerza relativa (0-100)."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100.0 - 100.0 / (1.0 + rs)
    return out.fillna(50.0)


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Devuelve (línea MACD, línea de señal, histograma)."""
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line, macd_line - signal_line


def bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0):
    """Devuelve (banda media, superior, inferior)."""
    mid = sma(series, window)
    std = series.rolling(window, min_periods=1).std(ddof=0)
    return mid, mid + num_std * std, mid - num_std * std


def rolling_volatility(returns: pd.Series, window: int = 20) -> pd.Series:
    return returns.rolling(window, min_periods=1).std(ddof=0)


def momentum(series: pd.Series, window: int = 60) -> pd.Series:
    """Retorno acumulado en una ventana (momentum de precio)."""
    return series / series.shift(window) - 1.0


def zscore(series: pd.Series, window: int = 20) -> pd.Series:
    mean = series.rolling(window, min_periods=1).mean()
    std = series.rolling(window, min_periods=1).std(ddof=0)
    return ((series - mean) / std.replace(0.0, np.nan)).fillna(0.0)


def atr_proxy(prices: pd.Series, window: int = 14) -> pd.Series:
    """Proxy de Average True Range usando solo precios de cierre."""
    return prices.diff().abs().rolling(window, min_periods=1).mean()
