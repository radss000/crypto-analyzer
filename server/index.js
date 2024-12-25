import express from 'express';
import cors from 'cors';
import { PythonShell } from 'python-shell';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
app.use(cors());
app.use(express.json());

app.get('/analyze/:address', async (req, res) => {
  try {
    const { address } = req.params;
    
    let options = {
      mode: 'json',
      pythonPath: 'python3',
      pythonOptions: ['-u'],
      scriptPath: join(__dirname, 'python'),
      args: [address]
    };

    const results = await new Promise((resolve, reject) => {
      PythonShell.run('analyzer.py', options, (err, results) => {
        if (err) reject(err);
        resolve(results[0]); // Get the first result since we're expecting a single JSON object
      });
    });

    res.json(results);
  } catch (error) {
    console.error('Analysis error:', error);
    res.status(500).json({ error: 'Failed to analyze token' });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});