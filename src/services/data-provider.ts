// src/services/data-provider.ts

import axios from 'axios';
import { createClient } from 'urql';
import { MarketData, OnChainData, TokenAnalysisResult } from '../types/token';

class TokenDataProvider {
    private coingeckoApi: string;
    private graphClient: any;
    private cache: Map<string, { data: TokenAnalysisResult; timestamp: number }>;
    private CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

    constructor() {
        this.coingeckoApi = "https://api.coingecko.com/api/v3";
        this.graphClient = createClient({
            url: 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
        });
        this.cache = new Map();
    }

    private getCacheKey(address: string, chain: string = 'ethereum'): string {
        return `${chain}-${address.toLowerCase()}`;
    }

    async getCompleteTokenData(address: string, chain: string = 'ethereum'): Promise<TokenAnalysisResult> {
        const cacheKey = this.getCacheKey(address, chain);
        const cached = this.cache.get(cacheKey);

        if (cached && Date.now() - cached.timestamp < this.CACHE_DURATION) {
            console.log('Returning cached data');
            return cached.data;
        }

        try {
            // Parallel fetch of data from different sources
            const [marketData, onChainData] = await Promise.all([
                this.getMarketData(address),
                this.getOnChainData(address)
            ]);

            const result: TokenAnalysisResult = {
                timestamp: new Date().toISOString(),
                token_address: address,
                chain,
                market_data: marketData,
                on_chain_data: onChainData
            };

            // Cache the result
            this.cache.set(cacheKey, {
                data: result,
                timestamp: Date.now()
            });

            return result;

        } catch (error) {
            console.error('Error fetching token data:', error);
            throw error;
        }
    }

    private async getMarketData(address: string): Promise<MarketData> {
        try {
            const [marketChart, tokenInfo] = await Promise.all([
                axios.get(`${this.coingeckoApi}/coins/ethereum/contract/${address}/market_chart?vs_currency=usd&days=200`),
                axios.get(`${this.coingeckoApi}/coins/ethereum/contract/${address}`)
            ]);

            return {
                prices: marketChart.data.prices.map(([timestamp, value]: [number, number]) => ({
                    timestamp,
                    value
                })),
                volumes: marketChart.data.total_volumes.map(([timestamp, value]: [number, number]) => ({
                    timestamp,
                    value
                })),
                marketCaps: marketChart.data.market_caps.map(([timestamp, value]: [number, number]) => ({
                    timestamp,
                    value
                })),
                currentPrice: tokenInfo.data.market_data.current_price.usd,
                priceChange24h: tokenInfo.data.market_data.price_change_percentage_24h || 0,
                volume24h: tokenInfo.data.market_data.total_volume.usd,
                marketCap: tokenInfo.data.market_data.market_cap.usd,
                totalSupply: tokenInfo.data.market_data.total_supply,
                maxSupply: tokenInfo.data.market_data.max_supply
            };
        } catch (error) {
            console.error('Error fetching market data:', error);
            throw error;
        }
    }

    private async getOnChainData(address: string): Promise<OnChainData> {
        try {
            const query = `
                query TokenData($address: String!) {
                    token(id: $address) {
                        totalSupply
                        txCount
                        poolCount
                        totalValueLockedUSD
                        derivedETH
                    }
                }
            `;

            const { data } = await this.graphClient.query(query, { address }).toPromise();
            
            if (!data || !data.token) {
                throw new Error('No on-chain data found');
            }

            return {
                ...data.token,
                holdersCount: await this.getHoldersCount(address)
            };
        } catch (error) {
            console.error('Error fetching on-chain data:', error);
            throw error;
        }
    }

    private async getHoldersCount(address: string): Promise<number> {
        try {
            // Vous pouvez utiliser Etherscan API ici si vous avez une clé API
            // Pour l'exemple, on retourne une valeur mock
            return 1000;
        } catch (error) {
            console.error('Error fetching holders count:', error);
            return 0;
        }
    }

    // Méthode utilitaire pour nettoyer le cache
    public clearCache(): void {
        this.cache.clear();
    }
}

export const dataProvider = new TokenDataProvider();