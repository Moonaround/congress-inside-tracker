const express = require('express');
const { exec } = require('child_process');
const axios = require('axios');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// FIXED: Robust CORS middleware allowing any local development port to fetch data
app.use((req, res, next) => {
    res.header("Access-Control-Allow-Origin", "*");
    res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
    next();
});

app.get('/api/analyze-trades', async (req, res) => {
    try {
        // Fetch real data from the House public records pipeline
        const govRes = await axios.get('https://amazonaws.com');
        const latestTrades = govRes.data.slice(0, 5); // Process the top 5 newest filings

        const base64Data = Buffer.from(JSON.stringify(latestTrades)).toString('base64');
        
        // FIXED: Using explicit python3 execution to bridge your local venv environments smoothly
        exec(`python3 pipeline.py "${base64Data}"`, (error, stdout, stderr) => {
            if (error) {
                console.error(`Python script crash error: ${stderr}`);
                return res.status(500).json({ error: "AI Processing pipeline error", details: stderr });
            }
            try {
                res.json(JSON.parse(stdout));
            } catch (parseError) {
                res.status(500).json({ error: "Failed to parse Python engine output data payload stream." });
            }
        });
    } catch (err) {
        res.status(500).json({ error: "Failed to collect live government transaction data feeds." });
    }
});

app.listen(PORT, () => console.log(`API Gateway operational on http://127.0.0.1:${PORT}`));
