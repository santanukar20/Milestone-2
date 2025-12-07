import os
import json
import pandas as pd
import google.generativeai as genai
import re
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=api_key)

# 1. USE THE HIGH-LIMIT MODEL
MODEL_NAME = "gemini-1.5-flash"

def generate_theme_details(theme_name, reviews):
    review_text = "\n".join([f"- {r}" for r in reviews])
    
    # Prompt: Strict "Senior PM" briefing style
    prompt = f"""
    You are a Senior Product Manager. Analyze these user reviews for the theme: '{theme_name}'.
    
    Output a valid JSON object with:
    1. "issue_headline": A 10-word punchy headline of the core friction.
    2. "user_quotes": List of 3 short, exact user quotes.
    3. "action_items": List of 3 specific technical/UX fixes.
    
    Reviews:
    {review_text}
    
    Return ONLY JSON.
    """
    
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        clean_json = text_response.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"   ⚠️ Parsing Error for {theme_name}: {e}")
        return {
            "issue_headline": "Analysis unavailable",
            "user_quotes": ["N/A"],
            "action_items": ["Manual review required"]
        }

def generate_html_report(pulse_data):
    # UX/UI Persona: Clean, Card-Based Layout
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica', Arial, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #fff; border-radius: 8px; overflow: hidden; }}
            .header {{ background: #2c3e50; color: #fff; padding: 20px; text-align: center; }}
            .card {{ border-bottom: 1px solid #eee; padding: 20px; }}
            .tag {{ background: #34495e; color: #fff; padding: 3px 8px; border-radius: 4px; font-size: 11px; text-transform: uppercase; }}
            .headline {{ margin: 10px 0; color: #2c3e50; font-size: 18px; font-weight: bold; }}
            .split {{ display: table; width: 100%; border-spacing: 10px; }}
            .col {{ display: table-cell; width: 50%; vertical-align: top; background: #f9f9f9; padding: 10px; border-radius: 5px; }}
            .label {{ font-size: 10px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; display: block; }}
            ul {{ padding-left: 15px; margin: 0; font-size: 12px; line-height: 1.4; }}
            li {{ margin-bottom: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>{pulse_data['title']}</h2>
                <p>{pulse_data['executive_summary']}</p>
            </div>
    """
    
    for item in pulse_data['top_themes']:
        quotes = "".join([f"<li>\"{q}\"</li>" for q in item['details']['user_quotes']])
        actions = "".join([f"<li>{a}</li>" for a in item['details']['action_items']])
        
        html += f"""
        <div class="card">
            <span class="tag">#{item['rank']} {item['theme_name']}</span>
            <div class="headline">{item['details']['issue_headline']}</div>
            <div class="split">
                <div class="col" style="background:#FFF5F5;">
                    <span class="label" style="color:#C0392B;">🗣️ User Voices</span>
                    <ul style="color:#555;">{quotes}</ul>
                </div>
                <div class="col" style="background:#F0F7FA;">
                    <span class="label" style="color:#2980B9;">⚡ Actions</span>
                    <ul style="color:#333;">{actions}</ul>
                </div>
            </div>
        </div>
        """
        
    html += "</div></body></html>"
    return html

def generate_pulse(input_csv):
    print(f"--- Layer 3: Generating Executive UX Report from {input_csv} ---")
    
    if not os.path.exists(input_csv):
        return None

    df = pd.read_csv(input_csv)
    
    # Handle column names
    if 'operational_bucket' not in df.columns:
        if 'classification' in df.columns:
            df['operational_bucket'] = df['classification']
        else:
            return None

    actionable_df = df[df['operational_bucket'] != 'General Sentiment']
    if actionable_df.empty: actionable_df = df
    
    top_3_themes = actionable_df['operational_bucket'].value_counts().head(3).index.tolist()
    
    report_data = {
        "title": "Groww Product Pulse",
        "executive_summary": f"Prioritized analysis of {len(df)} reviews. Top friction points: {', '.join(top_3_themes)}.",
        "top_themes": []
    }
    
    for i, theme in enumerate(top_3_themes):
        print(f"   Analyzing: {theme}...")
        theme_reviews = df[df['operational_bucket'] == theme]['content'].tolist()
        details = generate_theme_details(theme, theme_reviews) # Use ALL reviews
        
        report_data['top_themes'].append({
            "rank": i + 1,
            "theme_name": theme,
            "details": details
        })

    print("✅ Executive Report Generated.")
    return generate_html_report(report_data)

if __name__ == "__main__":
    print(generate_pulse("weekly_classified.csv"))