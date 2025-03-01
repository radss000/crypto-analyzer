// src/App.tsx

import React, { useState } from 'react';
import { LineChart, AlertTriangle, Loader2 } from 'lucide-react';
import { TokenAnalysis } from './components/TokenAnalysis';
import { SearchForm } from './components/SearchForm';
import { tokenService, type TokenAnalysisResult } from './services/token.service';

function App() {
  const [analysis, setAnalysis] = useState<TokenAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAnalyze = async (address: string) => {
    setLoading(true);
    setError('');
    try {
      const result = await tokenService.analyzeToken(address);
      console.log('Analysis data:', result);
      setAnalysis(result);
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err instanceof Error ? err.message : 'Failed to analyze token');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center space-x-2">
            <LineChart className="h-8 w-8 text-indigo-600" />
            <h1 className="text-2xl font-bold text-gray-900">Crypto Analyzer</h1>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <SearchForm 
          onSubmit={handleAnalyze}
          loading={loading}
        />

        {error && (
          <div className="mt-4 p-4 bg-red-50 rounded-lg flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {loading && (
          <div className="mt-8 flex justify-center">
            <Loader2 className="h-8 w-8 text-indigo-600 animate-spin" />
          </div>
        )}

        {analysis && !loading && (
          <TokenAnalysis analysis={analysis} />
        )}
      </main>
    </div>
  );
}

export default App;