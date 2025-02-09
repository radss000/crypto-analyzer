import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, Optional, List
from tradingview_ta import TA_Handler, Interval
import sys
import time
import os
from indicators import calculate_rsi, calculate_macd, calculate_bollinger_bands, calculate_adx

class CryptoAnalyzer:
    def __init__(self, token_address: str, chain: str = 'ethereum'):
        self.token_address = token_address
        self.chain = chain.lower()
        self.base_url = "https://api.dexscreener.com/latest/dex"
        
        # Configuration par chaîne
        self.chain_configs = {
            'ethereum': {
                'address_prefix': '0x',
                'dex_list': ['uniswap', 'sushiswap'],
                'symbols': {
                    '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599': 'BTCUSDT',
                    '0x514910771af9ca656af840dff83e8264ecf986ca': 'LINKUSDT',
                    '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': 'ETHUSDT',
                    '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': 'USDCUSDT'
                }
            },
            'sui': {
                'address_prefix': '0x',
                'dex_list': ['suiswap', 'cetus'],
                'symbols': {}
            },
            'kaspa': {
                'address_prefix': 'kaspa:',
                'dex_list': ['kaspaswap'],
                'symbols': {}
            },
            'solana': {
                'address_prefix': '',
                'dex_list': ['raydium', 'orca'],
                'symbols': {}
            },
            'avalanche': {
                'address_prefix': '0x',
                'dex_list': ['traderjoe', 'pangolin'],
                'symbols': {}
            }
        }

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

    async def get_historical_prices(self, pair_data: Dict) -> List[float]:
        """Extraire ou récupérer les données historiques de prix"""
        try:
            # Pour l'exemple, utilisons les données des dernières 24h de DexScreener
            prices = []
            for i in range(24):
                price = pair_data.get(f'priceUsd{i}h', pair_data.get('priceUsd', 0))
                prices.append(float(price))
            return prices
        except Exception as e:
            print(f"Warning: Failed to get historical prices: {e}", file=sys.stderr)
            return []

    def calculate_risk_score(self, liquidity: float, volume: float, buy_sell_ratio: float = 1.0) -> float:
        """Calculate risk score based on liquidity and volume metrics"""
        # Normalize metrics
        liquidity_score = min(liquidity / 1_000_000, 10) / 10  # Normalize to 0-1, cap at $10M
        volume_score = min(volume / 100_000, 10) / 10  # Normalize to 0-1, cap at $100K
        
        # Buy/Sell ratio score (1.0 means equal buys/sells)
        balance_score = 1 - min(abs(1 - buy_sell_ratio), 1)
        
        # Chain-specific adjustments
        chain_multiplier = {
            'ethereum': 1.0,  # Reference chain
            'sui': 0.85,      # Newer chain
            'kaspa': 0.8,     # Newer chain
            'solana': 0.9,    # Established chain
            'avalanche': 0.9  # Established chain
        }.get(self.chain, 0.8)
        
        # Weighted average
        weights = [0.5, 0.3, 0.2]  # Liquidity more important than volume
        risk_score = np.average([liquidity_score, volume_score, balance_score], weights=weights)
        
        return float(min(max(risk_score * chain_multiplier, 0), 1))

    async def calculate_technical_indicators(self, pair_data: Dict) -> Dict:
        """Calcule les indicateurs techniques à partir des données disponibles"""
        prices = await self.get_historical_prices(pair_data)
        if not prices:
            return {}

        prices_array = np.array(prices)
        
        # Calcul du RSI
        rsi = calculate_rsi(prices_array)
        current_rsi = rsi[-1] if len(rsi) > 0 else 50

        # Calcul du MACD
        macd_line, signal_line, hist = calculate_macd(prices_array)
        current_macd = {
            'macd': float(macd_line[-1]) if len(macd_line) > 0 else 0,
            'signal': float(signal_line[-1]) if len(signal_line) > 0 else 0,
            'hist': float(hist[-1]) if len(hist) > 0 else 0
        }

        # Calcul des Bandes de Bollinger
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(prices_array)
        current_bb = {
            'upper': float(bb_upper[-1]) if len(bb_upper) > 0 else prices_array[-1],
            'middle': float(bb_middle[-1]) if len(bb_middle) > 0 else prices_array[-1],
            'lower': float(bb_lower[-1]) if len(bb_lower) > 0 else prices_array[-1]
        }

        # Générer des signaux basés sur les indicateurs
        signals = self.generate_signals(
            current_price=prices_array[-1],
            rsi=current_rsi,
            macd=current_macd,
            bollinger=current_bb
        )

        return {
            'indicators': {
                'RSI': current_rsi,
                'MACD': current_macd,
                'BB': current_bb,
                'EMA': {
                    'EMA20': float(np.mean(prices_array[-20:])) if len(prices_array) >= 20 else float(prices_array[-1]),
                    'EMA50': float(np.mean(prices_array[-50:])) if len(prices_array) >= 50 else float(prices_array[-1]),
                    'EMA200': float(np.mean(prices_array[-200:])) if len(prices_array) >= 200 else float(prices_array[-1])
                },
                'volume': pair_data.get('volume', {}).get('h24', 0)
            },
            'oscillators': signals['oscillators'],
            'moving_averages': signals['moving_averages'],
            'summary': signals['summary']
        }

    def generate_signals(self, current_price: float, rsi: float, 
                        macd: Dict, bollinger: Dict) -> Dict:
        """Génère des signaux de trading basés sur les indicateurs"""
        signals = {
            'oscillators': {'buy': 0, 'sell': 0, 'neutral': 0},
            'moving_averages': {'buy': 0, 'sell': 0, 'neutral': 0},
            'summary': {'buy': 0, 'sell': 0, 'neutral': 0}
        }

        # Signaux RSI
        if rsi < 30:
            signals['oscillators']['buy'] += 1
        elif rsi > 70:
            signals['oscillators']['sell'] += 1
        else:
            signals['oscillators']['neutral'] += 1

        # Signaux MACD
        if macd['macd'] > macd['signal']:
            signals['oscillators']['buy'] += 1
        elif macd['macd'] < macd['signal']:
            signals['oscillators']['sell'] += 1
        else:
            signals['oscillators']['neutral'] += 1

        # Signaux Bollinger Bands
        if current_price < bollinger['lower']:
            signals['moving_averages']['buy'] += 1
        elif current_price > bollinger['upper']:
            signals['moving_averages']['sell'] += 1
        else:
            signals['moving_averages']['neutral'] += 1

        # Calculer les totaux
        signals['summary'] = {
            'buy': signals['oscillators']['buy'] + signals['moving_averages']['buy'],
            'sell': signals['oscillators']['sell'] + signals['moving_averages']['sell'],
            'neutral': signals['oscillators']['neutral'] + signals['moving_averages']['neutral']
        }

        # Déterminer la recommandation
        for category in ['oscillators', 'moving_averages', 'summary']:
            buy = signals[category]['buy']
            sell = signals[category]['sell']
            
            if buy > sell:
                recommendation = 'BUY'
            elif sell > buy:
                recommendation = 'SELL'
            else:
                recommendation = 'NEUTRAL'
                
            signals[category] = {
                'recommendation': recommendation,
                'buy_signals': buy,
                'sell_signals': sell,
                'neutral_signals': signals[category]['neutral']
            }

        return signals

    async def get_chain_specific_metrics(self) -> Dict:
        """Get metrics specific to each chain"""
        try:
            chain_data = {}
            
            if self.chain == 'sui':
                chain_data = {
                    'tps': 'Unknown',
                    'epoch': 'Unknown',
                    'total_transactions': 'Unknown'
                }
            elif self.chain == 'kaspa':
                chain_data = {
                    'blockdag_status': 'Unknown',
                    'network_hashrate': 'Unknown'
                }
            elif self.chain == 'solana':
                chain_data = {
                    'slot': 'Unknown',
                    'recent_performance': 'Unknown'
                }
            
            return chain_data
            
        except Exception as e:
            print(f"Warning: Failed to get chain-specific metrics: {e}", file=sys.stderr)
            return {}

    async def fetch_market_data(self) -> Tuple[Dict, Dict]:
        """Fetch market data from DEX and chain-specific sources"""
        try:
            url = f"{self.base_url}/tokens/{self.token_address}"
            response = requests.get(url)
            data = response.json()
            
            pairs = data.get('pairs', [])
            if not pairs:
                raise Exception(f"No trading pairs found for token on {self.chain}")
            
            # Filter pairs by chain if specified in API response
            chain_pairs = [p for p in pairs if p.get('chainId', '').lower() == self.chain]
            active_pairs = chain_pairs if chain_pairs else pairs
            
            main_pair = max(active_pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0) or 0))
            
            # Get TradingView analysis for supported tokens
            tv_analysis = None
            chain_config = self.chain_configs.get(self.chain, {})
            if chain_config.get('symbols', {}).get(self.token_address.lower()):
                symbol = chain_config['symbols'][self.token_address.lower()]
                tv_analysis = await self.get_tradingview_analysis(symbol)
            
            return tv_analysis, main_pair
            
        except requests.RequestException as e:
            print(f"API request error: {e}", file=sys.stderr)
            raise
        except Exception as e:
            print(f"Error processing market data: {e}", file=sys.stderr)
            raise

    def calculate_confidence_score(self, 
                                tradingview_signals: Optional[Dict],
                                risk_score: float,
                                price_change: float) -> float:
        """Calculate confidence score with chain-specific adjustments"""
        # Base calculation
        if not tradingview_signals:
            signal_score = 0.5
        else:
            buy_signals = tradingview_signals['summary']['buy_signals']
            sell_signals = tradingview_signals['summary']['sell_signals']
            total_signals = buy_signals + sell_signals
            signal_score = buy_signals / total_signals if total_signals > 0 else 0.5
        
        # Price momentum
        momentum_score = 0.5 + (price_change / 100)
        momentum_score = min(max(momentum_score, 0), 1)
        
        # Chain-specific adjustments
        chain_confidence = {
            'ethereum': 1.0,  # Reference chain
            'sui': 0.85,      # Newer chain
            'kaspa': 0.8,     # Newer chain
            'solana': 0.9,    # Established chain
            'avalanche': 0.9  # Established chain
        }
        
        chain_multiplier = chain_confidence.get(self.chain, 0.8)
        
        # Weighted average with chain adjustment
        weights = [0.4, 0.4, 0.2]
        base_confidence = np.average([signal_score, risk_score, momentum_score], weights=weights)
        confidence = base_confidence * chain_multiplier
        
        return float(min(max(confidence, 0), 1))

    async def run_analysis(self) -> Dict:
        """Run complete token analysis with chain support"""
        try:
            print(f"\n=== Starting Token Analysis on {self.chain.upper()} ===", file=sys.stderr)
            
            tradingview_data, pair_data = await self.fetch_market_data()
            
            # Si pas de données TradingView, utiliser notre propre analyse technique
            if not tradingview_data:
                tradingview_data = await self.calculate_technical_indicators(pair_data)
            
            chain_metrics = await self.get_chain_specific_metrics()
            
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
                'chain': self.chain,
                'pair_address': pair_data.get('pairAddress', ''),
                'dex': pair_data.get('dexId', ''),
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
                'chain_specific': chain_metrics,
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