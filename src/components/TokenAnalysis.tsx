import React from 'react';
import { 
  LineChart as Chart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip,
  ResponsiveContainer 
} from 'recharts';
import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';

interface TokenAnalysisProps {
  analysis: any;
}

export function TokenAnalysis({ analysis }: TokenAnalysisProps) {
  const {
    technical_indicators,
    liquidity_analysis,
    risk_metrics,
    trading_signals,
    final_scores
  } = analysis;

  const getScoreColor = (score: number) => {
    if (score >= 0.7) return 'text-green-600';
    if (score >= 0.4) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="mt-8 space-y-6">
      {/* Technical Score */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Technical Analysis Score</h2>
        <div className="flex items-center space-x-4">
          <div className={`text-4xl font-bold ${getScoreColor(final_scores.technical_score)}`}>
            {(final_scores.technical_score * 100).toFixed(1)}%
          </div>
          {final_scores.technical_score >= 0.5 ? (
            <TrendingUp className="h-8 w-8 text-green-500" />
          ) : (
            <TrendingDown className="h-8 w-8 text-red-500" />
          )}
        </div>
      </div>

      {/* Price Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Price Analysis</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <Chart data={technical_indicators.price_history}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="price" 
                stroke="#4f46e5" 
                strokeWidth={2} 
              />
            </Chart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Risk Metrics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Risk Analysis</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-500">Volatility (24h)</div>
            <div className="mt-1 text-xl font-semibold">
              {(risk_metrics.volatility_24h * 100).toFixed(2)}%
            </div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-500">Liquidity Score</div>
            <div className="mt-1 text-xl font-semibold">
              {(liquidity_analysis.depth_score * 100).toFixed(2)}%
            </div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-500">Risk Score</div>
            <div className="mt-1 text-xl font-semibold">
              {(risk_metrics.risk_score * 100).toFixed(2)}%
            </div>
          </div>
        </div>
      </div>

      {/* Trading Signals */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Trading Signals</h2>
        <div className="space-y-4">
          {Object.entries(trading_signals.individual_signals).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="font-medium capitalize">{key}</div>
              <div className={`px-3 py-1 rounded-full ${
                value > 0 ? 'bg-green-100 text-green-800' : 
                value < 0 ? 'bg-red-100 text-red-800' : 
                'bg-yellow-100 text-yellow-800'
              }`}>
                {value > 0 ? 'Buy' : value < 0 ? 'Sell' : 'Hold'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}