# 🏛️ Congress Insider Trading Sentiment Engine (CITSE)
[![License: MIT](https://shields.io)](LICENSE)
[![Engine: Node.js v20+](https://shields.io)](https://nodejs.org)
[![LLM: OpenRouter](https://shields.io)](https://openrouter.ai)
[![Vectors: ChromaDB](https://shields.io)](https://www.trychroma.com)

An asynchronous, AI-powered system designed to ingest public Congressional financial disclosure feeds, calculate a composite risk vector using tabular ML scoring models, and perform semantic document correlation against open legislative text.

---

## 🛰️ Core System Architecture Overview

CITSE operates as an asynchronous multi-runtime ingestion and reasoning pipeline designed to scale across heterogeneous microservices:

```text
       [ Public Ingestion Endpoint ] (S3 Raw Data Nodes)
                     │
                     ▼
  ┌─────────────────────────────────────┐
  │      Node.js Express Gateway        │ ──► Low-latency REST Route Handling
  └─────────────────────────────────────┘
                     │ (Subprocess IPC / Base64 Data Packet)
                     ▼
  ┌─────────────────────────────────────┐
  │     Python 3.12 Intelligence Core    │
  └─────────────────────────────────────┘
        │                 │                │
        ▼                 ▼                ▼
 ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
 │  Heuristic   │ │ Vector Search│ │  OpenRouter  │
 │ Score + Data │ │  (ChromaDB)  │ │  LLM Engine  │
 └──────────────┘ └──────────────┘ └──────────────┘
  Suspicion +      Semantic Bill   Reasoning & NLP
  Market Context   Matching Engine  Summary Synthesis
        │                 │                │
        └─────────────────┼────────────────┘
                          ▼
             [ JSON Output Serialization ]
                          │
                          ▼
            [ Frontend Cyberpunk Terminal ]
```

- **Gateway Service (Node.js/Express)**: Implements high-throughput, non-blocking I/O to interface with the frontend terminal and pull downstream public data pools from Amazon S3 buckets. Handles secure cross-origin resource sharing (CORS) and manages decoupled execution lifecycles.
- **Data Serialization & Processing Core (Python 3.12)**: Runs isolated feature-extraction. Unstructured transaction bounds are stripped and parsed into continuous integers for scoring.
- **Suspicion Scoring Layer (log-scaled heuristic)**: Parses the dollar band, log-scales it, and weights purchases above sales (ω = 1.5 for purchases over $1M) to output a non-linear suspicion score from `1` to `100`. Deterministic and dependency-free.
- **Market Context Layer (yfinance + Alpha Vantage)**: Resolves company name, industry, and price via `yfinance`; escalates to Alpha Vantage's `OVERVIEW` endpoint for P/E and precise industry only on high-suspicion (score ≥ 75) targets. Both fail soft.
- **Semantic Mapping Matrix (local ChromaDB vectors)**: Embeds each company's industry classification and congressional bill text with a local sentence-transformer model (all-MiniLM-L6-v2, persisted under `backend/chroma_db/`) and runs a cosine-similarity nearest-neighbour query. Runs fully offline after the first model download — no per-query token cost.
- **Generative Synthesis Agent (OpenRouter via OpenAI SDK)**: Sends the analytical context to a free-tier model (`meta-llama/llama-3.1-8b-instruct:free`) under strict anti-hallucination, score-tiered instructions. Falls back to a deterministic template when no key is configured.

---

## 🛠️ Microservice Directory Blueprint

```text
congress-inside-tracker/
│
├── backend/
│   ├── server.js            # Node.js API Gateway & Subprocess IPC Orchestrator
│   ├── pipeline.py          # Python Core (Feature Extraction, Vector Query, ML Scoring)
│   ├── package.json         # Node.js Core Dependency Tree Manifest
│   ├── requirements.txt     # Python Virtual Environment Native ML Pip Matrix
│   └── .env                 # Local Encrypted Security Vault (Exempt from Remote Tracking)
│
├── frontend/
│   └── index.html           # Self-contained Terminal UI (inline CSS + telemetry JS)
│
├── .gitignore               # Strict Directory Compilation Exclusion Mappings
└── README.md                # Enterprise Structural System Documentation Architecture
```

---

## ⚙️ Enterprise Deployment & Environment Lifecycle Setup

### 1. Configure the Local Environment Vault (`backend/.env`)
Create an environment file inside your local backend workspace. The LLM layer
talks to **OpenRouter** through the OpenAI SDK, so `OPENAI_API_KEY` holds your
OpenRouter key. All keys are optional — the pipeline degrades to deterministic
fallbacks when any is absent.
```ini
PORT=3000
# OpenRouter key (used by the OpenAI SDK). Without it, summaries use a template.
OPENAI_API_KEY=your_openrouter_key_here
AI_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL=meta-llama/llama-3.1-8b-instruct:free
# Alpha Vantage key — only queried for high-suspicion (score >= 75) targets.
FINANCIAL_API_KEY=your_alphavantage_key_here
```

### 2. Launch the Node.js API Gateway Microservice
Initialize your Node execution layer dependencies and bring up the server runtime:
```bash
cd ~/Documents/congress-inside-tracker/backend
npm install
npm start
```

### 3. Initialize the Python Virtual Environment & Native ML Matrix
Open a secondary terminal session, isolate the python runtime version, and build out your model compilation packages:
```bash
cd ~/Documents/congress-inside-tracker/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Execute Frontend Terminal Interface
No compilation overhead required. Simply open `frontend/index.html` inside your Google Chrome instance or host a low-latency local node server using Python:
```bash
cd ~/Documents/congress-inside-tracker/frontend
python3 -m http.server 8080
```
Navigate your browser window to `http://localhost:8080` to interact with the system interface.

---

## 📐 Algorithmic Design Specifications & Core Pipelines

### Data Cleansing & Regular Expression Transformation
The processing engine evaluates incoming asset data bands (`trade['amount']`) containing diverse format string ranges like `"$1,000,001 - $5,000,000"` or `"$15,001 - $50,000"`. The internal module utilizes prioritized substitution functions to clean data without creating excessive string overhead:

$$\text{Continuous Int Matrix} = \max\left(\left[ \text{int}(x) \text{ for } x \text{ in } \text{re.findall}(\text{r'[\d,]+'}, \text{String}) \right]\right)$$

### Non-Linear Suspicion Scoring Formula
The scoring layer log-scales the parsed transaction size into a baseline, then weights it by direction and capital-risk thresholds. With $\text{Base} = 10 \cdot \log_{10}(\text{max\_value})$:

$$Score = \max\left(1,\; \min\left(100, \lfloor \text{Base} \times \omega \rfloor\right)\right) \quad \text{where} \quad \omega = \begin{cases} 1.5 & \text{if } \text{max\_value} \geq \$1{,}000{,}000 \text{ and Type} = \text{'Purchase'} \\ 1.2 & \text{if } \text{Type} = \text{'Purchase'} \\ 1.0 & \text{otherwise} \end{cases}$$

---

## 📜 System Licensing and Legal Frameworks
Distributed under the strict terms of the **MIT Software License Agreement**. Continuous scraping systems must remain compliant with the updated public query limits defined by the official Senate Office of Public Records and the House Financial Disclosures Database guidelines.
