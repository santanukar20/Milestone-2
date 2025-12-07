import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_email(body_content):
    # 1. READ VARIABLES (Updated to match your .env file)
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    recipient_email = os.getenv("EMAIL_RECEIVER")

    # 2. SAFETY CHECK
    if not sender_email or not sender_password:
        print("❌ Error: EMAIL_SENDER or EMAIL_PASSWORD missing in .env")
        print(f"   Found: Sender={sender_email}, Password={'*' * 5 if sender_password else 'None'}")
        return

    if not recipient_email:
        print("⚠️ Warning: EMAIL_RECEIVER not found. Using sender as recipient.")
        recipient_email = sender_email

    # 3. PREPARE EMAIL
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "Weekly App Review Pulse"
    
    msg.attach(MIMEText(body_content, 'html'))

    # 4. SEND
    try:
        print(f"   Connecting to Gmail as {sender_email}...")
        # Note: Using port 465 for SSL (standard for Gmail)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"✅ Email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")