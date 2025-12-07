# Groww App Review Intelligence Pipeline

A Python-based automated pipeline that scrapes, analyzes, and reports on user reviews from the Groww app using Google Gemini AI.

## Overview

This project implements a 4-layer intelligent review analysis system:

1. **Layer 1: Data Import (Scraping)** - Fetches recent reviews from the Groww app on Google Play Store
2. **Layer 2: Theme Extraction (Classification)** - Categorizes reviews into operational themes using Gemini AI
3. **Layer 3: Content Generation (Report)** - Generates actionable insights and summaries using Gemini
4. **Layer 4: Delivery (Email)** - Sends formatted HTML reports via Gmail

## Features

- **Automated Web Scraping**: Pulls recent reviews from Google Play Store (last 1 week by default)
- **AI-Powered Classification**: Uses Gemini 1.5 Flash to categorize reviews into 9 operational themes
- **Intelligent Report Generation**: Generates insights with issue summaries, user quotes, and action items
- **Email Delivery**: Sends formatted HTML reports directly to stakeholders
- **Rate Limit Management**: Built-in 15-second delays to respect Gemini free tier quotas
- **Error Handling**: Comprehensive error handling and fallback mechanisms

## Operational Themes

Reviews are classified into the following categories:

1. Order Execution
2. Payments/Money
3. App Performance
4. Onboarding/KYC
5. Charges/Policy
6. Missing or Requested Features
7. Customer Support & Service Quality
8. User Interface & Experience (UI/UX)
9. General Sentiment

## Project Structure

```
Milestone-2/
├── main.py                          # Main orchestration script
├── scrape_groww.py                  # Web scraping logic
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables (not committed)
├── groww_relevant_reviews.csv       # Raw scraped reviews
├── weekly_classified.csv            # Classified reviews
├── src/
│   ├── classifier.py                # Theme classification module
│   ├── reporter.py                  # Report generation module
│   └── emailer.py                   # Email delivery module
└── README.md                        # This file
```

## Installation

### Prerequisites

- Python 3.8+
- Google Gemini API key
- Gmail account with app password

### Setup Steps

1. **Clone the repository**
   ```powershell
   git clone <your-repo-url>
   cd Milestone-2
   ```

2. **Create a virtual environment (optional but recommended)**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the project root with your credentials:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   EMAIL_SENDER=your_email@gmail.com
   EMAIL_PASSWORD=your_gmail_app_password
   EMAIL_RECEIVER=recipient@example.com
   ```

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Your Google Gemini API key | `AIzaSy...` |
| `EMAIL_SENDER` | Gmail address to send from | `bot@gmail.com` |
| `EMAIL_PASSWORD` | Gmail app-specific password | `abcd efgh ijkl mnop` |
| `EMAIL_RECEIVER` | Email to send reports to | `manager@company.com` |

### Getting Gmail App Password

1. Enable 2-Factor Authentication on your Google account
2. Go to [Google Account Security](https://myaccount.google.com/security)
3. Find "App passwords" section
4. Generate a password for "Mail" on "Windows Computer"
5. Use this password in `.env` as `EMAIL_PASSWORD`

## Usage

### Run the Complete Pipeline

```powershell
python main.py
```

This will:
1. Scrape reviews from the last week
2. Classify them using Gemini AI
3. Generate a detailed report
4. Send an email with the findings

### Expected Output

```
--- Groww App Review Intelligence Pipeline - Started 2025-12-08 10:30:45.123456 ---

Step 1: Running Data Import (Scraping) to groww_relevant_reviews.csv...
✓ Scraped 42 reviews from the last week

Step 2: Running Theme Extraction (Classification) to weekly_classified.csv...
✓ Classified 42 reviews into operational themes

Step 3: Running Content Generation (Report)...
✓ Generated pulse report with top 3 themes

Step 4: Running Delivery (Emailing)...
✓ Email sent successfully to recipient@example.com

--- Groww App Review Intelligence Pipeline - Finished 2025-12-08 10:35:12.654321 ---
```

## API Rate Limits

The pipeline respects Gemini API free tier limits:

- **Requests per minute**: 5 (for Flash model)
- **Configured delay**: 15 seconds between API calls
- **Fallback behavior**: Returns "General Sentiment" if API fails

To avoid quota exhaustion, the classifier waits 15 seconds between each review classification.

## File Descriptions

### `main.py`
Orchestrates the entire pipeline, connecting all 4 layers and handling errors.

### `scrape_groww.py`
Fetches reviews from Google Play Store using the `google-play-scraper` library.
- Filters for reviews from the last 1 week
- Validates and sanitizes data
- Masks PII (emails, phone numbers)

### `src/classifier.py`
Classifies reviews into operational themes using Gemini 1.5 Flash chat model.
- Analyzes each review against 9 predefined themes
- Returns the best-matching theme
- Includes error handling and fallback mechanisms

### `src/reporter.py`
Generates detailed insights for the top 3 themes.
- Extracts issue summaries
- Pulls representative user quotes
- Suggests actionable improvements

### `src/emailer.py`
Sends formatted HTML emails with the report.
- Connects to Gmail's SMTP server
- Formats data as professional HTML
- Includes error handling for authentication

## Troubleshooting

### Error: GEMINI_API_KEY not set
**Solution**: Ensure `.env` file exists in the project root with your API key.

### Error: 429 Quota Exceeded
**Solution**: The pipeline already includes 15-second delays. If quota still exceeded:
- Wait until the quota resets (usually within an hour)
- Consider upgrading to a paid Gemini API plan

### Error: Failed to authenticate with SMTP
**Solution**: Verify your email and app password in `.env`. Use Gmail app password, not your regular password.

### Email sent but no content
**Solution**: Check that reviews are being classified properly. Run and check `weekly_classified.csv` to ensure the `operational_bucket` column has theme names.

## Dependencies

```
pandas              - Data manipulation and CSV handling
google-play-scraper - Google Play Store scraping
google-generativeai - Gemini API access
tqdm                - Progress bars
scikit-learn        - Machine learning utilities
python-dotenv       - Environment variable management
```

## Performance Notes

- **Scraping**: ~1-2 minutes for 1000 reviews
- **Classification**: ~10+ minutes for 42 reviews (due to 15s delays per request)
- **Report Generation**: ~1-2 minutes
- **Total Pipeline**: ~15-20 minutes for full run

## Future Enhancements

- [ ] Implement batch classification to reduce API calls
- [ ] Add sentiment score analysis
- [ ] Create dashboard for trend visualization
- [ ] Store historical reports in database
- [ ] Implement automatic scheduling (daily/weekly)
- [ ] Add support for multiple apps

## License

This project is part of the NextLeap Milestone-2 initiative.

## Support

For issues or questions, please contact the development team or create an issue in the repository.

---

**Last Updated**: December 8, 2025
