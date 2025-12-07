import pandas as pd
from google_play_scraper import reviews, Sort
from datetime import datetime, timedelta
import sys
import re

# CONFIGURATION
APP_ID = 'com.nextbillion.groww'  # Groww App ID
LOOKBACK_WEEKS = 1
MAX_SCRAPE_COUNT = 1000  # Fetch top 1000 relevant reviews to find recent ones
# CSV_FILE is now passed as an argument to scrape_relevant_recent

def get_cutoff_date():
    """Calculate the date 8 weeks ago from today."""
    return datetime.now() - timedelta(weeks=LOOKBACK_WEEKS)

def validate_review(r):
    """
    Strict validation to ensure data is not null/empty.
    Returns True if valid, False otherwise.
    """
    required_fields = ['reviewId', 'content', 'at', 'score']
    
    for field in required_fields:
        if field not in r or r[field] is None:
            return False
            
    # Check for empty strings in content
    if isinstance(r['content'], str) and not r['content'].strip():
        return False
        
    return True

def mask_pii(text):
    """
    Mask sensitive information in text.
    """
    # Mask email addresses
    text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL_MASKED]", text)
    # Mask phone numbers (common Indian formats)
    text = re.sub(r"\\b\\d{10}\\b", "[PHONE_MASKED]", text) # 10-digit numbers
    text = re.sub(r"\\+91[-\\s]?\\d{10}\\b", "[PHONE_MASKED]", text) # +91 prefix
    
    return text

def scrape_relevant_recent(output_csv_file: str = 'groww_relevant_reviews.csv'):
    print(f"--- Starting Scrape for {APP_ID} ---")
    print(f"Filter: MOST RELEVANT | Time Window: Last {LOOKBACK_WEEKS} Weeks")
    
    cutoff_date = get_cutoff_date()
    print(f"Looking for reviews newer than: {cutoff_date.date()}")

    # 1. Fetch Reviews (Batch Processing)
    # We fetch a large batch because 'Relevant' sort is not chronological.
    result, _ = reviews(
        APP_ID,
        lang='en', # English
        country='in', # India (Groww's primary market)
        sort=Sort.MOST_RELEVANT, # The specific filter you asked for
        count=MAX_SCRAPE_COUNT
    )

    valid_data = []
    skipped_old = 0
    skipped_invalid = 0

    # 2. Process & Validate
    for r in result:
        # Step A: Data Validation (Check for nulls)
        if not validate_review(r):
            skipped_invalid += 1
            continue

        # Step B: Date Filtering (The 8-week check)
        review_date = r['at']
        if review_date < cutoff_date:
            skipped_old += 1
            continue

        # Step C: Structure Data
        valid_data.append({
            'review_id': r['reviewId'],
            'date': review_date.strftime('%Y-%m-%d'),
            'user_name': "Anonymous User", # Anonymize user name
            'score': r['score'],
            'thumbs_up': r['thumbsUpCount'],
            'content': mask_pii(r['content']), # Mask PII in content
            'review_created_version': r.get('reviewCreatedVersion', 'Unknown')
        })

    # 3. Summary & Save
    print(f"\n--- Processing Complete ---")
    print(f"Total Fetched: {len(result)}")
    print(f"Skipped (Too Old): {skipped_old}")
    print(f"Skipped (Invalid/Null): {skipped_invalid}")
    print(f"Valid Recent Reviews Kept: {len(valid_data)}")

    if valid_data:
        df = pd.DataFrame(valid_data)
        # Sort by date for easier reading, even though we scraped by relevance
        df = df.sort_values(by='date', ascending=False)
        
        df.to_csv(output_csv_file, index=False)
        print(f"\n[SUCCESS] Saved {len(valid_data)} reviews to '{output_csv_file}'")
        print(f"Sample:\n{df[['date', 'score', 'content']].head(3)}")
    else:
        print("\n[WARNING] No reviews found in the last 8 weeks within the 'Most Relevant' batch.")
        print("Tip: Try increasing MAX_SCRAPE_COUNT or switch to Sort.NEWEST.")

if __name__ == "__main__":
    # When run directly, it will use the default output file name.
    scrape_relevant_recent()