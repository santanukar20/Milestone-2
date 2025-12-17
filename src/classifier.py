import os
import json
import time
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")
genai.configure(api_key=api_key)

# ✅ SAFE MODEL: Using Gemini 2.5 Flash Lite to avoid quota exhaustion
MODEL_NAME = "gemini-2.5-flash-lite"
FALLBACK_MODEL = "gemini-2.0-flash-lite-preview"

def classify_batch_reviews(reviews_list, themes):
    """
    Classify multiple reviews in a SINGLE API call using batch processing.
    This reduces API calls from 39 to just 1-2 calls.
    """
    # Format reviews for batch processing
    reviews_formatted = "\n".join([f'{i+1}. "{r}"' for i, r in enumerate(reviews_list)])
    
    prompt = f"""
    You are a review analyst. Classify each review into ONE category from: {', '.join(themes)}
    
    Reviews to classify:
    {reviews_formatted}
    
    Return a JSON array where each item has "review_id" (1-based) and "theme" (the category).
    Example: {{"review_id": 1, "theme": "App Performance"}}
    
    Return ONLY valid JSON array, no other text.
    """
    
    tried_fallback = False
    current_model = MODEL_NAME
    while True:
        try:
            model = genai.GenerativeModel(current_model)
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            # Clean up potential markdown formatting
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            classifications_data = json.loads(result_text)
            
            # Extract classifications in order
            classifications = []
            for item in classifications_data:
                theme = item.get("theme", "General Sentiment")
                # Validate theme
                if not any(t.lower() in theme.lower() for t in themes):
                    theme = "General Sentiment"
                classifications.append(theme)
            
            return classifications
        except Exception as e:
            err_str = str(e).lower()
            # If model not found or unsupported, try fallback once
            if (not tried_fallback) and ("not found" in err_str or "not supported" in err_str or "404" in err_str):
                tried_fallback = True
                current_model = FALLBACK_MODEL
                print(f"   Model {MODEL_NAME} not available; retrying with fallback {FALLBACK_MODEL}...")
                continue
            print(f"   ❌ AI Error: {e}")
            # Fallback: return all as "General Sentiment"
            return ["General Sentiment"] * len(reviews_list)

def classify_reviews(input_csv, output_csv):
    print(f"--- Layer 2: Classifying (Using {MODEL_NAME}) with Batch Processing ---")
    if not os.path.exists(input_csv): 
        print(f"Error: {input_csv} not found")
        return
    
    df = pd.read_csv(input_csv)
    reviews_to_process = df.copy() 
    
    if reviews_to_process.empty:
        print("No reviews to classify")
        return
    
    print(f"Processing {len(reviews_to_process)} reviews using batch API calls...")
    
    theme_names = ["Order Execution", "Payments/Money", "App Performance", "Onboarding/KYC", 
                   "Charges/Policy", "Missing or Requested Features", "Customer Support", 
                   "UI/UX", "General Sentiment"]
    
    # Split reviews into batches of 10 to avoid token limits
    BATCH_SIZE = 10
    all_classifications = []
    
    for batch_start in range(0, len(reviews_to_process), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(reviews_to_process))
        batch_reviews = reviews_to_process['content'].iloc[batch_start:batch_end].tolist()
        
        print(f"   Processing batch {batch_start//BATCH_SIZE + 1} ({batch_start+1}-{batch_end}/{len(reviews_to_process)})...")
        
        # Classify entire batch in ONE API call
        batch_classifications = classify_batch_reviews(batch_reviews, theme_names)
        all_classifications.extend(batch_classifications)
        
        # Small delay between batches to respect rate limits
        if batch_end < len(reviews_to_process):
            print(f"   Waiting 2s before next batch...")
            time.sleep(2)
    
    reviews_to_process['operational_bucket'] = all_classifications
    reviews_to_process.to_csv(output_csv, index=False)
    print(f"✅ Saved to {output_csv}")
    print(f"Theme Distribution:\n{reviews_to_process['operational_bucket'].value_counts()}")

if __name__ == "__main__":
    classify_reviews("groww_relevant_reviews.csv", "weekly_classified.csv")