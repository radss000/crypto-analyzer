import express from 'express';
import cors from 'cors';
import { PythonShell } from 'python-shell';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

console.log('Starting server setup...');

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
app.use(cors());
app.use(express.json());

// Configuration des chaînes supportées
const SUPPORTED_CHAINS = {
  ethereum: {
    rpcUrl: 'https://eth-mainnet.g.alchemy.com/v2/your-key',
    explorerUrl: 'https://etherscan.io',
    defaultDex: 'uniswap'
  },
  sui: {
    rpcUrl: 'https://fullnode.mainnet.sui.io',
    explorerUrl: 'https://suiscan.com',
    defaultDex: 'suiswap'
  },
  kaspa: {
    rpcUrl: 'https://api.kaspa.org',
    explorerUrl: 'https://explorer.kaspa.org',
    defaultDex: 'kaspaswap'
  },
  solana: {
    rpcUrl: 'https://api.mainnet-beta.solana.com',
    explorerUrl: 'https://solscan.io',
    defaultDex: 'raydium'
  },
  avalanche: {
    rpcUrl: 'https://api.avax.network/ext/bc/C/rpc',
    explorerUrl: 'https://snowtrace.io',
    defaultDex: 'traderjoe'
  }
};

console.log('Python script path:', join(__dirname, 'python'));

app.get('/analyze/:address', async (req, res) => {
  const chain = req.headers['x-chain']?.toLowerCase() || 'ethereum';
  console.log(`Received analysis request for address: ${req.params.address} on chain: ${chain}`);

  if (!SUPPORTED_CHAINS[chain]) {
    return res.status(400).json({ 
      error: 'Unsupported chain', 
      supported: Object.keys(SUPPORTED_CHAINS) 
    });
  }

  try {
    const { address } = req.params;
    const chainConfig = SUPPORTED_CHAINS[chain];
    
    let options = {
      mode: 'json',
      pythonPath: process.env.PYTHON_PATH || 'python3',
      pythonOptions: ['-u'],
      scriptPath: join(__dirname, 'python'),
      args: [address, chain],
      env: {
        ...process.env,
        PYTHONPATH: join(__dirname, 'python'),
        CHAIN_RPC_URL: chainConfig.rpcUrl,
        CHAIN_EXPLORER_URL: chainConfig.explorerUrl,
        CHAIN_DEFAULT_DEX: chainConfig.defaultDex
      }
    };

    console.log('Starting Python analysis with options:', JSON.stringify({
      ...options,
      env: { ...options.env, CHAIN_RPC_URL: '***hidden***' }
    }, null, 2));

    const results = await new Promise((resolve, reject) => {
      console.log('Creating PythonShell instance...');
      const pyshell = new PythonShell('analyzer.py', options);
      let jsonResult = null;

      pyshell.on('message', function (message) {
        console.log('Received message from Python:', 
          typeof message === 'object' ? JSON.stringify(message) : message);
        try {
          jsonResult = message;
        } catch (err) {
          console.error('Error parsing Python output:', err);
        }
      });

      pyshell.on('stderr', function (stderr) {
        console.log('Python stderr:', stderr);
      });

      pyshell.end(function (err) {
        console.log('Python script ended');
        if (err) {
          console.error('Python script error:', err);
          reject(err);
        } else {
          resolve(jsonResult);
        }
      });
    });

    if (!results) {
      throw new Error('No results received from Python script');
    }

    // Ajouter des métadonnées spécifiques à la chaîne
    const enrichedResults = {
      ...results,
      chain_metadata: {
        name: chain,
        explorer_url: chainConfig.explorerUrl,
        default_dex: chainConfig.defaultDex
      }
    };

    console.log('Analysis completed successfully, sending response');
    res.json(enrichedResults);
  } catch (error) {
    console.error('Analysis error:', error);
    res.status(500).json({ 
      error: 'Failed to analyze token', 
      chain: chain,
      details: error.message 
    });
  }
});

const PORT = process.env.PORT || 3000;

try {
  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });
} catch (error) {
  console.error('Failed to start server:', error);
}