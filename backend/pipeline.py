import sys
import json
import base64
import re
import os
import math

import requests
import yfinance as yf
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from dotenv import load_dotenv

# Load the local environment vault (API keys, model overrides).
load_dotenv()

# Anchor the vector store next to this script so it works regardless of the
# process working directory.
CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")

# Values in .env that mean "not configured yet".
PLACEHOLDER_MARKERS = ("your_", "changeme", "sk-your")


def _is_real_key(value):
    if not value:
        return False
    low = value.lower()
    return not any(low.startswith(m) or m in low for m in PLACEHOLDER_MARKERS)


# ------------------------------------------------------------------
# CHALLENGE 1: DATA ENGINEERING & MATH MODELING
# ------------------------------------------------------------------
def calculate_xgboost_suspicion(trade):
    """
    Derive a 1-100 suspicion score from the trade's dollar band and direction.

    1. Extract every integer sequence from the dirty amount string
       ("$1,000,001 - $5,000,000" -> [1000001, 5000000]) and take the maximum.
    2. Log-scale it so each order of magnitude adds a fixed amount rather than
       letting the largest trades dominate linearly ($1k ~30, $1M ~60, $50M ~77).
    3. Weight purchases above sales: a well-timed *buy* ahead of legislation is
       the classic information-advantage signal. Purchases over $1M get the full
       omega = 1.5; smaller purchases 1.2; sales 1.0.
    4. Clamp to [1, 100].
    """
    amount_str = trade.get('amount', '$0') or '$0'
    tx_type = (trade.get('type', 'Exchange') or '').lower()

    try:
        numeric_sequences = [
            int(x.replace(',', '')) for x in re.findall(r'[\d,]+', amount_str) if x.strip(',')
        ]
        max_value = max(numeric_sequences) if numeric_sequences else 0
    except (ValueError, TypeError):
        max_value = 0

    if max_value <= 0:
        return 1

    base = 10 * math.log10(max_value)

    is_purchase = 'purchase' in tx_type or tx_type in ('buy', 'p')
    if is_purchase and max_value >= 1_000_000:
        weight = 1.5
    elif is_purchase:
        weight = 1.2
    else:
        weight = 1.0

    return max(1, min(100, int(base * weight)))


# ------------------------------------------------------------------
# HYBRID MARKET DATA ENGINE
# ------------------------------------------------------------------
def get_complete_market_profile(ticker, suspicion_score):
    """
    Resolve company/industry context for a ticker.

    Pipeline A (always): yfinance for company name, industry, and price.
    Pipeline B (only when score >= 75 and a key is configured): Alpha Vantage
    OVERVIEW for P/E and a more precise industry classification.

    Both pipelines fail soft: any network/parse error leaves the running profile
    intact so a single slow lookup never stalls the batch.
    """
    clean_ticker = str(ticker or '').strip().upper()

    profile = {
        "company_name": clean_ticker or "UNKNOWN",
        "industry": "General Market",
        "current_price": "Unknown",
        "pe_ratio": "N/A",
    }

    if not clean_ticker or clean_ticker == "UNKNOWN":
        return profile

    # Pipeline A: yfinance.
    try:
        asset_info = yf.Ticker(clean_ticker).info or {}
        profile["company_name"] = asset_info.get('longName') or clean_ticker
        profile["industry"] = asset_info.get('industry') or "General Market"
        price = asset_info.get('regularMarketPrice')
        if isinstance(price, (int, float)):
            profile["current_price"] = f"${price:.2f}"
    except Exception:
        pass  # keep defaults, maintain throughput

    # Pipeline B: Alpha Vantage, only for high-risk targets.
    api_key = os.getenv("FINANCIAL_API_KEY")
    if suspicion_score >= 75 and _is_real_key(api_key):
        try:
            url = (
                "https://www.alphavantage.co/query"
                f"?function=OVERVIEW&symbol={clean_ticker}&apikey={api_key}"
            )
            data = requests.get(url, timeout=5).json()
            if isinstance(data, dict) and data.get("PERatio"):
                profile["pe_ratio"] = data.get("PERatio", "N/A")
                profile["industry"] = data.get("Industry") or profile["industry"]
        except Exception:
            pass  # non-fatal: keep yfinance result

    return profile


