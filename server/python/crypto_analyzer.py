import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, Optional
from tradingview_ta import TA_Handler, Interval
import sys
import time

class CryptoAnalyzer:
    def __init__(self, token_address: str):
        self.token_address = token_address
        self.base_url = "https://api.dexscreener.com/latest/dex"
        # Token address to TradingView symbol mapping
        self.token_symbols = {
            '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599': 'BTCUSDT',  # WBTC
            '0x514910771af9ca656af840dff83e8264ecf986ca': 'LINKUSDT', # LINK
            '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': 'ETHUSDT',  # WETH
            '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': 'USDCUSDT', # USDC
            # Add more tokens as needed
        }
        print(f"Initializing CryptoAnalyzer with token: {token_address}", file=sys.stderr)

    def _ensure_serializable(self, obj):
        """Ensure all values are JSON serializable"""
        if isinstance(obj, dict):
            return {key: self._ensure_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._ensure_serializable(item) for item in obj]
        elif isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        elif isinstance(obj, (np.int64, np.int32, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    async def get_tradingview_analysis(self, symbol: str) -> Optional[Dict]:
        """Get technical analysis from TradingView"""
        try:
            handler = TA_Handler(
                symbol=symbol,
                screener="crypto",
                exchange="BINANCE",
                interval=Interval.INTERVAL_1_HOUR
            )
            
            analysis = handler.get_analysis()
            
            indicators = analysis.indicators
            oscillators = analysis.oscillators
            moving_averages = analysis.moving_averages
            
            return {
                'indicators': {
                    'RSI': indicators.get('RSI', 50),
                    'MACD': {
                        'macd': indicators.get('MACD.macd', 0),
                        'signal': indicators.get('MACD.signal', 0),
                        'hist': indicators.get('MACD.hist', 0)
                    },
                    'BB': {
                        'upper': indicators.get('BB.upper', 0),
                        'middle': indicators.get('BB.middle', 0),
                        'lower': indicators.get('BB.lower', 0)
                    },
                    'EMA': {
                        'EMA20': indicators.get('EMA20', 0),
                        'EMA50': indicators.get('EMA50', 0),
                        'EMA200': indicators.get('EMA200', 0)
                    },
                    'volume': indicators.get('volume', 0),
                },
                'oscillators': {
                    'recommendation': oscillators.get('RECOMMENDATION', ''),
                    'buy_signals': oscillators.get('BUY', 0),
                    'sell_signals': oscillators.get('SELL', 0),
                    'neutral_signals': oscillators.get('NEUTRAL', 0)
                },
                'moving_averages': {
                    'recommendation': moving_averages.get('RECOMMENDATION', ''),
                    'buy_signals': moving_averages.get('BUY', 0),
                    'sell_signals': moving_averages.get('SELL', 0),
                    'neutral_signals': moving_averages.get('NEUTRAL', 0)
                },
                'summary': {
                    'recommendation': analysis.summary.get('RECOMMENDATION', ''),
                    'buy_signals': analysis.summary.get('BUY', 0),
                    'sell_signals': analysis.summary.get('SELL', 0),
                    'neutral_signals': analysis.summary.get('NEUTRAL', 0)
                }
            }
        except Exception as e:
            print(f"Warning: TradingView analysis failed: {e}", file=sys.stderr)
            return None

    def calculate_risk_score(self, liquidity: float, volume: float, buy_sell_ratio: float) -> float:
        """Calculate risk score based on liquidity and volume metrics"""
        # Normalize metrics
        liquidity_score = min(liquidity / 1_000_000, 10) / 10  # Normalize to 0-1, cap at $10M
        volume_score = min(volume / 100_000, 10) / 10  # Normalize to 0-1, cap at $100K
        
        # Buy/Sell ratio score (1.0 means equal buys/sells)
        balance_score = 1 - min(abs(1 - buy_sell_ratio), 1)
        
        # Weighted average
        weights = [0.5, 0.3, 0.2]  # Liquidity more important than volume
        risk_score = np.average([liquidity_score, volume_score, balance_score], weights=weights)
        
        return float(min(max(risk_score, 0), 1))

    def calculate_confidence_score(self, 
                                tradingview_signals: Dict,
                                risk_score: float,
                                price_change: float) -> float:
        """Calculate confidence score based on multiple factors"""
        if not tradingview_signals:
            return 0.5  # Neutral score if no TradingView data
            
        # Get signal counts
        buy_signals = tradingview_signals['summary']['buy_signals']
        sell_signals = tradingview_signals['summary']['sell_signals']
        total_signals = buy_signals + sell_signals
        
        if total_signals == 0:
            signal_score = 0.5
        else:
            signal_score = buy_signals / total_signals
            
        # Price momentum (normalized)
        momentum_score = 0.5 + (price_change / 100)  # Center around 0.5
        momentum_score = min(max(momentum_score, 0), 1)
        
        # Combine scores with weights
        weights = [0.4, 0.4, 0.2]  # Trading signals and risk equally important
        confidence = np.average([signal_score, risk_score, momentum_score], weights=weights)
        
        return float(min(max(confidence, 0), 1))

    async def fetch_market_data(self) -> Tuple[Dict, Dict]:
        """Fetch market data from both DexScreener and TradingView"""
        print(f"Fetching market data for token: {self.token_address}", file=sys.stderr)
        
        try:
            # Get DexScreener data
            url = f"{self.base_url}/tokens/{self.token_address}"
            print(f"Fetching from DexScreener: {url}", file=sys.stderr)
            
            response = requests.get(url, headers={
                'Accept': 'application/json',
                'User-Agent': 'TokenAnalyzer/1.0'
            })
            response.raise_for_status()
            
            data = response.json()
            pairs = data.get('pairs', [])
            
            if not pairs:
                raise Exception("No trading pairs found for this token")
            
            # Get most liquid pair
            main_pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0) or 0))
            print(f"Found main pair with liquidity: ${main_pair.get('liquidity', {}).get('usd', 0)}", file=sys.stderr)
            
            # Get TradingView analysis if available
            tv_analysis = None
            if self.token_address.lower() in [k.lower() for k in self.token_symbols.keys()]:
                symbol = self.token_symbols[self.token_address]
                print(f"Fetching TradingView analysis for {symbol}", file=sys.stderr)
                tv_analysis = await self.get_tradingview_analysis(symbol)
            
            return tv_analysis, main_pair
            
        except requests.RequestException as e:
            print(f"API request error: {e}", file=sys.stderr)
            raise
        except Exception as e:
            print(f"Error processing market data: {e}", file=sys.stderr)
            raise

    async def run_analysis(self) -> Dict:
        """Run complete token analysis"""
        try:
            print("\n=== Starting Token Analysis ===", file=sys.stderr)
            tradingview_data, pair_data = await self.fetch_market_data()
            
            # Extract key metrics
            current_price = float(pair_data.get('priceUsd', 0))
            volume_24h = float(pair_data.get('volume', {}).get('h24', 0))
            liquidity = float(pair_data.get('liquidity', {}).get('usd', 0))
            price_change = float(pair_data.get('priceChange', {}).get('h24', 0))
            
            # Calculate buy/sell ratio
            buys = int(pair_data.get('txns', {}).get('h24', {}).get('buys', 0))
            sells = int(pair_data.get('txns', {}).get('h24', {}).get('sells', 0))
            buy_sell_ratio = buys / sells if sells > 0 else 1.0
            
            # Calculate scores
            risk_score = self.calculate_risk_score(liquidity, volume_24h, buy_sell_ratio)
            confidence_score = self.calculate_confidence_score(tradingview_data, risk_score, price_change)
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'token_address': self.token_address,
                'pair_address': pair_data.get('pairAddress', ''),
                'dex': pair_data.get('dexId', ''),
                'chain': pair_data.get('chainId', ''),
                'market_data': {
                    'current_price': current_price,
                    'price_change_24h': price_change,
                    'volume_24h': volume_24h,
                    'liquidity': liquidity,
                    'transactions_24h': {
                        'buys': buys,
                        'sells': sells,
                        'buy_sell_ratio': buy_sell_ratio
                    }
                },
                'technical_analysis': tradingview_data if tradingview_data else {},
                'risk_metrics': {
                    'risk_score': risk_score,
                    'confidence_score': confidence_score
                }
            }
            
            print("\n=== Analysis Completed Successfully ===", file=sys.stderr)
            return self._ensure_serializable(result)
            
        except Exception as e:
            print(f"\n!!! Error in analysis: {str(e)}", file=sys.stderr)
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }