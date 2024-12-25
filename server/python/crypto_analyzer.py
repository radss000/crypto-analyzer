import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict
from . import indicators 

class CryptoAnalyzer:
    def __init__(self, token_address: str):
        self.token_address = token_address
        
    async def fetch_market_data(self) -> pd.DataFrame:
        """Fetch historical price and volume data from DexScreener"""
        url = f"https://api.dexscreener.com/latest/dex/tokens/{self.token_address}"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("Failed to fetch data from DexScreener")
            
        data = response.json()
        pairs = data.get('pairs', [])
        if not pairs:
            raise Exception("No trading pairs found")
            
        # Get the most liquid pair
        main_pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0)))
        
        # Convert price history to DataFrame
        df = pd.DataFrame(main_pair.get('priceHistory', []))
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df, main_pair

    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate technical indicators"""
        close_prices = df['price'].astype(float).values
        
        indicators_dict = {}
        
        # Momentum Indicators
        indicators_dict['rsi'] = indicators.calculate_rsi(close_prices)
        indicators_dict['macd'], indicators_dict['macd_signal'], indicators_dict['macd_hist'] = \
            indicators.calculate_macd(pd.Series(close_prices))
            
        # Volatility Indicators
        indicators_dict['bb_upper'], indicators_dict['bb_middle'], indicators_dict['bb_lower'] = \
            indicators.calculate_bollinger_bands(pd.Series(close_prices))
            
        # Trend Indicators
        indicators_dict['adx'] = indicators.calculate_adx(
            df['price'].astype(float).values,  # Using price as high
            df['price'].astype(float).values,  # Using price as low
            df['price'].astype(float).values
        )
                                    
        return indicators_dict

    def analyze_liquidity(self, pair_data: Dict) -> Dict:
        """Analyze liquidity metrics"""
        liquidity = float(pair_data.get('liquidity', {}).get('usd', 0))
        volume_24h = float(pair_data.get('volume', {}).get('h24', 0))
        
        depth_score = liquidity / volume_24h if volume_24h > 0 else 0
        
        return {
            'total_liquidity': liquidity,
            'volume_24h': volume_24h,
            'depth_score': depth_score
        }

    def calculate_risk_metrics(self, df: pd.DataFrame, liquidity_data: Dict) -> Dict:
        """Calculate risk metrics"""
        volatility_24h = df['price'].astype(float).pct_change().std() * np.sqrt(24)
        liquidity_concentration = liquidity_data['depth_score']
        
        risk_score = self._calculate_risk_score(
            volatility_24h,
            liquidity_concentration,
            liquidity_data['total_liquidity']
        )
        
        return {
            'volatility_24h': volatility_24h,
            'liquidity_concentration': liquidity_concentration,
            'risk_score': risk_score
        }

    def _calculate_risk_score(self, volatility: float, 
                            liquidity_concentration: float,
                            total_liquidity: float) -> float:
        """Calculate overall risk score"""
        vol_score = 1 - min(volatility, 1)
        liq_score = min(liquidity_concentration, 1)
        size_score = min(total_liquidity / 1_000_000, 1)  # Normalize to $1M
        
        weights = [0.4, 0.3, 0.3]
        return float(np.average([vol_score, liq_score, size_score], weights=weights))

    def generate_trading_signals(self, indicators_dict: Dict) -> Dict:
        """Generate trading signals based on technical indicators"""
        signals = {}
        
        # MACD Signal
        macd_signal = 1 if indicators_dict['macd'][-1] > indicators_dict['macd_signal'][-1] else -1
        
        # RSI Signal
        rsi_signal = 1 if indicators_dict['rsi'][-1] < 30 else (-1 if indicators_dict['rsi'][-1] > 70 else 0)
        
        # Bollinger Bands Signal
        bb_signal = 1 if indicators_dict['bb_lower'][-1] > indicators_dict['bb_middle'][-1] else \
                   (-1 if indicators_dict['bb_upper'][-1] < indicators_dict['bb_middle'][-1] else 0)
        
        signals = {
            'macd': macd_signal,
            'rsi': rsi_signal,
            'bollinger': bb_signal
        }
        
        composite_signal = float(np.mean([macd_signal, rsi_signal, bb_signal]))
        
        return {
            'individual_signals': signals,
            'composite_signal': composite_signal
        }

    async def run_analysis(self) -> Dict:
        """Run complete token analysis"""
        try:
            df, pair_data = await self.fetch_market_data()
            indicators_dict = self.calculate_technical_indicators(df)
            liquidity_data = self.analyze_liquidity(pair_data)
            risk_metrics = self.calculate_risk_metrics(df, liquidity_data)
            signals = self.generate_trading_signals(indicators_dict)
            
            # Calculate final scores
            technical_score = self._calculate_technical_score(indicators_dict, signals)
            confidence_score = float(np.average([
                technical_score,
                1 - risk_metrics['risk_score'],
                liquidity_data['depth_score']
            ], weights=[0.4, 0.3, 0.3]))
            
            return {
                'timestamp': datetime.now().isoformat(),
                'technical_indicators': {
                    'price_history': df[['timestamp', 'price']].to_dict('records'),
                    'current_price': float(df['price'].iloc[-1]),
                    'rsi': float(indicators_dict['rsi'][-1]),
                    'macd': float(indicators_dict['macd'][-1]),
                    'macd_signal': float(indicators_dict['macd_signal'][-1])
                },
                'liquidity_analysis': liquidity_data,
                'risk_metrics': risk_metrics,
                'trading_signals': signals,
                'final_scores': {
                    'technical_score': technical_score,
                    'confidence_score': confidence_score
                }
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _calculate_technical_score(self, indicators_dict: Dict, signals: Dict) -> float:
        """Calculate technical analysis score"""
        trend_strength = float(np.mean(indicators_dict['adx'][-10:]) / 100)
        momentum = float((indicators_dict['rsi'][-1] - 50) / 50)
        signal_strength = float(abs(signals['composite_signal']))
        
        weights = [0.4, 0.3, 0.3]
        score = float(np.average([
            trend_strength,
            abs(momentum),
            signal_strength
        ], weights=weights))
        
        return min(max(score, 0), 1)