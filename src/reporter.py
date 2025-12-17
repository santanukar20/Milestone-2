import os
import json
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

def generate_all_themes_details(themes_with_reviews):
    """
    Generate details for ALL themes in a SINGLE API call.
    This reduces API calls from 3 to just 1.
    themes_with_reviews: list of tuples (theme_name, reviews_list)
    """
    # Build prompt for all themes at once
    themes_section = ""
    for theme_name, reviews in themes_with_reviews:
        review_text = "\n".join([f"  - {r[:100]}" for r in reviews[:5]])  # Limit to first 5 reviews per theme
        themes_section += f"\n\nTheme: {theme_name}\nReviews:\n{review_text}"
    
    prompt = f"""
    You are a Senior Product Manager. Analyze reviews for multiple themes.
    Output a JSON object with theme names as keys. Each theme should have:
    1. "issue_headline": Punchy 10-word headline.
    2. "user_quotes": List of 3 verbatim quotes from reviews.
    3. "action_items": List of 3 specific, actionable fixes.
    
    Themes and Reviews:
    {themes_section}
    
    Return ONLY valid JSON in this format:
    {{
        "Theme Name 1": {{"issue_headline": "...", "user_quotes": [...], "action_items": [...]}},
        "Theme Name 2": {{"issue_headline": "...", "user_quotes": [...], "action_items": [...]}}
    }}
    """
    
    tried_fallback = False
    current_model = MODEL_NAME
    while True:
        try:
            model = genai.GenerativeModel(current_model)
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean up markdown formatting if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            return json.loads(result_text)
        except Exception as e:
            err_str = str(e).lower()
            # If model not found or unsupported, try fallback once
            if (not tried_fallback) and ("not found" in err_str or "not supported" in err_str or "404" in err_str):
                tried_fallback = True
                current_model = FALLBACK_MODEL
                print(f"   Model {MODEL_NAME} not available; retrying with fallback {FALLBACK_MODEL}...")
                continue
            print(f"   ❌ Error generating theme details: {e}")
            # Return default fallback
            fallback = {}
            for theme_name, _ in themes_with_reviews:
                fallback[theme_name] = {
                    "issue_headline": f"Analysis unavailable for {theme_name}",
                    "user_quotes": ["N/A"],
                    "action_items": ["Manual review required"]
                }
            return fallback

def generate_html_report(pulse_data):
    html = f"""
    <html><body style="font-family: sans-serif; padding: 20px;">
    <div style="max-width: 600px; margin: auto; border: 1px solid #ccc; border-radius: 8px;">
        <div style="background: #2C3E50; color: white; padding: 20px; text-align: center;">
            <h2>{pulse_data['title']}</h2><p>{pulse_data['executive_summary']}</p>
        </div>
    """
    for item in pulse_data['top_themes']:
        q = "".join([f"<li>\"{x}\"</li>" for x in item['details']['user_quotes']])
        a = "".join([f"<li>{x}</li>" for x in item['details']['action_items']])
        html += f"""
        <div style="padding: 20px; border-bottom: 1px solid #eee;">
            <span style="background: #eee; padding: 3px 8px; font-size: 11px;">#{item['rank']} {item['theme_name']}</span>
            <h3 style="color: #2C3E50;">{item['details']['issue_headline']}</h3>
            <div style="background: #FFF5F5; padding: 10px; margin-bottom: 5px;"><b>🗣️ User Voices:</b><ul>{q}</ul></div>
            <div style="background: #F0F7FA; padding: 10px;"><b>⚡ Actions:</b><ul>{a}</ul></div>
        </div>"""
    return html + "</div></body></html>"

def generate_pulse(input_csv):
    print(f"--- Layer 3: Generating Report (Using {MODEL_NAME}) with Batch Processing ---")
    if not os.path.exists(input_csv): return None
    df = pd.read_csv(input_csv)
    
    if 'operational_bucket' not in df.columns: return None
    actionable = df[df['operational_bucket'] != 'General Sentiment']
    if actionable.empty: actionable = df
    
    top_3 = actionable['operational_bucket'].value_counts().head(3).index.tolist()
    
    print(f"   Extracting top themes: {top_3}")
    
    # Prepare all themes data for batch processing
    themes_with_reviews = []
    for theme in top_3:
        reviews = df[df['operational_bucket'] == theme]['content'].tolist()
        themes_with_reviews.append((theme, reviews))
    
    # Generate ALL themes in ONE API call
    print(f"   Generating insights for all themes in a single API call...")
    all_theme_details = generate_all_themes_details(themes_with_reviews)
    
    report = {"title": "Groww Product Pulse", "executive_summary": f"Top issues: {', '.join(top_3)}", "top_themes": []}
    
    for i, theme in enumerate(top_3):
        theme_details = all_theme_details.get(theme, {
            "issue_headline": "Analysis unavailable",
            "user_quotes": ["N/A"],
            "action_items": ["Manual review required"]
        })
        report['top_themes'].append({
            "rank": i+1, "theme_name": theme, "details": theme_details
        })
    
    print(f"✅ Report generated with {len(top_3)} themes")
    return generate_html_report(report)

    return generate_html_report(report)

if __name__ == "__main__":
    print(generate_pulse("weekly_classified.csv"))