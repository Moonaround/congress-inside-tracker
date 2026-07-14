# 🏛️ Congress Insider Trading Sentiment Engine (CITSE)
[![License: MIT](https://shields.io)](LICENSE)
[![Engine: Node.js v20+](https://shields.io)](https://nodejs.org)
[![Model: XGBoost--v2.0](https://shields.io)](https://readthedocs.io)
[![Database: Supabase/Vector](https://shields.io)](https://supabase.com)

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
  │     Python 3.11 Intelligence Core    │
  └─────────────────────────────────────┘
        │                 │                │
        ▼                 ▼                ▼
 ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
 │   Tabular    │ │ Vector Search│ │  LLM Multi-  │
 │ XGBoost Model│ │ (SupabaseDB) │ │ Agent Engine │
 └──────────────┘ └──────────────┘ └──────────────┘
  Feature Matrix   Semantic Bill   Reasoning & NLP
   Risk Scoring    Matching Engine  Summary Synthesis
        │                 │                │
        └─────────────────┼────────────────┘
                          ▼
             [ JSON Output Serialization ]
                          │
                          ▼
            [ Frontend Cyberpunk Terminal ]
```

- **Gateway Service (Node.js/Express)**: Implements high-throughput, non-blocking I/O to interface with the frontend terminal and pull downstream public data pools from Amazon S3 buckets. Handles secure cross-origin resource sharing (CORS) and manages decoupled execution lifecycles.
- **Data Serialization & Processing Core (Python 3.11)**: Runs isolated feature-extraction operations. Unstructured transaction bounds are systematically stripped, tokenized, and transformed into numeric continuous tensors for machine learning processing.
- **Tabular ML Scoring Layer (XGBoost / Scikit-Learn)**: Analyzes statistical risk factors (Transaction Type, Asset Size Band, Politician Committee Assignment History) to output a dynamic, non-linear Suspicion Weight Vector scaled from `1` to `100`.
- **Semantic Mapping Matrix (Supabase Vector / Embeddings)**: Converts active corporate asset tickers and congressional bill scripts into high-dimensional vector embeddings (`text-embedding-3-small`). Executes cosine similarity queries to cross-reference transactions against active legislation hidden behind committee walls.
- **Generative Synthesis Agent (OpenAI/Gemini Orchestrator)**: Injects programmatic system instructions to process the analytical context into clear forensic insights, tracking political trading activities with precision.

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

### 1. Configure the Local Security Vault (`backend/.env`)
Create an encrypted environment variable file inside your local backend workspace:
```ini
PORT=3000
OPENAI_API_KEY=your_production_llm_api_key_here
FINANCIAL_API_KEY=your_live_market_data_feed_api_key
SUPABASE_URL=https://supabase.co
SUPABASE_KEY=your_high_privilege_service_role_database_key
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
The XGBoost model processes the parsed transaction size alongside localized multi-committee categorical mappings. It computes a localized baseline score weighted dynamically by capital risk thresholds:

$$Score = \min\left(100, \lfloor \text{Base} \times \omega \rfloor\right) \quad \text{where} \quad \omega = \begin{cases} 1.5 & \text{if } \text{max\_value} > \$1,000,000 \text{ and Type} = \text{'Purchase'} \\ 1.0 & \text{otherwise} \end{cases}$$

---

## 📜 System Licensing and Legal Frameworks
Distributed under the strict terms of the **MIT Software License Agreement**. Continuous scraping systems must remain compliant with the updated public query limits defined by the official Senate Office of Public Records and the House Financial Disclosures Database guidelines.
