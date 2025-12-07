import os
import time
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ SAFE MODEL: Using the alias from your logs
MODEL_NAME = "gemini-flash-latest"

def classify_single_review(text, themes):
    prompt = f"""
    Analyze this review. Assign it to exactly ONE category: {', '.join(themes)}
    Review: "{text}"
    Reply ONLY with the category name.
    """
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        category = response.text.strip()
        for theme in themes:
            if theme.lower() in category.lower(): return theme
        return "General Sentiment"
    except Exception as e:
        print(f"   ❌ AI Error: {e}")
        return "General Sentiment"

def classify_reviews(input_csv, output_csv):
    print(f"--- Layer 2: Classifying (Using {MODEL_NAME}) ---")
    if not os.path.exists(input_csv): return
    
    df = pd.read_csv(input_csv)
    # Process ALL reviews
    reviews_to_process = df.copy() 
    print(f"Processing {len(reviews_to_process)} reviews...")
    
    theme_names = ["Order Execution", "Payments/Money", "App Performance", "Onboarding/KYC", 
                   "Charges/Policy", "Missing or Requested Features", "Customer Support", 
                   "UI/UX", "General Sentiment"]
    
    classifications = []
    for i, row in reviews_to_process.iterrows():
        classifications.append(classify_single_review(row['content'], theme_names))
        # ✅ CRITICAL: 15-second pause to stay within free tier limits (5 requests/min = 1 every 12s)
        print(f"   Review {i+1}/{len(reviews_to_process)}: Waiting 15s to respect API limits...")
        time.sleep(15)

    reviews_to_process['operational_bucket'] = classifications
    reviews_to_process.to_csv(output_csv, index=False)
    print(f"✅ Saved to {output_csv}")

if __name__ == "__main__":
    classify_reviews("groww_relevant_reviews.csv", "weekly_classified.csv")