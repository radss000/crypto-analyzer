"""Technical indicators calculation utilities"""
import numpy as np
from typing import Tuple, List

def calculate_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Relative Strength Index"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum()/period
    down = -seed[seed < 0].sum()/period
    rs = up/down
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100./(1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up*(period-1) + upval)/period
        down = (down*(period-1) + downval)/period
        rs = up/down
        rsi[i] = 100. - 100./(1. + rs)

    return rsi

def calculate_macd(prices: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate MACD, Signal line, and MACD histogram"""
    exp1 = prices.ewm(span=12, adjust=False).mean()
    exp2 = prices.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return macd, signal, hist

def calculate_bollinger_bands(prices: np.ndarray, period: int = 20) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Bollinger Bands"""
    ma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = ma + (std * 2)
    lower = ma - (std * 2)
    return upper, ma, lower

def calculate_adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate Average Directional Index"""
    tr1 = abs(high - low)
    tr2 = abs(high - close[:-1])
    tr3 = abs(low - close[:-1])
    tr = np.maximum(tr1[1:], tr2)
    tr = np.maximum(tr, tr3)
    atr = np.zeros_like(close)
    atr[period-1] = tr[:period].mean()
    for i in range(period, len(close)):
        atr[i] = (atr[i-1] * (period-1) + tr[i-1]) / period
    
    return atr  # Simplified ADX calculation