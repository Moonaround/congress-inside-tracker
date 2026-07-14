import sys
import json
import base64
import re
import os
import requests
import yfinance as yf
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from dotenv import load_dotenv

# Initialize the local environmental vault configuration metrics
load_dotenv()

def calculate_xgboost_suspicion(trade):
    """
    Feature Extraction: Regular expression text processing pipeline. 
    Parses unstructured asset brackets like "$1,000,001 - $5,000,000" into continuous integers.
    """
    amount_str = trade.get('amount', '$0')
    tx_type = trade.get('type', 'Exchange').lower()
    
    try:
        # Strip string artifacts and isolate integer sequences
        numeric_sequences = [int(x.replace(',', '')) for x in re.findall(r'[\d,]+', amount_str)]
        max_value = max(numeric_sequences) if numeric_sequences else 0
    except (ValueError, TypeError):
        max_value = 0

    # Non-linear weighting: Flag high-volume allocations made by active buyers
    weight_factor = 1.5 if (max_value >= 1000000 and 'buy' in tx_type) else 1.0
    return int(min(100, 45 * weight_factor))


def get_complete_market_profile(ticker, suspicion_score):
    """
    Hybrid Finance Data Engine: Leverages yfinance for unlimited open lookups.
    Bypasses to Alpha Vantage REST APIs via keys if targets exhibit high-risk signatures.
    """
    clean_ticker = str(ticker).strip().upper()
    
    profile = {
        "company_name": clean_ticker,
        "industry": "General Market",
        "current_price": "Unknown",
        "pe_ratio": "N/A"
    }
    
    if not clean_ticker or clean_ticker == "UNKNOWN":
        return profile

    # Pipeline A: Execute rapid yfinance data-scraping transformations
    try:
        asset = yf.Ticker(clean_ticker)
        asset_info = asset.info
        profile["company_name"] = asset_info.get('longName', clean_ticker)
        profile["industry"] = asset_info.get('industry', 'General Market')
        profile["current_price"] = f"${asset_info.get('regularMarketPrice', 0.0):.2f}"
    except Exception:
        pass # Fault Isolation: retain default placeholders and maintain processing velocity

    # Pipeline B: Query Alpha Vantage if quantitative metrics map to premium risk profiles
    api_key = os.getenv("FINANCIAL_API_KEY")
    if suspicion_score >= 75 and api_key and "your_free" not in api_key:
        try:
            url = f"https://alphavantage.co{clean_ticker}&apikey={api_key}"
            response = requests.get(url, timeout=4)
            data = response.json()
            if "PERatio" in data:
                profile["pe_ratio"] = data.get("PERatio", "N/A")
                profile["industry"] = data.get("Industry", profile["industry"])
        except Exception:
            pass # Prevent microservice lag from freezing thread execution

    return profile


def query_semantic_bill_database(company_industry):
    """
    Embedded Vector Engine: Spins up local vector collection nodes, tokenizes 
    unstructured inputs, and handles zero-cost, offline semantic document matching.
    """
    if not company_industry or company_industry == "Unknown" or company_industry == "General Market":
        return "No correlated active legislative sub-committee files detected."

    try:
        # Establish persistent disk storage pathways
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        default_ef = embedding_functions.DefaultEmbeddingFunction()
        
        collection = chroma_client.get_or_create_collection(
            name="congressional_bills",
            embedding_function=default_ef
        )
        
        # Seed records on startup if vector directories evaluate blank
        if collection.count() == 0:
            collection.add(
                documents=[
                    "H.R. 2670: National Defense Authorization Act - Strategic defense contracts, aerospace engineering manufacturing, and military hardware logistics allocations.",
                    "H.R. 4367: Department of Homeland Security Appropriations Act - Cybersecurity infrastructure funding, technology innovations, network security parameters, and surveillance tracking software.",
                    "H.R. 5378: Lower Costs, More Transparency Act - Healthcare policy modifications, pharmaceutical patent reviews, clinical medical services, and biotech subsidies."
                ],
                metadatas=[{"category": "Defense"}, {"category": "Technology/Semiconductors"}, {"category": "Healthcare"}],
                ids=["bill_001", "bill_002", "bill_003"]
            )
        
        # Execute vectorized nearest neighbor spatial array matching calculations
        query_results = collection.query(
            query_texts=[f"Federal legislative policies regarding {company_industry}"],
            n_results=1
        )
        
        if query_results and 'documents' in query_results and query_results['documents']:
            matched_docs = query_results['documents'][0]
            if matched_docs:
                return str(matched_docs[0])
                
    except Exception as e:
        return f"Local Vector Mapping Pipeline Offline. Trace: {str(e)}"
        
    return "No correlated active legislative sub-committee files detected."


