import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional
from indicators import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_ema_signals,
    calculate_adx,
    calculate_risk_score,
    calculate_confidence_score,
    get_trading_signals
)

class CryptoAnalyzer:
    def __init__(self, token_address: str, chain: str = "ethereum"):
        self.token_address = token_address
        self.chain = chain
        self.base_url = "https://api.dexscreener.com/latest/dex"
        print(f"Initializing CryptoAnalyzer with token: {token_address} on chain: {chain}")

    def _normalize_token_address(self) -> str:
        """Normalise l'adresse du token en fonction de la chaîne"""
        CHAIN_MAPPINGS = {
            "ethereum": lambda addr: addr.lower(),
            "sui": lambda addr: addr if "sui" in addr else f"0x2::sui::{addr}",
            "solana": lambda addr: addr.upper(),
            # Ajoutez d'autres chaînes selon vos besoins
        }
        
        if self.chain in CHAIN_MAPPINGS:
            return CHAIN_MAPPINGS[self.chain](self.token_address)
        return self.token_address

    def _get_chain_explorer_url(self) -> str:
        """Retourne l'URL de l'explorateur de la chaîne"""
        CHAIN_EXPLORERS = {
            "ethereum": "https://etherscan.io",
            "sui": "https://suiscan.com",
            "solana": "https://solscan.io",
            # Ajoutez d'autres chaînes selon vos besoins
        }
        return CHAIN_EXPLORERS.get(self.chain, "")
            
    async def get_historical_prices(self) -> Dict[str, np.ndarray]:
        """Get historical price data for calculations"""
        try:
            # 1. D'abord, on récupère les données de DexScreener pour les données récentes
            dex_data = await self._get_dexscreener_data()
            
            # 2. Ensuite, on récupère les données de CoinGecko pour l'historique
            coingecko_data = await self._get_coingecko_data()
            
            # 3. On fusionne les données
            combined_data = self._merge_price_data(dex_data, coingecko_data)
            
            return combined_data
            
        except Exception as e:
            print(f"Error fetching historical data: {str(e)}")
            raise

    async def _get_dexscreener_data(self):
        url = f"{self.base_url}/tokens/{self.token_address}"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        pairs = data.get('pairs', [])
        
        if not pairs:
            print(f"Warning: No trading pairs found for {self.token_address}")
            # Au lieu de lever une exception, renvoyer des données par défaut
            return {
                'price_history': [],
                'volume': 0,
                'liquidity': 0,
                'market_cap': 0,
                'price_change_24h': 0,
                'buys': 0,
                'sells': 0
            }
            
        main_pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0) or 0))
        
        return {
            'price_history': main_pair.get('priceHistory', []),
            'volume': float(main_pair.get('volume', {}).get('h24', 0)),
            'liquidity': float(main_pair.get('liquidity', {}).get('usd', 0)),
            'market_cap': float(main_pair.get('fdv', 0)),
            'price_change_24h': float(main_pair.get('priceChange', {}).get('h24', 0)),
            'buys': float(main_pair.get('txns', {}).get('h24', {}).get('buys', 0)),
            'sells': float(main_pair.get('txns', {}).get('h24', {}).get('sells', 1))
        }

    async def _get_coingecko_data(self):
        # Mapping des adresses de token vers les IDs CoinGecko
        COINGECKO_IDS = {
            "0x2::sui::SUI": "sui",
            # Ajoutez d'autres mappings ici
        }
        
        token_id = COINGECKO_IDS.get(self.token_address)
        if not token_id:
            return None
            
        url = f"https://api.coingecko.com/api/v3/coins/{token_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': '200',
            'interval': 'daily'
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return {
                'prices': data.get('prices', []),
                'volumes': data.get('total_volumes', []),
                'market_caps': data.get('market_caps', [])
            }
        return None

    def _merge_price_data(self, dex_data, coingecko_data):
        prices = []
        volumes = []
        highs = []
        lows = []
        
        # Si on a des données CoinGecko, on les utilise comme base
        if coingecko_data:
            prices = [p[1] for p in coingecko_data['prices']]
            volumes = [v[1] for v in coingecko_data['volumes']]
            # On utilise le prix comme high/low en l'absence de données plus précises
            highs = prices
            lows = prices
        
        # On ajoute les données DexScreener récentes
        if dex_data['price_history']:
            recent_prices = [float(p) for p in dex_data['price_history']]
            prices = prices[-100:] + recent_prices  # On garde les 100 derniers points
        
        return {
            'close': np.array(prices),
            'high': np.array(highs) if highs else np.array(prices),
            'low': np.array(lows) if lows else np.array(prices),
            'volume': dex_data['volume'],
            'liquidity': dex_data['liquidity'],
            'market_cap': dex_data['market_cap'],
            'price_change_24h': dex_data['price_change_24h'],
            'buy_sell_ratio': dex_data['buys'] / dex_data['sells'] if dex_data['sells'] > 0 else 1.0
        }

    async def analyze_technical_indicators(self, price_data: Dict[str, np.ndarray]) -> Dict:
        """Calculate technical indicators"""
        if len(price_data['close']) == 0:
            return {}
            
        prices = price_data['close']
        current_price = prices[-1]
        
        # Calculate indicators
        rsi = calculate_rsi(prices)
        macd_data = calculate_macd(prices)
        bb_data = calculate_bollinger_bands(prices)
        ema_data = calculate_ema_signals(prices)
        adx = calculate_adx(price_data['high'], price_data['low'], prices)
        
        # Get trading signals
        signals = get_trading_signals(rsi, macd_data, bb_data, ema_data, current_price)
        
        # Add market data to technical analysis
        return {
            'indicators': {
                'RSI': rsi,
                'MACD': macd_data,
                'BB': bb_data,
                'EMA': ema_data,
                'ADX': adx
            },
            'market_data': {
                'current_price': current_price,
                'volume_24h': price_data['volume'],
                'liquidity': price_data['liquidity'],
                'price_change_24h': price_data['price_change_24h'],
                'market_cap': price_data['market_cap'],
                'buy_sell_ratio': price_data['buy_sell_ratio']
            },
            'signals': signals
        }

    async def run_analysis(self) -> Dict:
            try:
                print(f"\n=== Starting analysis for {self.token_address} on {self.chain} ===")
                
                # Fetch market data
                try:
                    price_data = await self.get_historical_prices()
                except Exception as e:
                    return {
                        'timestamp': datetime.now().isoformat(),
                        'token_address': self.token_address,
                        'chain': self.chain,
                        'error': f"Failed to retrieve market data: {str(e)}",
                        'status': 'no_data'
                    }
                
                # Validation des données
                if not price_data or len(price_data['close']) == 0:
                    return {
                        'timestamp': datetime.now().isoformat(),
                        'token_address': self.token_address,
                        'chain': self.chain,
                        'error': "No price data available for analysis",
                        'status': 'no_data'
                    }
                    
                if np.any(np.isnan(price_data['close'])) or np.any(np.isinf(price_data['close'])):
                    return {
                        'timestamp': datetime.now().isoformat(),
                        'token_address': self.token_address,
                        'chain': self.chain,
                        'error': "Invalid price data detected (NaN or Inf values)",
                        'status': 'invalid_data'
                    }
                    
                # Vérification minimum de points pour l'analyse technique
                if len(price_data['close']) < 10:  # Minimum requis pour la plupart des indicateurs
                    return {
                        'timestamp': datetime.now().isoformat(),
                        'token_address': self.token_address,
                        'chain': self.chain,
                        'market_data': {
                            'current_price': float(price_data['close'][-1]) if len(price_data['close']) > 0 else 0,
                            'volume_24h': price_data['volume'],
                            'liquidity': price_data['liquidity'],
                            'price_change_24h': price_data['price_change_24h']
                        },
                        'note': f'Limited historical data ({len(price_data["close"])} points) for technical analysis',
                        'status': 'limited_data'
                    }
                        
                # Calculate technical indicators
                try:
                    analysis_results = await self.analyze_technical_indicators(price_data)
                    print("Technical analysis completed")
                except Exception as e:
                    return {
                        'timestamp': datetime.now().isoformat(),
                        'token_address': self.token_address,
                        'chain': self.chain,
                        'market_data': {
                            'current_price': float(price_data['close'][-1]),
                            'volume_24h': float(price_data['volume']),
                            'liquidity': float(price_data['liquidity']),
                            'price_change_24h': float(price_data['price_change_24h'])
                        },
                        'error': f"Failed to calculate technical indicators: {str(e)}",
                        'status': 'analysis_error'
                    }
                    
                # Validation des résultats techniques
                if not analysis_results or 'indicators' not in analysis_results:
                    return {
                        'timestamp': datetime.now().isoformat(),
                        'token_address': self.token_address,
                        'chain': self.chain,
                        'market_data': {
                            'current_price': float(price_data['close'][-1]),
                            'volume_24h': float(price_data['volume']),
                            'liquidity': float(price_data['liquidity']),
                            'price_change_24h': float(price_data['price_change_24h'])
                        },
                        'error': "Technical analysis failed to produce valid results",
                        'status': 'invalid_results'
                    }
                    
                # Calculate risk metrics with validation
                try:
                    volatility = np.std(price_data['close']) / np.mean(price_data['close'])
                    if np.isnan(volatility) or np.isinf(volatility):
                        volatility = 0.5  # Valeur par défaut si calcul invalide
                        
                    risk_score = calculate_risk_score(
                        liquidity=max(0, price_data['liquidity']),
                        volume=max(0, price_data['volume']),
                        market_cap=max(0, price_data['market_cap']),
                        volatility=min(1.0, volatility),
                        buy_sell_ratio=max(0.1, min(10, price_data['buy_sell_ratio']))
                    )
                    
                    confidence_score = calculate_confidence_score(
                        technical_signals=analysis_results['signals'],
                        risk_score=risk_score,
                        price_momentum=price_data['price_change_24h'],
                        volatility=volatility
                    )
                except Exception as e:
                    return {
                        'timestamp': datetime.now().isoformat(),
                        'token_address': self.token_address,
                        'chain': self.chain,
                        'market_data': {
                            'current_price': float(price_data['close'][-1]),
                            'volume_24h': float(price_data['volume']),
                            'liquidity': float(price_data['liquidity']),
                            'price_change_24h': float(price_data['price_change_24h'])
                        },
                        'technical_analysis': {
                            'indicators': {
                                k: float(v) if isinstance(v, (int, float, np.number)) else v
                                for k, v in analysis_results['indicators'].items()
                            } if 'indicators' in analysis_results else {},
                            'signals': analysis_results.get('signals', {})
                        },
                        'error': f"Failed to calculate risk metrics: {str(e)}",
                        'status': 'risk_calculation_error'
                    }
                    
                # Final result
                return {
                    'timestamp': datetime.now().isoformat(),
                    'token_address': self.token_address,
                    'chain': self.chain,
                    'market_data': {
                        'current_price': float(price_data['close'][-1]),
                        'volume_24h': float(price_data['volume']),
                        'liquidity': float(price_data['liquidity']),
                        'price_change_24h': float(price_data['price_change_24h']),
                        'market_cap': float(price_data['market_cap']),
                        'buy_sell_ratio': float(price_data['buy_sell_ratio'])
                    },
                    'technical_analysis': {
                        'indicators': {
                            k: float(v) if isinstance(v, (int, float, np.number)) else v
                            for k, v in analysis_results['indicators'].items()
                        },
                        'signals': analysis_results['signals']
                    },
                    'risk_metrics': {
                        'risk_score': float(risk_score),
                        'confidence_score': float(confidence_score),
                        'volatility': float(volatility)
                    },
                    'status': 'success'
                }
                        
            except Exception as e:
                print(f"Analysis error: {str(e)}")
                return {
                    'timestamp': datetime.now().isoformat(),
                    'token_address': self.token_address,
                    'chain': self.chain,
                    'error': f"Unexpected error: {str(e)}",
                    'status': 'error'
                }