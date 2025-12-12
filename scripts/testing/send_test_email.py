#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send Test Verification Email
Non-interactive version for automated testing
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

print("="*60)
print("SENDING TEST VERIFICATION EMAIL")
print("="*60)

# Get configuration
smtp_host = os.environ.get('SMTP_HOST')
smtp_port = int(os.environ.get('SMTP_PORT', 587))
smtp_user = os.environ.get('SMTP_USER')
smtp_password = os.environ.get('SMTP_PASSWORD')
smtp_from = os.environ.get('SMTP_FROM_EMAIL')

# Test email destination
test_email = "rob.houghton.ca@gmail.com"

print(f"\nSending test email to: {test_email}")
print(f"From: {smtp_from}")
print(f"Via: {smtp_host}:{smtp_port}\n")

try:
    # Create test message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "✅ Test Email - Your Training Monkey Verification System"
    msg['From'] = smtp_from
    msg['To'] = test_email

    # Plain text version
    text_body = """
Your Training Monkey - Email Verification Test

This is a test email to verify your SMTP configuration is working correctly.

If you received this email, your email verification system is ready to deploy!

Test verification link (not functional):
https://yourtrainingmonkey.com/verify-email?token=test-token-12345

---
Your Training Monkey
    """

    # HTML version
    html_body = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .container {
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
            border-radius: 12px;
            border: 2px solid #16a34a;
            padding: 30px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #16a34a;
            margin: 0;
        }
        .content {
            background: white;
            border-radius: 8px;
            padding: 25px;
            margin: 20px 0;
        }
        .button {
            display: inline-block;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 15px 40px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
        }
        .success {
            background: #d1fae5;
            border: 2px solid #10b981;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="https://yourtrainingmonkey.com/static/images/YTM_Logo_byandfor.webp" alt="Your Training Monkey" style="max-width: 220px; height: auto; margin-bottom: 15px;">
            <p style="font-size: 18px; font-weight: 600; margin: 0;">Email Verification Test</p>
        </div>

        <div class="content">
            <div class="success">
                <h2 style="color: #065f46; margin: 0;">✅ SMTP Test Successful!</h2>
            </div>

            <p>This is a test email to verify your SMTP configuration is working correctly.</p>

            <p><strong>If you received this email, your email verification system is ready to deploy!</strong></p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="https://yourtrainingmonkey.com/verify-email?token=test-token-12345" class="button">
                    Test Verification Button (Non-functional)
                </a>
            </div>

            <p style="font-size: 0.9rem; color: #6b7280;">
                This is a test email. The verification link above is not functional.
            </p>
        </div>

        <div style="text-align: center; color: #6b7280; font-size: 0.9rem; margin-top: 20px;">
            <p>Your Training Monkey - Email Verification System</p>
        </div>
    </div>
</body>
</html>
    """

    # Attach both versions
    part1 = MIMEText(text_body, 'plain')
    part2 = MIMEText(html_body, 'html')
    msg.attach(part1)
    msg.attach(part2)

    # Send email
    print("Connecting to SMTP server...")
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        print("Enabling TLS...")
        server.starttls()

        print("Authenticating...")
        server.login(smtp_user, smtp_password)

        print("Sending email...")
        server.send_message(msg)

    print("\n" + "="*60)
    print("✅ TEST EMAIL SENT SUCCESSFULLY!")
    print("="*60)
    print(f"\nCheck {test_email} inbox (and spam folder)")
    print("If you receive the email with proper formatting,")
    print("the email verification system is ready to deploy!")
    print("="*60)

except Exception as e:
    print(f"\n❌ Failed to send test email: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
