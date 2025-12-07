import os
import sys
from datetime import datetime
import pandas as pd # For initial CSV creation if needed
import json
from dotenv import load_dotenv

# Add src to the system path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import functions from other layers
from scrape_groww import scrape_relevant_recent # Assuming scrape_groww is in the root
from src.classifier import classify_reviews
from src.reporter import generate_pulse
from src.emailer import send_email

# Define file paths
RAW_REVIEWS_CSV = 'groww_relevant_reviews.csv'
CLASSIFIED_REVIEWS_CSV = 'weekly_classified.csv'

def main():
    """
    Orchestrates the entire Review Intelligence Pipeline:
    Scrape -> Classify -> Generate Report -> Send Email.
    Includes comprehensive error handling.
    """
    print(f"\n--- Groww App Review Intelligence Pipeline - Started {datetime.now()} ---")

    # Ensure environment variables are set for API keys and email
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable not set. Please set it before running.")
        sys.exit(1)
    if not os.environ.get("EMAIL_SENDER") or not os.environ.get("EMAIL_PASSWORD"):
        print("Warning: EMAIL_SENDER or EMAIL_PASSWORD environment variables not set. Emailing might fail.")

    # --- Layer 1: Data Import (Scraping) ---
    try:
        print(f"\nStep 1: Running Data Import (Scraping) to {RAW_REVIEWS_CSV}...")
        scrape_relevant_recent(output_csv_file=RAW_REVIEWS_CSV)
        if not os.path.exists(RAW_REVIEWS_CSV) or pd.read_csv(RAW_REVIEWS_CSV).empty:
            raise ValueError(f"Scraping completed but {RAW_REVIEWS_CSV} is empty or not created.")
        print("Data Import (Scraping) completed successfully.")
    except Exception as e:
        print(f"Critical Error during Data Import (Scraping): {e}")
        sys.exit(1) # Exit if scraping fails

    # --- Layer 2: Theme Extraction (Classification) ---
    try:
        print(f"\nStep 2: Running Theme Extraction (Classification) to {CLASSIFIED_REVIEWS_CSV}...")
        classify_reviews(RAW_REVIEWS_CSV, CLASSIFIED_REVIEWS_CSV)
        if not os.path.exists(CLASSIFIED_REVIEWS_CSV) or pd.read_csv(CLASSIFIED_REVIEWS_CSV).empty:
            raise ValueError(f"Classification completed but {CLASSIFIED_REVIEWS_CSV} is empty or not created.")
        print("Theme Extraction (Classification) completed successfully.")
    except Exception as e:
        print(f"Error during Theme Extraction (Classification): {e}")
        # Continue to next steps if classification error is not critical, or exit based on severity
        # For now, we'll allow it to proceed to see if a report can still be generated.

    # --- Layer 3: Content Generation (Report) ---
    pulse_data = None
    try:
        print("\nStep 3: Running Content Generation (Report)...")
        if os.path.exists(CLASSIFIED_REVIEWS_CSV):
            pulse_data = generate_pulse(CLASSIFIED_REVIEWS_CSV)
            if pulse_data and not pulse_data.get("error"):
                print("Content Generation (Report) completed successfully.")
                print("Generated Pulse Report (JSON snippet):")
                print(json.dumps(pulse_data, indent=2)[:500] + "...\n") # Print a snippet
            else:
                raise ValueError(f"Content Generation failed: {pulse_data.get('error', 'Unknown error')}")
        else:
            raise FileNotFoundError(f"'{CLASSIFIED_REVIEWS_CSV}' not found after classification. Cannot generate report.")
    except Exception as e:
        print(f"Error during Content Generation (Report): {e}")
        # Continue to emailing, as an empty report might still be sent to notify.

    # --- Layer 4: Delivery (Emailing) ---
    try:
        print("\nStep 4: Running Delivery (Emailing)...")
        if pulse_data:
            send_email(pulse_data)
            print("Delivery (Emailing) process initiated.")
        else:
            print("Skipping email delivery: No pulse data was generated.")
    except Exception as e:
        print(f"Error during Delivery (Emailing): {e}")

    print(f"\n--- Groww App Review Intelligence Pipeline - Finished {datetime.now()} ---")

if __name__ == "__main__":
    # For local testing, you might need a .env file or to set environment variables directly
    # Example for local development (do NOT commit .env with secrets)
    # from dotenv import load_dotenv
    # load_dotenv() # This would load GEMINI_API_KEY, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER from a .env file
    load_dotenv() # Load environment variables from .env file
    main()