import React, { useState } from 'react';
import { LineChart, AlertTriangle, Loader2 } from 'lucide-react';
import { TokenAnalysis } from './components/TokenAnalysis';
import { SearchForm } from './components/SearchForm';

interface Analysis {
  market_data: any;
  technical_analysis: any;
  risk_metrics: any;
  chain_specific?: any;
  error?: string;
}

function App() {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [debugInfo, setDebugInfo] = useState('');
  const [currentChain, setCurrentChain] = useState('');

  const handleAnalyze = async (address: string, chain: string) => {
    setLoading(true);
    setError('');
    setDebugInfo('');
    setCurrentChain(chain);
    
    try {
      console.log(`Starting analysis for address: ${address} on chain: ${chain}`);
      setDebugInfo(prev => prev + `\nStarting request for ${chain}...`);
      
      const response = await fetch(`http://localhost:3000/analyze/${address}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'X-Chain': chain
        }
      });
      
      setDebugInfo(prev => prev + `\nResponse status: ${response.status}`);
      
      const data = await response.json();
      setDebugInfo(prev => prev + '\nReceived data: ' + JSON.stringify(data, null, 2));
      
      if (!response.ok) {
        throw new Error(data.error || 'Analysis failed');
      }
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      console.log('Analysis data:', data);
      setAnalysis(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      console.error('Analysis error:', err);
      setError(`Analysis failed: ${errorMessage}`);
      setDebugInfo(prev => prev + '\nError: ' + errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <LineChart className="h-8 w-8 text-indigo-600" />
              <h1 className="text-2xl font-bold text-gray-900">Multi-Chain Crypto Analyzer</h1>
            </div>
            {currentChain && (
              <div className="text-sm text-gray-600">
                Current Chain: <span className="font-semibold">{currentChain.toUpperCase()}</span>
              </div>
            )}
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

        {debugInfo && (
          <div className="mt-4 p-4 bg-gray-100 rounded-lg">
            <h3 className="font-semibold mb-2">Debug Information:</h3>
            <pre className="whitespace-pre-wrap text-sm">{debugInfo}</pre>
          </div>
        )}

        {loading && (
          <div className="mt-8 flex justify-center">
            <Loader2 className="h-8 w-8 text-indigo-600 animate-spin" />
          </div>
        )}

        {analysis && !loading && (
          <TokenAnalysis 
            analysis={analysis} 
            chain={currentChain}
          />
        )}
      </main>
    </div>
  );
}

export default App;