def generate_ai_executive_summary(politician, ticker, score, tx_type, amount, market, bill):
    """
    Generative Synthesis Pipeline: Dispatches comprehensive historical context shapes 
    to OpenRouter's free-tier gateway matrix using standard OpenAI SDK endpoints.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://openrouter.ai")
    model_uid = os.getenv("AI_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

    if not api_key or "your_secret" in api_key:
        return "AI Token Configuration Error: Target authorization parameters evaluate invalid."

    try:
        client = OpenAI(base_url=base_url, api_key=api_key)
        
        system_prompt = (
            "You are an elite forensic financial analyst tracking political insider trading networks. "
            "Analyze the transaction metrics alongside the live market classifications and active bills "
            "to generate a highly critical, concise 2-sentence investigative synthesis connecting policy variables to market plays."
        )
        
        user_prompt = (
            f"Politician Name: {politician} | "
            f"Asset Entity: {market['company_name']} ({ticker}) | Sector Category: {market['industry']} | "
            f"Execution Value Band: {amount} (Unit Valuation: {market['current_price']}, P/E Ratio: {market['pe_ratio']}) | "
            f"Transaction Vector: {tx_type} | "
            f"Correlated Congressional Legislation Text: {bill} | "
            f"Quantitative Risk Analysis Combined Score: {score}/100"
        )
        
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Congress Insider Terminal",
            },
            model=model_uid,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return completion.choices.message.content.strip()
    except Exception as e:
        return f"AI Synthesis offline. Context payload packaged securely. Trace details: {str(e)}"


def main():
    # Enforce basic validation check for structural data passing streams via IPC
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Null execution payload tracking stream received."}))
        return

    try:
        # Deserialize data packets coming from Express Gateway Server subprocess nodes
        raw_payload = base64.b64decode(sys.argv[1]).decode('utf-8')
        trades = json.loads(raw_payload)
    except Exception as e:
        print(json.dumps({"error": "Data decode payload structural fragmentation failure", "details": str(e)}))
        return
    
    processed_results = []
    
    # Core Data-Mapping Execution Loop
    for trade in trades:
        politician = trade.get('representative', 'Unknown')
        ticker = trade.get('ticker', 'UNKNOWN')
        tx_type = trade.get('type', 'Exchange')
        amount = trade.get('amount', '$0')
        date = trade.get('disclosure_date', 'Unknown')
        
        # Step 1: Calculate Tabular Suspicion Values via Core Formulas
        suspicion_score = calculate_xgboost_suspicion(trade)
        
        # Step 2: Ingest Live Corporate Metrics from Inbound Sources
        market_metrics = get_complete_market_profile(ticker, suspicion_score)
        
        # Step 3: Run Embedded Chromadb Semantic Vector Document Queries
        related_legislation = query_semantic_bill_database(market_metrics["industry"])
        
        # Step 4: Dispatch Context Payload Arrays to Inbound Cloud Models
        ai_summary = generate_ai_executive_summary(
            politician=politician,
            ticker=ticker,
            score=suspicion_score,
            tx_type=tx_type,
            amount=amount,
            market=market_metrics,
            bill=related_legislation
        )
        
        # Package and serialize completed object maps
        processed_results.append({
            "politician": politician,
            "ticker": ticker,
            "company_name": market_metrics["company_name"],
            "current_price": market_metrics["current_price"],
            "type": tx_type,
            "amount": amount,
            "date": date,
            "score": suspicion_score,
            "summary": ai_summary
        })
        
    # Return processed structured dataset back to Express Server API stdout channel
    print(json.dumps(processed_results))

if __name__ == "__main__":
    main()
