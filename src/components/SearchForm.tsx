import React, { useState } from 'react';
import { Search } from 'lucide-react';

interface SearchFormProps {
  onSubmit: (address: string) => void;
  loading: boolean;
}

export function SearchForm({ onSubmit, loading }: SearchFormProps) {
  const [address, setAddress] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (address.trim()) {
      onSubmit(address.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div className="flex shadow-sm rounded-lg overflow-hidden">
        <input
          type="text"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Enter token address (0x...)"
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
    </form>
  );
}