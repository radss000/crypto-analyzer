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

// API routes
app.get('/analyze/:address', async (req, res) => {
  // Votre code existant
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