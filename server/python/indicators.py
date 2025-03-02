"""Technical indicators calculation with improved accuracy"""
import numpy as np
import pandas as pd
from typing import Tuple, Dict, List

def calculate_rsi(prices: np.ndarray, period: int = 14) -> float:
    """
    Calculate RSI with proper exponential weighting
    
    Args:
        prices: Array of closing prices
        period: RSI period (default 14)
    """
    # Handle not enough data
    if len(prices) < period + 1:
        return 50.0  # Return neutral value
        
    # Check for constant values (no price change)
    if np.all(prices == prices[0]):
        return 50.0  # Return neutral value
        
    # Calculate price changes
    delta = np.diff(prices)
    delta = np.append(delta, delta[-1])  # Append last value to maintain array size
    
    # Separate gains and losses
    gains = np.where(delta > 0, delta, 0)
    losses = np.where(delta < 0, -delta, 0)
    
    # Check if all changes are gains or all are losses
    if np.all(losses == 0):
        return 100.0  # All price movements are up
    elif np.all(gains == 0):
        return 0.0    # All price movements are down
    
    # Calculate average gains and losses
    avg_gains = pd.Series(gains).ewm(alpha=1/period, min_periods=period).mean()
    avg_losses = pd.Series(losses).ewm(alpha=1/period, min_periods=period).mean()
    
    # Calculate RS and RSI (handle division by zero)
    rs = avg_gains.iloc[-1] / max(avg_losses.iloc[-1], 0.0001)  # Avoid division by zero
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi)

def calculate_macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    """
    Calculate MACD with proper exponential moving averages
    
    Args:
        prices: Array of closing prices
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period
    """
    # Calculate EMAs
    fast_ema = pd.Series(prices).ewm(span=fast, adjust=False).mean()
    slow_ema = pd.Series(prices).ewm(span=slow, adjust=False).mean()
    
    # Calculate MACD line
    macd_line = fast_ema - slow_ema
    
    # Calculate signal line
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    
    # Calculate histogram
    histogram = macd_line - signal_line
    
    return {
        'macd': float(macd_line.iloc[-1]),
        'signal': float(signal_line.iloc[-1]),
        'hist': float(histogram.iloc[-1])
    }

