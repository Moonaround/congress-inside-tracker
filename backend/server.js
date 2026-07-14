const express = require('express');
const { execFile } = require('child_process');
const path = require('path');
const axios = require('axios');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Public Congressional disclosure feed (House Stock Watcher S3 dataset). The
// field names line up with what pipeline.py reads: representative, ticker,
// type, amount, disclosure_date. Overridable for testing / alternate feeds.
const TRADES_FEED_URL = process.env.TRADES_FEED_URL ||
    'https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json';

// Interpreter that has the Python deps installed. Defaults to the repo-root venv.
const PYTHON_BIN = process.env.PYTHON_BIN ||
    path.join(__dirname, '..', 'venv', 'bin', 'python3');
const PIPELINE_SCRIPT = path.join(__dirname, 'pipeline.py');

app.use(express.json());

// Enable safe communication across ports
app.use((req, res, next) => {
    res.header("Access-Control-Allow-Origin", "*");
    res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
    next();
});

// Endpoint that gets raw trade feeds and pipes them directly through the Python AI Core
app.get('/api/analyze-trades', async (req, res) => {
    try {
        // Fetch raw disclosure records from the public database
        const govRes = await axios.get(TRADES_FEED_URL);
        const allTrades = Array.isArray(govRes.data) ? govRes.data : [];

        // The raw feed is not pre-sorted; order by disclosure date (newest first)
        // and take the 5 most recent records.
        const latestTrades = allTrades
            .slice()
            .sort((a, b) => new Date(b.disclosure_date || 0) - new Date(a.disclosure_date || 0))
            .slice(0, 5);

        // Execute the python intelligence script, passing the data as a base64 argument.
        // execFile (no shell) + absolute paths avoid shell injection and cwd surprises;
        // the child inherits process.env, so OPENAI_API_KEY (loaded by dotenv) reaches it.
        const base64Data = Buffer.from(JSON.stringify(latestTrades)).toString('base64');

        execFile(PYTHON_BIN, [PIPELINE_SCRIPT, base64Data], (error, stdout, stderr) => {
            if (error) {
                return res.status(500).json({ error: "AI Script execution failed", details: stderr || error.message });
            }
            // Parse and return the final AI analyzed array. Guard against non-JSON
            // stdout (a stray warning or traceback) so a bad parse returns 500
            // instead of throwing an uncaught exception that crashes the server.
            try {
                res.json(JSON.parse(stdout));
            } catch (parseErr) {
                res.status(500).json({ error: "AI Script returned malformed output", details: stdout });
            }
        });
    } catch (err) {
        res.status(500).json({ error: "Failed to collect live government trade feeds", details: err.message });
    }
});

app.listen(PORT, () => console.log(`API Gateway operational on http://localhost:${PORT}`));
