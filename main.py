import os
import sys
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from scrape_groww import scrape_relevant_recent
from src.classifier import classify_reviews
from src.reporter import generate_pulse
from src.emailer import send_email

RAW = 'groww_relevant_reviews.csv'
CLASSIFIED = 'weekly_classified.csv'

def main():
    print(f"\n--- Pipeline Started {datetime.now()} ---")
    load_dotenv()
    
    if not os.getenv("GEMINI_API_KEY"): sys.exit("Error: GEMINI_API_KEY not set in .env file")

    # Step 1: Scrape
    try:
        print("\nStep 1: Scraping...")
        scrape_relevant_recent(output_csv_file=RAW)
    except Exception as e: sys.exit(f"Scrape Error: {e}")

    # Step 2: Classify
    try:
        print("\nStep 2: Classifying...")
        classify_reviews(RAW, CLASSIFIED)
    except Exception as e: print(f"Classify Error: {e}")

    # Step 3: Report
    report_html = None
    try:
        print("\nStep 3: Generating Report...")
        if os.path.exists(CLASSIFIED):
            report_html = generate_pulse(CLASSIFIED)
            if report_html: print("Report Generated.")
    except Exception as e: print(f"Report Error: {e}")

    # Step 4: Email
    try:
        print("\nStep 4: Emailing...")
        if report_html:
            send_email(report_html)
            print("✅ Email Sent!")
        else: print("No report to send.")
    except Exception as e: print(f"Email Error: {e}")

    print(f"\n--- Finished {datetime.now()} ---")

if __name__ == "__main__":
    main()