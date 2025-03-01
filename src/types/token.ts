// src/types/token.ts

export interface PriceData {
    timestamp: number;
    value: number;
  }
  
  export interface MarketData {
    prices: PriceData[];
    volumes: PriceData[];
    marketCaps: PriceData[];
    currentPrice: number;
    priceChange24h: number;
    volume24h: number;
    marketCap: number;
    totalSupply: number;
    maxSupply: number | null;
  }
  
  export interface OnChainData {
    totalSupply: string;
    holdersCount: number;
    txCount: number;
    poolCount: number;
    totalValueLockedUSD: string;
    derivedETH: string;
  }
  
  export interface TechnicalIndicators {
    RSI: number;
    MACD: {
      macd: number;
      signal: number;
      histogram: number;
    };
    BB: {
      upper: number;
      middle: number;
      lower: number;
    };
    EMA: {
      EMA20: number;
      EMA50: number;
      EMA200: number;
    };
    ADX: number;
  }
  
  export interface TradingSignals {
    recommendation: string;
    buy_signals: number;
    sell_signals: number;
    neutral_signals: number;
    total_signals: number;
  }
  
  export interface RiskMetrics {
    risk_score: number;
    confidence_score: number;
    volatility: number;
  }
  
  export interface TokenAnalysisResult {
    timestamp: string;
    token_address: string;
    chain: string;
    market_data: MarketData;
    technical_analysis?: {
      indicators: TechnicalIndicators;
      signals: TradingSignals;
    };
    risk_metrics?: RiskMetrics;
    on_chain_data?: OnChainData;
  }