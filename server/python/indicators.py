"""Technical indicators calculation utilities"""
import numpy as np
import pandas as pd
from typing import Tuple, List

def calculate_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate RSI with proper scaling"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum()/period
    down = -seed[seed < 0].sum()/period
    
    if down == 0:
        rs = np.inf
    else:
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
        
        if down == 0:
            rs = np.inf
        else:
            rs = up/down
        
        rsi[i] = 100. - 100./(1. + rs)
    
    return rsi

def calculate_macd(prices: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate MACD with percentage values"""
    # Convert to percentage changes
    pct_changes = np.diff(prices) / prices[:-1]
    pct_changes = np.insert(pct_changes, 0, 0)
    
    # Calculate EMAs on percentage changes
    exp1 = pd.Series(pct_changes).ewm(span=12, adjust=False).mean()
    exp2 = pd.Series(pct_changes).ewm(span=26, adjust=False).mean()
    
    macd = (exp1 - exp2) * 100  # Convert to percentage
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    
    return macd.to_numpy(), signal.to_numpy(), hist.to_numpy()

def calculate_bollinger_bands(prices: np.ndarray, period: int = 20) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate Bollinger Bands"""
    if len(prices) < period:
        return prices, prices, prices
        
    # Calculate on percentage changes
    pct_changes = pd.Series(prices)
    
    # Calculate middle band (SMA)
    middle = pct_changes.rolling(window=period, min_periods=1).mean()
    
    # Calculate standard deviation
    std = pct_changes.rolling(window=period, min_periods=1).std()
    
    # Calculate upper and lower bands
    upper = middle + (std * 2)
    lower = middle - (std * 2)
    
    return upper.to_numpy(), middle.to_numpy(), lower.to_numpy()

def calculate_adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculate ADX (Average Directional Index)"""
    if len(close) < period + 1:
        return np.zeros_like(close)
        
    # Calculate True Range
    tr1 = abs(high[1:] - low[1:])
    tr2 = abs(high[1:] - close[:-1])
    tr3 = abs(low[1:] - close[:-1])
    tr = np.maximum(tr1, tr2)
    tr = np.maximum(tr, tr3)
    tr = np.insert(tr, 0, tr[0])
    
    # Smooth True Range
    atr = pd.Series(tr).rolling(window=period).mean().to_numpy()
    
    # Directional Movement
    up_move = high[1:] - high[:-1]
    down_move = low[:-1] - low[1:]
    
    pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    pos_dm = np.insert(pos_dm, 0, pos_dm[0])
    neg_dm = np.insert(neg_dm, 0, neg_dm[0])
    
    # Smooth DM
    pos_di = 100 * pd.Series(pos_dm).rolling(window=period).mean() / atr
    neg_di = 100 * pd.Series(neg_dm).rolling(window=period).mean() / atr
    
    # Calculate ADX
    dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di)
    adx = pd.Series(dx).rolling(window=period).mean().fillna(0).to_numpy()
    
    return adx