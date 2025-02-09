app.get('/analyze/:address', async (req, res) => {
  const { address } = req.params;
  const chain = req.query.chain || 'ethereum';
  
  console.log(`Received analysis request for address: ${address} on chain: ${chain}`);
  
  try {
    let options = {
      mode: 'json',
      pythonPath: 'python3',
      pythonOptions: ['-u'],
      scriptPath: pythonPath,
      args: [address, chain],
      env: {
        ...process.env,
        PYTHONPATH: pythonPath
      }
    };

    console.log('Starting Python analysis...');

    const results = await new Promise((resolve, reject) => {
      let jsonResult = null;
      let errorOutput = [];
      
      const pyshell = new PythonShell('analyzer.py', options);

      pyshell.on('message', function (message) {
        console.log('Received message from Python:', message);
        jsonResult = message;
      });

      pyshell.on('stderr', function (stderr) {
        console.log('Python stderr:', stderr);
        errorOutput.push(stderr);
      });

      pyshell.end(function (err) {
        if (err) {
          console.error('Python script error:', err);
          reject(err);
        } else if (!jsonResult) {
          reject(new Error('No results received from Python script'));
        } else {
          resolve(jsonResult);
        }
      });
    });

    res.json(results);
  } catch (error) {
    console.error('Analysis error:', error);
    res.status(500).json({
      error: 'Failed to analyze token',
      details: error.message,
      chain: chain
    });
  }
});