import express from 'express';
import cors from 'cors';
import { PythonShell } from 'python-shell';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const pythonPath = join(__dirname, 'python');

console.log('Server starting...');
console.log('Python path:', pythonPath);

const app = express();
app.use(cors({
  origin: [
    'https://crypto-analyzer-w46m2f2mp-radialhsn-gmailcoms-projects.vercel.app',
    'http://localhost:5173'
  ],
  methods: ['GET', 'POST'],
  credentials: true
}));
app.use(express.json());

// Route de vérification de santé
app.get('/health', (req, res) => {
  res.status(200).send('OK');
});

// Test endpoint for Python integration
app.get('/test-python', (req, res) => {
  const options = {
    mode: 'text',
    pythonPath: 'python3',
    scriptPath: pythonPath,
    args: ['test']
  };
  
  PythonShell.run('analyzer.py', options)
    .then(results => {
      res.status(200).json({ 
        success: true, 
        message: 'Python integration works!',
        results: results 
      });
    })
    .catch(err => {
      console.error('Python test failed:', err);
      res.status(500).json({ 
        success: false, 
        error: err.message,
        traceback: err.traceback || 'No traceback available'
      });
    });
});

// API routes
app.get('/analyze/:address', async (req, res) => {
  try {
    const address = req.params.address;
    const chain = req.query.chain || 'ethereum';
    
    console.log(`Analyzing token: ${address} on chain: ${chain}`);
    
    // Options configuration for PythonShell
    const options = {
      mode: 'text',
      pythonPath: 'python3',
      scriptPath: path.join(__dirname, 'python'),
      args: [address, chain]
    };
    
    console.log(`Launching Python with options:`, JSON.stringify(options));
    
    // Call the Python analyzer
    PythonShell.run('analyzer.py', options)
      .then(results => {
        if (!results || results.length === 0) {
          console.error('No results from Python analyzer');
          return res.status(500).json({ error: 'Analysis failed: No results returned' });
        }
        
        console.log('Python output:', results);
        
        // Find the JSON output line from the results
        let resultData = null;
        for (const line of results) {
          try {
            // Fix NaN, Infinity, and -Infinity values which are not valid JSON
            const fixedLine = line
              .replace(/: NaN/g, ': "NaN"')
              .replace(/: Infinity/g, ': "Infinity"')
              .replace(/: -Infinity/g, ': "-Infinity"');
              
            // Try to parse each line as JSON
            const parsed = JSON.parse(fixedLine);
            if (parsed) {
              resultData = parsed;
              break;
            }
          } catch (e) {
            // Skip non-JSON lines silently (these are debug messages)
            continue;
          }
        }
        
        if (!resultData) {
          console.error('Could not find valid JSON in Python output');
          return res.status(500).json({ 
            error: 'Analysis failed: No valid data returned',
            rawOutput: results.join('\n')
          });
        }
        
        if (!resultData.success) {
          console.error('Analysis error:', resultData.error);
          return res.status(400).json({ 
            error: 'Analysis failed', 
            details: resultData.error 
          });
        }
        
        console.log(`Analysis successful for token: ${address}`);
        res.status(200).json(resultData.data);
      })
      .catch(err => {
        console.error('Failed to run Python analyzer:', err);
        res.status(500).json({ 
          error: 'Internal server error during analysis',
          details: err.message
        });
      });
  } catch (error) {
    console.error('Error in /analyze/:address endpoint:', error);
    res.status(500).json({ 
      error: 'Server error',
      details: error.message
    });
  }
});

// Servir les fichiers statiques du build React
app.use(express.static(path.join(__dirname, '../dist')));

// Route fallback pour l'application React (SPA)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../dist/index.html'));
});

const PORT = process.env.PORT || 8000;

const server = app.listen(PORT, () => {
  console.log(`\nServer running on port ${PORT}`);
  console.log(`Ready to analyze tokens...`);
});

server.on('error', (error) => {
  console.error('Server error:', error);
  process.exit(1);
});