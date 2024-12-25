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

console.log('Python script path:', join(__dirname, 'python'));

app.get('/analyze/:address', async (req, res) => {
  console.log('Received analysis request for address:', req.params.address);
  try {
    const { address } = req.params;
    
    let options = {
      mode: 'json',
      pythonPath: 'python3',
      pythonOptions: ['-u'],
      scriptPath: join(__dirname, 'python'),
      args: [address],
      env: {
        ...process.env,
        PYTHONPATH: join(__dirname, 'python')
      }
    };

    console.log('Starting Python analysis...');

    const results = await new Promise((resolve, reject) => {
      console.log('Creating PythonShell instance...');
      const pyshell = new PythonShell('analyzer.py', options);
      let jsonResult = null;

      pyshell.on('message', function (message) {
        console.log('Received message from Python:', message);
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

    console.log('Analysis completed successfully, sending response');
    res.json(results);
  } catch (error) {
    console.error('Analysis error:', error);
    res.status(500).json({ error: 'Failed to analyze token', details: error.message });
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