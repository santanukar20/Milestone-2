import pandas as pd
import random
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# --- Configuration for Phase 2 (Operational Buckets) ---
CSV_FILE = 'groww_relevant_reviews.csv'
LAYER2_OUTPUT_CSV_FILE = 'groww_reviews_operational_buckets.csv' # New output file name
EMBEDDING_DIM = 768 # Standard embedding dimension, adjust if needed

# --- Operational Buckets & Prioritization Logic ---
OPERATIONAL_BUCKETS = {
    "Order Execution": {
        "keywords": ["buy", "sell", "trade", "stop-loss", "order", "market timing", "stuck", "price not updated", "wrong candle", "loss", "profit", "execution", "lagging", "fail"],
        "priority": 1 # Highest priority for financial loss/technical failure in trading
    },
    "Payments/Money": {
        "keywords": ["money", "payment", "withdraw", "add fund", "UPI", "Netbanking", "withdrawal", "deposit", "transaction", "transferred", "credit", "debit"],
        "priority": 2 # Second highest for financial loss related to funds
    },
    "App Performance": {
        "keywords": ["crash", "lag", "slow", "freeze", "bug", "error", "not working", "technical issue", "hang", "battery drain", "glitch"],
        "priority": 3 # Third highest for technical failure impacting usability
    },
    "Onboarding/KYC": {
        "keywords": ["KYC", "onboard", "sign up", "verify", "document", "account activation", "registration", "login issue"],
        "priority": 4
    },
    "Charges/Policy": {
        "keywords": ["charges", "fees", "brokerage", "account maintenance", "hidden charges", "commission", "policy"],
        "priority": 5
    },
    "General Sentiment": {
        "keywords": ["good app", "easy to use", "best app", "superb", "excellent", "nice app", "great app", "simple interface", "user friendly", "no complaints"],
        "priority": 99 # Lowest priority, often ignored for pulse report if other themes exist
    }
}

def get_embedding_simulation(text_input):
    """
    Simulates the embedding generation for a given text.
    In a real scenario, this would be an API call to Gemini's embedding model.
    """
    return np.random.rand(EMBEDDING_DIM)

def assign_themes_to_reviews_with_priority(review_content, operational_buckets, bucket_embeddings):
    """
    Assigns exactly one operational bucket to a review based on keyword priority and then cosine similarity.
    Prioritizes buckets involving financial loss or technical failure.
    """
    if pd.isna(review_content) or not review_content.strip():
        return "Uncategorized"

    review_content_lower = review_content.lower()
    
    # Step 1: Check for General Sentiment (low priority, only if no other specific issues)
    general_sentiment_match = False
    for keyword in operational_buckets["General Sentiment"]["keywords"]:
        if keyword in review_content_lower:
            general_sentiment_match = True
            break

    # Step 2: Prioritized Keyword Matching
    matched_buckets = []
    for bucket_name, bucket_info in operational_buckets.items():
        if bucket_name == "General Sentiment": # Skip general sentiment for prioritized matching
            continue
        for keyword in bucket_info["keywords"]:
            if keyword in review_content_lower:
                matched_buckets.append((bucket_name, bucket_info["priority"]))
                break # Move to next bucket if any keyword matches
    
    if matched_buckets:
        # Sort by priority (lower number = higher priority)
        matched_buckets.sort(key=lambda x: x[1])
        # If multiple high-priority matches, use embeddings among them
        highest_priority_score = matched_buckets[0][1]
        top_priority_buckets = [b[0] for b in matched_buckets if b[1] == highest_priority_score]

        if len(top_priority_buckets) == 1:
            return top_priority_buckets[0]
        else:
            # If multiple top-priority buckets matched, use embedding similarity among them
            review_embedding = get_embedding_simulation(review_content)
            best_bucket = None
            max_similarity = -1
            for bucket_name in top_priority_buckets:
                theme_index = list(operational_buckets.keys()).index(bucket_name)
                similarity = cosine_similarity(review_embedding.reshape(1, -1), bucket_embeddings[theme_index].reshape(1, -1))[0][0]
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_bucket = bucket_name
            return best_bucket

    # Step 3: Fallback to Embedding Similarity for remaining reviews
    # This also handles cases where general sentiment was matched but there were no prioritized keywords
    if general_sentiment_match:
        return "General Sentiment"
    
    # If no keywords matched and not general sentiment, use pure embedding similarity for all buckets (excluding General Sentiment for classification)
    review_embedding = get_embedding_simulation(review_content)
    best_bucket = "Uncategorized"
    max_similarity = -1

    for i, (bucket_name, bucket_info) in enumerate(operational_buckets.items()):
        if bucket_name == "General Sentiment": # Do not classify into General Sentiment via pure similarity unless explicitly matched by keyword
            continue
        similarity = cosine_similarity(review_embedding.reshape(1, -1), bucket_embeddings[i].reshape(1, -1))[0][0]
        if similarity > max_similarity:
            max_similarity = similarity
            best_bucket = bucket_name
            
    return best_bucket

if __name__ == "__main__":
    print(f"--- Layer 2: Theme Extraction - Phase 2 (Operational Bucket Classification) ---")
    
    try:
        reviews_df = pd.read_csv(CSV_FILE)
        print(f"Loaded {len(reviews_df)} reviews from '{CSV_FILE}'")
        
        # Generate embeddings for all operational buckets
        print("Generating embeddings for operational buckets...")
        bucket_names = list(OPERATIONAL_BUCKETS.keys())
        bucket_embeddings = [get_embedding_simulation(name) for name in bucket_names]
        print("Operational bucket embeddings generated.")
        
        # Assign operational buckets to reviews
        print("Assigning operational buckets to reviews...")
        reviews_df['operational_bucket'] = reviews_df['content'].apply(lambda x: assign_themes_to_reviews_with_priority(x, OPERATIONAL_BUCKETS, bucket_embeddings))
        print("Operational buckets assigned to all reviews.")
        
        # Filter out [General Sentiment] for the pulse report
        pulse_report_df = reviews_df[reviews_df['operational_bucket'] != "General Sentiment"].copy()

        # Store & Aggregate results
        print("\n--- Storing Results ---")
        reviews_df.to_csv(LAYER2_OUTPUT_CSV_FILE, index=False)
        print(f"All reviews with operational buckets saved to '{LAYER2_OUTPUT_CSV_FILE}'")
        
        print("\n--- Operational Bucket Distribution Summary (Excluding General Sentiment) ---")
        bucket_counts = pulse_report_df['operational_bucket'].value_counts()
        print(bucket_counts)
        
        print("\n--- Full Operational Bucket Distribution Summary (Including General Sentiment) ---")
        full_bucket_counts = reviews_df['operational_bucket'].value_counts()
        print(full_bucket_counts)
        
    except FileNotFoundError:
        print(f"Error: The file '{CSV_FILE}' was not found. Please ensure it's in the correct directory.")
    except Exception as e:
        print(f"An error occurred: {e}")