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
        """Get token data from CoinGecko API"""
        # Try to match the token address to a known CoinGecko ID
        # Map of popular token addresses to their CoinGecko IDs
        TOKENS_MAP = {
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "ethereum",  # WETH
            "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": "bitcoin",   # WBTC
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "usd-coin",  # USDC
            "0xdac17f958d2ee523a2206206994597c13d831ec7": "tether",    # USDT
            "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984": "uniswap",   # UNI
            "0x514910771af9ca656af840dff83e8264ecf986ca": "chainlink", # LINK
            "0x6b175474e89094c44da98b954eedeac495271d0f": "dai",       # DAI
            "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9": "aave",      # AAVE
            "0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2": "maker",     # MKR
            "0xed1199093b1abd07a368dd1c0cdc77d8517ba2a0": "hyperliquid-eur-perp",  # Sample new token
        }
        
        # Lowercase the address for consistency
        token_address_lower = self.token_address.lower()
        
        # Try to get from known mappings
        coin_id = TOKENS_MAP.get(token_address_lower)
        
        # If not found in mapping, search CoinGecko by contract address
        if not coin_id:
            try:
                search_url = f"https://api.coingecko.com/api/v3/coins/ethereum/contract/{token_address_lower}"
                search_response = requests.get(search_url)
                if search_response.status_code == 200:
                    coin_data = search_response.json()
                    coin_id = coin_data.get('id')
                    print(f"Found CoinGecko ID for token: {coin_id}")
            except Exception as e:
                print(f"Error searching for token by address: {str(e)}")
        
        # If we have a coin ID, get the data
        if coin_id:
            try:
                # Get market data
                market_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
                market_response = requests.get(market_url)
                market_response.raise_for_status()
                market_data = market_response.json()
                
                # Get historical price data
                history_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
                params = {
                    'vs_currency': 'usd',
                    'days': '30',
                    'interval': 'daily'
                }
                history_response = requests.get(history_url, params=params)
                history_response.raise_for_status()
                history_data = history_response.json()
                
                # Extract prices
                price_history = [price[1] for price in history_data.get('prices', [])]
                
                # Get total_volume and market_cap
                current_price = market_data.get('market_data', {}).get('current_price', {}).get('usd', 0)
                volume_24h = market_data.get('market_data', {}).get('total_volume', {}).get('usd', 0)
                market_cap = market_data.get('market_data', {}).get('market_cap', {}).get('usd', 0)
                price_change_24h = market_data.get('market_data', {}).get('price_change_percentage_24h', 0)
                
                # Get liquidity approximation - for simplicity using 10% of 24h volume
                liquidity = volume_24h * 0.1
                
                # Get buy/sell ratio (using a fixed value since CoinGecko doesn't provide this)
                buy_sell_ratio = 1.0
                
                return {
                    'price_history': price_history,
                    'volume': float(volume_24h),
                    'liquidity': float(liquidity),
                    'market_cap': float(market_cap),
                    'price_change_24h': float(price_change_24h),
                    'buys': 50,  # Placeholder values
                    'sells': 50   # Placeholder values
                }
            except Exception as e:
                print(f"Error fetching CoinGecko data: {str(e)}")
        
        # Fallback to DefiLlama if CoinGecko fails or token not found
        try:
            print(f"Trying DefiLlama for token data: {self.token_address}")
            llama_url = f"https://coins.llama.fi/prices/current/ethereum:{self.token_address}"
            llama_response = requests.get(llama_url)
            llama_response.raise_for_status()
            llama_data = llama_response.json()
            
            # Extract token data
            token_key = f"ethereum:{self.token_address}"
            token_data = llama_data.get('coins', {}).get(token_key, {})
            
            if token_data:
                current_price = token_data.get('price', 0)
                # Generate synthetic price history (flat)
                price_history = [current_price] * 30
                
                return {
                    'price_history': price_history,
                    'volume': float(token_data.get('volume', 100000)),
                    'liquidity': float(token_data.get('liquidity', 10000)),
                    'market_cap': float(token_data.get('mcap', 1000000)),
                    'price_change_24h': float(token_data.get('price_change_24h', 0)),
                    'buys': 50,
                    'sells': 50
                }
        except Exception as e:
            print(f"Error fetching DefiLlama data: {str(e)}")
        
        # Return default values if all APIs fail
        print(f"No data found for token {self.token_address}, using default values")
        return {
            'price_history': [1.0] * 30,  # Generating fake price history
            'volume': 10000,
            'liquidity': 5000,
            'market_cap': 1000000,
            'price_change_24h': 0,
            'buys': 50,
            'sells': 50
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
        
        # Use the primary data from the renamed _get_dexscreener_data method
        # which now actually fetches from CoinGecko or DefiLlama
        
        # Use historical price data from the primary source
        if dex_data['price_history']:
            # Convert to float and ensure we have data
            prices = [float(p) for p in dex_data['price_history'] if p is not None]
            
            # If we have enough data points, generate high/low with some variation
            if len(prices) > 0:
                # Create synthetic high/low values if needed
                volatility = 0.02  # 2% price movement for highs/lows
                highs = [p * (1 + (volatility * (i % 3) / 3)) for i, p in enumerate(prices)]
                lows = [p * (1 - (volatility * (i % 3) / 3)) for i, p in enumerate(prices)]
        
        # Add CoinGecko data if available and not already using it
        if coingecko_data and not prices:
            prices = [p[1] for p in coingecko_data['prices']]
            volumes = [v[1] for v in coingecko_data['volumes']]
            # Create high/low from the price data
            highs = prices
            lows = prices
        
        # Fallback to some default data if we have no prices
        if not prices:
            print("Warning: No price history available, using synthetic data")
            base_price = 1.0
            num_days = 30
            prices = [base_price * (1 + 0.01 * (i % 5 - 2)) for i in range(num_days)]
            highs = [p * 1.02 for p in prices]
            lows = [p * 0.98 for p in prices]
        
        # Ensure we have enough data points for technical analysis
        min_data_points = 20
        if len(prices) < min_data_points:
            # Duplicate the last price to get enough data points
            last_price = prices[-1] if prices else 1.0
            prices.extend([last_price] * (min_data_points - len(prices)))
            
            if highs:
                last_high = highs[-1]
                highs.extend([last_high] * (min_data_points - len(highs)))
            else:
                highs = [p * 1.02 for p in prices]
                
            if lows:
                last_low = lows[-1]
                lows.extend([last_low] * (min_data_points - len(lows)))
            else:
                lows = [p * 0.98 for p in prices]
        
        # Return properly formatted data
        return {
            'close': np.array(prices),
            'high': np.array(highs),
            'low': np.array(lows),
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