def calculate_bollinger_bands(prices: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
    """
    Calculate Bollinger Bands with proper standard deviation
    
    Args:
        prices: Array of closing prices
        period: Moving average period
        std_dev: Number of standard deviations
    """
    # Calculate middle band (SMA)
    middle_band = pd.Series(prices).rolling(window=period).mean()
    
    # Calculate standard deviation
    rolling_std = pd.Series(prices).rolling(window=period).std()
    
    # Calculate upper and lower bands
    upper_band = middle_band + (rolling_std * std_dev)
    lower_band = middle_band - (rolling_std * std_dev)
    
    return {
        'upper': float(upper_band.iloc[-1]),
        'middle': float(middle_band.iloc[-1]),
        'lower': float(lower_band.iloc[-1])
    }

def calculate_ema_signals(prices: np.ndarray) -> Dict[str, float]:
    """
    Calculate EMAs and their crossover signals
    """
    ema20 = pd.Series(prices).ewm(span=20, adjust=False).mean()
    ema50 = pd.Series(prices).ewm(span=50, adjust=False).mean()
    ema200 = pd.Series(prices).ewm(span=200, adjust=False).mean()
    
    return {
        'EMA20': float(ema20.iloc[-1]),
        'EMA50': float(ema50.iloc[-1]),
        'EMA200': float(ema200.iloc[-1])
    }

def calculate_risk_score(
    liquidity: float,
    volume: float,
    market_cap: float,
    volatility: float,
    buy_sell_ratio: float
) -> float:
    """
    Calculate improved risk score based on multiple factors
    
    Args:
        liquidity: Token liquidity in USD
        volume: 24h trading volume in USD
        market_cap: Token market capitalization
        volatility: Price volatility (standard deviation)
        buy_sell_ratio: Ratio of buys to sells
    """
    # Normalize metrics between 0 and 1
    liquidity_score = min(liquidity / 100_000_000, 1)  # Cap at $100M
    volume_score = min(volume / 10_000_000, 1)  # Cap at $10M
    mcap_score = min(market_cap / 1_000_000_000, 1)  # Cap at $1B
    volatility_score = 1 - min(volatility / 0.1, 1)  # Lower volatility = better
    balance_score = 1 - abs(1 - buy_sell_ratio)  # 1.0 means equal buys/sells
    
    # Weighted average with emphasis on liquidity and market cap
    weights = [0.3, 0.2, 0.25, 0.15, 0.1]
    scores = [liquidity_score, volume_score, mcap_score, volatility_score, balance_score]
    
    # Higher score means lower risk
    risk_score = 1 - np.average(scores, weights=weights)
    
    return float(min(max(risk_score, 0), 1))


def calculate_adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate ADX (Average Directional Index)
    
    Args:
        high: Array of high prices
        low: Array of low prices
        close: Array of closing prices
        period: ADX period (default 14)
    Returns:
        ADX values
    """
    if len(close) < period + 1:
        return np.zeros_like(close)
        
    # Calculate True Range
    tr1 = abs(high[1:] - low[1:])
    tr2 = abs(high[1:] - close[:-1])
    tr3 = abs(low[1:] - close[:-1])
    tr = np.maximum(tr1, tr2)
    tr = np.maximum(tr, tr3)
    tr = np.insert(tr, 0, tr[0])
    
    # Calculate ATR (Average True Range)
    atr = pd.Series(tr).ewm(span=period, adjust=False).mean()
    
    # Calculate +DM and -DM (Directional Movement)
    high_diff = high[1:] - high[:-1]
    low_diff = low[:-1] - low[1:]
    
    pos_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
    neg_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
    
    pos_dm = np.insert(pos_dm, 0, pos_dm[0])
    neg_dm = np.insert(neg_dm, 0, neg_dm[0])
    
    # Calculate +DI and -DI (Directional Indicators)
    pos_di = 100 * pd.Series(pos_dm).ewm(span=period, adjust=False).mean() / atr
    neg_di = 100 * pd.Series(neg_dm).ewm(span=period, adjust=False).mean() / atr
    
    # Calculate DX (Directional Index)
    dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di)
    
    # Calculate ADX
    adx = pd.Series(dx).ewm(span=period, adjust=False).mean()
    
    return float(adx.iloc[-1])

def get_trading_signals(
    rsi: float,
    macd_data: Dict[str, float],
    bb_data: Dict[str, float],
    ema_data: Dict[str, float],
    current_price: float
) -> Dict:
    """
    Generate comprehensive trading signals
    """
    signals = {
        'buy': 0,
        'sell': 0,
        'neutral': 0
    }
    
    # RSI signals
    if rsi < 30:
        signals['buy'] += 1
    elif rsi > 70:
        signals['sell'] += 1
    else:
        signals['neutral'] += 1
    
    # MACD signals
    if macd_data['macd'] > macd_data['signal']:
        signals['buy'] += 1
    elif macd_data['macd'] < macd_data['signal']:
        signals['sell'] += 1
    else:
        signals['neutral'] += 1
    
    # Bollinger Bands signals
    if current_price < bb_data['lower']:
        signals['buy'] += 1
    elif current_price > bb_data['upper']:
        signals['sell'] += 1
    else:
        signals['neutral'] += 1
    
    # EMA signals
    if current_price > ema_data['EMA20'] > ema_data['EMA50']:
        signals['buy'] += 1
    elif current_price < ema_data['EMA20'] < ema_data['EMA50']:
        signals['sell'] += 1
    else:
        signals['neutral'] += 1

    # Calculate total signals
    total_signals = signals['buy'] + signals['sell'] + signals['neutral']
    
    # Generate recommendation
    buy_strength = signals['buy'] / total_signals if total_signals > 0 else 0
    sell_strength = signals['sell'] / total_signals if total_signals > 0 else 0
    
    if buy_strength > 0.6:
        recommendation = 'STRONG_BUY'
    elif buy_strength > 0.4:
        recommendation = 'BUY'
    elif sell_strength > 0.6:
        recommendation = 'STRONG_SELL'
    elif sell_strength > 0.4:
        recommendation = 'SELL'
    else:
        recommendation = 'NEUTRAL'
    
    return {
        'recommendation': recommendation,
        'buy_signals': signals['buy'],
        'sell_signals': signals['sell'],
        'neutral_signals': signals['neutral'],
        'total_signals': total_signals,
        'summary': {
            'recommendation': recommendation,
            'buy_signals': signals['buy'],
            'sell_signals': signals['sell'],
            'neutral_signals': signals['neutral'],
            'total_signals': total_signals
        }
    }

def calculate_confidence_score(
    technical_signals: Dict,
    risk_score: float,
    price_momentum: float,
    volatility: float
) -> float:
    """
    Calculate improved confidence score
    """
    # Technical analysis weight
    total_signals = (technical_signals.get('buy_signals', 0) + 
                    technical_signals.get('sell_signals', 0) + 
                    technical_signals.get('neutral_signals', 0))
    
    if total_signals == 0:
        signal_score = 0.5
    else:
        buy_ratio = technical_signals.get('buy_signals', 0) / total_signals
        signal_score = buy_ratio
    
    # Momentum score normalized between 0 and 1
    momentum_score = 0.5 + (price_momentum / 100)
    momentum_score = min(max(momentum_score, 0), 1)
    
    # Volatility impact
    volatility_factor = 1 - min(volatility / 0.1, 1)
    
    # Combine scores with dynamic weights
    weights = [0.35, 0.25, 0.25, 0.15]  # Technical, risk, momentum, volatility
    scores = [signal_score, 1 - risk_score, momentum_score, volatility_factor]
    
    confidence = np.average(scores, weights=weights)
    
    return float(min(max(confidence, 0), 1))