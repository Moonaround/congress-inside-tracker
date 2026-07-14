import sys
import json
import base64
import numpy as np

# ------------------------------------------------------------------
# CHALLENGE 1: DATA ENGINEERING & MATH MODELING
# ------------------------------------------------------------------
def calculate_xgboost_suspicion(trade):
    """
    ENGINEERING MISSION:
    You need to write a scoring algorithm here that replaces this static placeholder.
    Think about how to calculate a risk value between 1 and 100 based on these fields:
      - trade['amount']: Value ranges like "$1,001-$15,000" or "$1,000,001-$5,000,000"
      - trade['type']: 'purchase' (buy) or 'sale_full' (sell)
      
    DEEP THINKING QUESTIONS:
    1. How will you clean the string trade['amount'] to extract a single maximum number? 
       (e.g., Turning "$1,000,001 - $5,000,000" into the number 5000000).
    2. Why should a 'purchase' (buy) order receive a higher initial suspicion score 
       than a 'sale_full' (sell) order during market shifts?
    3. How will you normalize the scale so the final score never goes below 1 or above 100?
    """
    # WRITE YOUR DATA EXTRACTION AND MATHEMATICAL CODES HERE
    
    simulated_score = 45 # Replace this with your dynamic mathematical calculation
    return simulated_score


# ------------------------------------------------------------------
# CHALLENGE 2: INTEGRATING THE VECTOR REASONING PIPELINE
# ------------------------------------------------------------------
def query_semantic_bill_database(ticker):
    """
    ENGINEERING MISSION:
    This function must query a database containing thousands of active Congressional bills.
    We want to check if the company being traded matches any laws currently being debated.
    
    DEEP THINKING QUESTIONS:
    1. If a politician buys Lockheed Martin (LMT) but a bill only textually references 
       "aerospace manufacturing subsidies", standard keyword searching will miss it completely. 
       How do Vector Embeddings solve this semantic matching challenge?
    2. Write an imaginary layout schema for your database table. What columns do you need to store?
    """
    # WRITE YOUR VECTOR DATABASE HOOKS OR MOCK SCHEMAS HERE
    
    matched_bill = "H.R. 4367: Department of Homeland Security Appropriations Act"
    return matched_bill


# ------------------------------------------------------------------
# CHALLENGE 3: PROMPT ENGINEERING & LLM REASONING
# ------------------------------------------------------------------
def generate_ai_executive_summary(politician, ticker, score, bill):
    """
    ENGINEERING MISSION:
    You must construct a highly detailed instruction system prompt for an LLM (like GPT-4).
    The prompt must force the AI to behave like a financial forensic investigator.
    
    DEEP THINKING QUESTIONS:
    1. If the AI doesn't know the answer, it can hallucinate fake stories. What strict negative 
       constraints will you add to the prompt to force the model to stay grounded in facts?
    2. How would you instruct the model to analyze the trade if the calculated suspicion score is 
       over 80 versus under 30?
    """
    # WRITE YOUR STRING PROMPT SYSTEM SYSTEM TEMPLATE HERE
    
    simulated_summary = f"AI Analysis complete. High correlation detected with active bill: {bill}."
    return simulated_summary


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No payload received"}))
        return

    # Decode data from backend
    raw_payload = base64.b64decode(sys.argv[1]).decode('utf-8')
    trades = json.loads(raw_payload)
    
    processed_results = []
    
    for trade in trades:
        politician = trade.get('representative', 'Unknown')
        ticker = trade.get('ticker', 'UNKNOWN')
        tx_type = trade.get('type', 'Exchange')
        amount = trade.get('amount', '$0')
        date = trade.get('disclosure_date', 'Unknown')
        
        # Execute your engineering pipelines
        suspicion_score = calculate_xgboost_suspicion(trade)
        related_legislation = query_semantic_bill_database(ticker)
        ai_text = generate_ai_executive_summary(politician, ticker, suspicion_score, related_legislation)
        
        processed_results.append({
            "politician": politician,
            "ticker": ticker,
            "type": tx_type,
            "amount": amount,
            "date": date,
            "score": suspicion_score,
            "summary": ai_text
        })
        
    # Return processed dataset back to Node.js server via standard system output stream
    print(json.dumps(processed_results))

if __name__ == "__main__":
    main()
