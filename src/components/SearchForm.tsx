import React, { useState } from 'react';
import { Search } from 'lucide-react';

interface SearchFormProps {
  onSubmit: (address: string, chain: string) => void;
  loading: boolean;
}

// Liste des chaînes supportées avec leurs formats d'adresse
const SUPPORTED_CHAINS = {
  ethereum: {
    name: 'Ethereum',
    format: '0x...',
    placeholder: '0x2260fac...',
    validate: (address: string) => address.startsWith('0x') && address.length === 42
  },
  sui: {
    name: 'SUI',
    format: '0x...',
    placeholder: '0x123...',
    validate: (address: string) => address.startsWith('0x')
  },
  kaspa: {
    name: 'Kaspa',
    format: 'kaspa:...',
    placeholder: 'kaspa:abc...',
    validate: (address: string) => address.startsWith('kaspa:')
  },
  solana: {
    name: 'Solana',
    format: '...',
    placeholder: 'Enter Solana address',
    validate: (address: string) => true // Ajouter validation spécifique
  },
  avalanche: {
    name: 'Avalanche',
    format: '0x...',
    placeholder: '0x...',
    validate: (address: string) => address.startsWith('0x') && address.length === 42
  }
};

export function SearchForm({ onSubmit, loading }: SearchFormProps) {
  const [address, setAddress] = useState('');
  const [chain, setChain] = useState('ethereum');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const chainConfig = SUPPORTED_CHAINS[chain as keyof typeof SUPPORTED_CHAINS];
    
    if (!address.trim()) {
      setError('Please enter an address');
      return;
    }

    if (!chainConfig.validate(address.trim())) {
      setError(`Invalid address format for ${chainConfig.name}. Expected format: ${chainConfig.format}`);
      return;
    }

    setError('');
    onSubmit(address.trim(), chain);
  };

  const handleChainChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setChain(e.target.value);
    setAddress(''); // Reset address when chain changes
    setError('');
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto space-y-4">
      <div className="flex flex-col sm:flex-row gap-4">
        <select
          value={chain}
          onChange={handleChainChange}
          className="px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500
                   bg-white sm:w-48"
          disabled={loading}
        >
          {Object.entries(SUPPORTED_CHAINS).map(([value, { name }]) => (
            <option key={value} value={value}>{name}</option>
          ))}
        </select>

        <div className="flex-1 flex shadow-sm rounded-lg overflow-hidden">
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder={SUPPORTED_CHAINS[chain as keyof typeof SUPPORTED_CHAINS].placeholder}
            className="flex-1 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 border-0"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !address.trim()}
            className="px-6 py-3 bg-indigo-600 text-white font-medium hover:bg-indigo-700 
                     disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            <Search className="h-5 w-5 mr-2" />
            Analyze
          </button>
        </div>
      </div>

      {error && (
        <div className="text-red-600 text-sm mt-2">{error}</div>
      )}
    </form>
  );
}