// src/services/token.service.ts

import axios from 'axios';

export interface TokenAnalysisResult {
  timestamp: string;
  token_address: string;
  chain: string;
  market_data: {
    current_price: number;
    volume_24h: number;
    liquidity: number;
    price_change_24h: number;
    market_cap: number;
    buy_sell_ratio: number;
  };
  technical_analysis?: {
    indicators: {
      RSI: number;
      MACD: {
        macd: number;
        signal: number;
        hist: number;
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
    };
    signals: {
      recommendation: string;
      buy_signals: number;
      sell_signals: number;
      neutral_signals: number;
      total_signals: number;
    };
  };
  risk_metrics?: {
    risk_score: number;
    confidence_score: number;
    volatility: number;
  };
  note?: string;
}

class TokenService {
  VITE_API_URL = 'VITE_API_URL';

  async analyzeToken(address: string, chain: string = 'ethereum'): Promise<TokenAnalysisResult> {
    try {
      const response = await axios.get<TokenAnalysisResult>(
        `${this.VITE_API_URL}/analyze/${address}`,
        {
          params: { chain }
        }
      );

      return response.data;
    } catch (error) {
      console.error('Failed to analyze token:', error);
      throw this.handleError(error);
    }
  }

  private handleError(error: any): Error {
    if (error.response) {
      // Le serveur a répondu avec un code d'erreur
      const message = error.response.data?.details || error.response.data?.error || 'Analysis failed';
      return new Error(message);
    }
    if (error.request) {
      // La requête a été faite mais pas de réponse
      return new Error('Could not connect to analysis server');
    }
    // Autre type d'erreur
    return error;
  }
}

export const tokenService = new TokenService();