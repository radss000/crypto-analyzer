import React from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  AlertCircle,
  Activity,
  BarChart2,
  DollarSign
} from 'lucide-react';

interface TokenAnalysisProps {
  analysis: any;
}

export function TokenAnalysis({ analysis }: TokenAnalysisProps) {
  const {
    market_data,
    technical_analysis,
    risk_metrics
  } = analysis;

  const getScoreColor = (score: number) => {
    if (score >= 0.7) return 'text-green-600';
    if (score >= 0.4) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  return (
    <div className="mt-8 space-y-6">
      {/* Market Overview */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <DollarSign className="h-6 w-6 mr-2"/>
          Market Overview
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-500">Current Price</div>
            <div className="mt-1 text-xl font-semibold">{formatCurrency(market_data.current_price)}</div>
            <div className={`text-sm ${market_data.price_change_24h >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {market_data.price_change_24h}%
            </div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-500">24h Volume</div>
            <div className="mt-1 text-xl font-semibold">{formatCurrency(market_data.volume_24h)}</div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-500">Liquidity</div>
            <div className="mt-1 text-xl font-semibold">{formatCurrency(market_data.liquidity)}</div>
          </div>
        </div>
      </div>

      {/* Technical Analysis */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Activity className="h-6 w-6 mr-2"/>
          Technical Analysis
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-500">RSI</div>
            <div className="mt-1 text-xl font-semibold">
              {technical_analysis?.indicators?.RSI.toFixed(2)}
            </div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-500">Overall Recommendation</div>
            <div className={`mt-1 text-xl font-semibold ${
              technical_analysis?.summary?.recommendation === 'BUY' ? 'text-green-600' :
              technical_analysis?.summary?.recommendation === 'SELL' ? 'text-red-600' :
              'text-yellow-600'
            }`}>
              {technical_analysis?.summary?.recommendation}
            </div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-500">Signal Strength</div>
            <div className="mt-1">
              <div className="flex justify-between text-sm">
                <span className="text-green-600">Buy: {technical_analysis?.summary?.buy_signals}</span>
                <span className="text-red-600">Sell: {technical_analysis?.summary?.sell_signals}</span>
                <span className="text-gray-600">Neutral: {technical_analysis?.summary?.neutral_signals}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Analysis */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <BarChart2 className="h-6 w-6 mr-2"/>
          Risk Analysis
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-500">Risk Score</div>
            <div className={`mt-1 text-xl font-semibold ${getScoreColor(risk_metrics.risk_score)}`}>
              {(risk_metrics.risk_score * 100).toFixed(1)}%
            </div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-500">Confidence Score</div>
            <div className={`mt-1 text-xl font-semibold ${getScoreColor(risk_metrics.confidence_score)}`}>
              {(risk_metrics.confidence_score * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {/* Transaction Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">24h Transaction Activity</h2>
        <div className="flex space-x-4">
          <div className="flex-1 p-4 bg-green-50 rounded-lg">
            <div className="text-sm text-gray-500">Buys</div>
            <div className="mt-1 text-xl font-semibold text-green-600">
              {market_data.transactions_24h.buys}
            </div>
          </div>
          <div className="flex-1 p-4 bg-red-50 rounded-lg">
            <div className="text-sm text-gray-500">Sells</div>
            <div className="mt-1 text-xl font-semibold text-red-600">
              {market_data.transactions_24h.sells}
            </div>
          </div>
          <div className="flex-1 p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-500">Buy/Sell Ratio</div>
            <div className="mt-1 text-xl font-semibold">
              {market_data.transactions_24h.buy_sell_ratio.toFixed(2)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}