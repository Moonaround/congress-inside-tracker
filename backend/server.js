const express = require('express');
const { exec } = require('child_process');
const axios = require('axios');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

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
        const govRes = await axios.get('https://amazonaws.com');
        const latestTrades = govRes.data.slice(0, 5); // Grab the 5 newest files

        // Execute the python intelligence script, passing the data as a string argument
        const base64Data = Buffer.from(JSON.stringify(latestTrades)).toString('base64');
        
        exec(`python3 pipeline.py "${base64Data}"`, (error, stdout, stderr) => {
            if (error) {
                return res.status(500).json({ error: "AI Script execution failed", details: stderr });
            }
            // Parse and return the final AI analyzed array back to user screen
            res.json(JSON.parse(stdout));
        });
    } catch (err) {
        res.status(500).json({ error: "Failed to collect live government trade feeds" });
    }
});

app.listen(PORT, () => console.log(`API Gateway operational on http://localhost:${PORT}`));
