import express from 'express';
import cors from 'cors';
import { PythonShell } from 'python-shell';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const pythonPath = join(__dirname, 'python');

console.log('Server starting...');
console.log('Python path:', pythonPath);

const app = express();
app.use(cors());
app.use(express.json());

app.get('/analyze/:address', async (req, res) => {
  const { address } = req.params;
  const chain = req.query.chain || 'ethereum';
  
  console.log(`\n=== New Analysis Request ===`);
  console.log(`Token: ${address}`);
  console.log(`Chain: ${chain}`);
  
  try {
    const options = {
      mode: 'text',
      pythonPath: 'python3',
      pythonOptions: ['-u'],
      scriptPath: pythonPath,
      args: [address, chain],
      env: {
        ...process.env,
        PYTHONPATH: pythonPath
      }
    };

    const results = await new Promise((resolve, reject) => {
      let jsonOutput = null;
      let debugOutput = [];
      let errorOutput = [];
      
      const pyshell = new PythonShell('analyzer.py', options);

      pyshell.on('message', function (message) {
        try {
          // Essayer de parser le message comme JSON
          const parsed = JSON.parse(message);
          if (parsed.success === false) {
            errorOutput.push(parsed.error);
          } else {
            jsonOutput = parsed;
          }
        } catch (err) {
          debugOutput.push(message);
        }
      });

      pyshell.on('stderr', function (stderr) {
        if (stderr.startsWith('ERROR:')) {
          errorOutput.push(stderr);
        } else if (stderr.startsWith('DEBUG:')) {
          debugOutput.push(stderr);
        }
      });

      pyshell.end(function (err) {
        if (err) {
          reject(new Error(errorOutput.join('\n') || err.message));
        } else if (!jsonOutput) {
          reject(new Error('No valid analysis results received'));
        } else {
          resolve(jsonOutput);
        }
      });
    });

    // Vérifie si les résultats sont valides
    if (!results.success) {
      throw new Error(results.error || 'Analysis failed without specific error');
    }

    res.json(results.data);
  } catch (error) {
    console.error('Analysis failed:', error);
    res.status(500).json({
      error: 'Failed to analyze token',
      details: error.message,
      timestamp: new Date().toISOString()
    });
  }
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