# ------------------------------------------------------------------
# CHALLENGE 2: OFFLINE SEMANTIC VECTOR REASONING (chromadb)
# ------------------------------------------------------------------
def query_semantic_bill_database(company_industry):
    """
    Match a company's industry to active legislation using a local, persistent
    Chroma vector collection. Keyword search would miss "aerospace subsidies" for
    a defense stock; embeddings capture the semantic link. Seeds a small bill set
    on first run, then returns the nearest bill by vector similarity.

    Note: Chroma's DefaultEmbeddingFunction downloads a small local model on first
    use; after that it runs offline with zero LLM-token cost. Any failure returns
    a graceful, JSON-safe string.
    """
    if not company_industry or company_industry in ("Unknown", "General Market"):
        return "No correlated active legislative sub-committee files detected."

    try:
        chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        default_ef = embedding_functions.DefaultEmbeddingFunction()

        collection = chroma_client.get_or_create_collection(
            name="congressional_bills",
            embedding_function=default_ef,
        )

        if collection.count() == 0:
            collection.add(
                documents=[
                    "H.R. 2670: National Defense Authorization Act - Strategic defense contracts, aerospace engineering manufacturing, and military hardware logistics allocations.",
                    "H.R. 4367: Department of Homeland Security Appropriations Act - Cybersecurity infrastructure funding, technology innovation, network security, and surveillance software.",
                    "H.R. 5378: Lower Costs, More Transparency Act - Healthcare policy, pharmaceutical patent reviews, clinical medical services, and biotech subsidies.",
                    "H.R. 1: Lower Energy Costs Act - Oil, gas, and energy infrastructure permitting, drilling leases, and fossil fuel production.",
                    "H.R. 4346: CHIPS and Science Act - Semiconductor manufacturing incentives, chip fabrication, and advanced computing research.",
                ],
                metadatas=[
                    {"category": "Defense"},
                    {"category": "Technology"},
                    {"category": "Healthcare"},
                    {"category": "Energy"},
                    {"category": "Semiconductors"},
                ],
                ids=["bill_001", "bill_002", "bill_003", "bill_004", "bill_005"],
            )

        query_results = collection.query(
            query_texts=[f"Federal legislative policy regarding {company_industry}"],
            n_results=1,
        )

        documents = (query_results or {}).get('documents') or []
        if documents and documents[0]:
            return str(documents[0][0])
    except Exception as exc:
        return f"Local vector mapping offline. Trace: {exc}"

    return "No correlated active legislative sub-committee files detected."


# ------------------------------------------------------------------
# CHALLENGE 3: GENERATIVE SYNTHESIS (OpenRouter via OpenAI SDK)
# ------------------------------------------------------------------
def generate_ai_executive_summary(politician, ticker, score, tx_type, amount, market, bill):
    """
    Produce a 2-sentence forensic synthesis via OpenRouter's free gateway using
    the OpenAI SDK. Degrades to a deterministic template when no key is set or the
    call fails, so the pipeline always emits valid JSON.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://openrouter.ai/api/v1")
    model_uid = os.getenv("AI_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

    if _is_real_key(api_key):
        try:
            client = OpenAI(base_url=base_url, api_key=api_key)

            system_prompt = (
                "You are a forensic financial analyst reviewing U.S. Congressional "
                "stock-disclosure filings. Use ONLY the facts provided; never invent "
                "dates, dollar amounts, committees, or news. These are legal "
                "disclosures, so describe statistical suspicion, not proven wrongdoing. "
                "If the score is above 80, flag heightened scrutiny and name the driver "
                "(large purchase, legislative overlap); below 30, call it routine. "
                "Respond in exactly 2 concise sentences."
            )
            user_prompt = (
                f"Politician: {politician} | "
                f"Asset: {market['company_name']} ({ticker}) | Sector: {market['industry']} | "
                f"Value band: {amount} (price: {market['current_price']}, P/E: {market['pe_ratio']}) | "
                f"Transaction: {tx_type} | "
                f"Correlated legislation: {bill} | "
                f"Suspicion score: {score}/100"
            )

            completion = client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "http://127.0.0.1:3000",
                    "X-Title": "Congress Insider Terminal",
                },
                model=model_uid,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=200,
            )
            return completion.choices[0].message.content.strip()
        except Exception as exc:
            sys.stderr.write(f"LLM synthesis failed, using fallback: {exc}\n")

    # Deterministic fallback (no key configured or API error).
    if score > 80:
        tier = ("This trade warrants heightened scrutiny, driven by transaction size "
                "and legislative overlap")
    elif score < 30:
        tier = "This trade reads as routine and low-priority"
    else:
        tier = "This trade shows a moderate risk profile"

    return (
        f"{tier}: {politician}'s {tx_type} of {market['company_name']} ({ticker}) "
        f"correlates with {bill} (score {score}/100; no wrongdoing implied)."
    )


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No payload received via IPC stream"}))
        return

    try:
        raw_payload = base64.b64decode(sys.argv[1]).decode('utf-8')
        trades = json.loads(raw_payload)
    except Exception as exc:
        print(json.dumps({"error": f"Payload decode failure: {exc}"}))
        return

    processed_results = []

    for trade in trades:
        try:
            politician = trade.get('representative', 'Unknown')
            ticker = trade.get('ticker', 'UNKNOWN')
            tx_type = trade.get('type', 'Exchange')
            amount = trade.get('amount', '$0')
            date = trade.get('disclosure_date', 'Unknown')

            suspicion_score = calculate_xgboost_suspicion(trade)
            market = get_complete_market_profile(ticker, suspicion_score)
            bill = query_semantic_bill_database(market['industry'])
            ai_text = generate_ai_executive_summary(
                politician, ticker, suspicion_score, tx_type, amount, market, bill
            )

            processed_results.append({
                "politician": politician,
                "ticker": ticker,
                "type": tx_type,
                "amount": amount,
                "date": date,
                "score": suspicion_score,
                "company": market['company_name'],
                "industry": market['industry'],
                "bill": bill,
                "summary": ai_text,
            })
        except Exception as exc:
            # Per-record fault isolation: one bad trade never sinks the batch.
            processed_results.append({
                "politician": trade.get('representative', 'Unknown'),
                "ticker": trade.get('ticker', 'UNKNOWN'),
                "type": trade.get('type', 'Exchange'),
                "amount": trade.get('amount', '$0'),
                "date": trade.get('disclosure_date', 'Unknown'),
                "score": 0,
                "summary": f"Record processing error: {exc}",
            })

    # Serialize the processed dataset back to Node.js via stdout.
    print(json.dumps(processed_results))


if __name__ == "__main__":
    main()
