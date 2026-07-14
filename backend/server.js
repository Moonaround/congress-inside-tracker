const express = require('express');
const { execFile } = require('child_process');
const path = require('path');
const axios = require('axios');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;
const HOST = process.env.HOST || '127.0.0.1';

// --- Configuration -------------------------------------------------------
// Real public Congressional disclosure feed (House Stock Watcher S3 dataset).
// Its field names line up 1:1 with what pipeline.py reads: representative,
// ticker, type, amount, disclosure_date. Overridable for tests / alt feeds.
const TRADES_FEED_URL = process.env.TRADES_FEED_URL ||
    'https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json';

// Interpreter that actually has the Python deps installed. Defaults to the
// repo-root virtualenv so the child never falls back to a bare system python3.
const PYTHON_BIN = process.env.PYTHON_BIN ||
    path.join(__dirname, '..', 'venv', 'bin', 'python3');
const PIPELINE_SCRIPT = path.join(__dirname, 'pipeline.py');

app.use(express.json());

// CORS: allow the static frontend (served on :8080 or opened as a file) to
// reach this gateway on :3000 during local development.
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    res.header('Access-Control-Allow-Methods', 'GET, OPTIONS');
    next();
});

app.get('/api/analyze-trades', async (req, res) => {
    try {
        // 1. Pull raw disclosure records from the public database.
        const govRes = await axios.get(TRADES_FEED_URL, { timeout: 15000 });
        const allTrades = Array.isArray(govRes.data) ? govRes.data : [];

        // 2. The raw file is not pre-sorted; order by disclosure date (newest
        //    first) and take the 5 most recent filings.
        const latestTrades = allTrades
            .slice()
            .sort((a, b) => new Date(b.disclosure_date || 0) - new Date(a.disclosure_date || 0))
            .slice(0, 5);

        // 3. Hand the batch to the Python intelligence core. execFile (no shell)
        //    + absolute paths removes the shell-injection surface and the cwd
        //    dependency; the venv interpreter guarantees deps resolve; the child
        //    inherits process.env, so API keys loaded by dotenv reach Python.
        const base64Data = Buffer.from(JSON.stringify(latestTrades)).toString('base64');

        execFile(
            PYTHON_BIN,
            [PIPELINE_SCRIPT, base64Data],
            { maxBuffer: 10 * 1024 * 1024 },
            (error, stdout, stderr) => {
                if (error) {
                    console.error(`Python pipeline crashed: ${stderr || error.message}`);
                    return res.status(500).json({
                        error: 'AI processing pipeline error',
                        details: stderr || error.message,
                    });
                }
                // Guard the parse: a stray warning/traceback on stdout must not
                // throw an uncaught exception and crash the Node process.
                try {
                    res.json(JSON.parse(stdout));
                } catch (parseError) {
                    console.error(`Malformed pipeline output: ${stdout}`);
                    res.status(500).json({
                        error: 'Failed to parse Python engine output',
                        details: String(stdout).slice(0, 500),
                    });
                }
            }
        );
    } catch (err) {
        res.status(500).json({
            error: 'Failed to collect live government transaction feeds',
            details: err.message,
        });
    }
});

app.listen(PORT, HOST, () => console.log(`API Gateway operational on http://${HOST}:${PORT}`));
