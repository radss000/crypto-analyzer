// src/services/token.service.ts
import axios from 'axios';

export interface TokenAnalysisResult {
}

class TokenService {
  private readonly API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';

  async analyzeToken(address: string, chain: string = 'ethereum'): Promise<TokenAnalysisResult> {
    try {
      const response = await axios.get<TokenAnalysisResult>(
        `${this.API_URL}/analyze/${address}`,
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
      // error code server 
      const message = error.response.data?.details || error.response.data?.error || 'Analysis failed';
      return new Error(message);
    }
    if (error.request) {
      return new Error('Could not connect to analysis server');
    }
    // other type of error 
    return error;
  }
}

export const tokenService = new TokenService();