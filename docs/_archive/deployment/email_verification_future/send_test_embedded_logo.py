#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send Test Email with Embedded Logo (Base64)
"""

import os
import sys
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

smtp_host = os.environ.get('SMTP_HOST')
smtp_port = int(os.environ.get('SMTP_PORT', 587))
smtp_user = os.environ.get('SMTP_USER')
smtp_password = os.environ.get('SMTP_PASSWORD')
smtp_from = os.environ.get('SMTP_FROM_EMAIL')

test_email = "rob.houghton.ca@gmail.com"

print(f"Sending test email with embedded logo to: {test_email}\n")

try:
    # Create message with related content (for embedded images)
    msg = MIMEMultipart('related')
    msg['Subject'] = "Test - YTM Email with Embedded Logo"
    msg['From'] = smtp_from
    msg['To'] = test_email

    # Create HTML alternative part
    msg_alternative = MIMEMultipart('alternative')
    msg.attach(msg_alternative)

    # Plain text version
    text_body = """
Your Training Monkey - Email Verification Test

This is a test email with embedded YTM logo.

If you received this email with the logo visible, the email verification system is ready!
    """

    # HTML version with embedded image reference
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
        .logo {
            max-width: 220px;
            height: auto;
            margin-bottom: 15px;
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
            <img src="cid:ytm_logo" alt="Your Training Monkey" class="logo">
            <p style="font-size: 18px; font-weight: 600; margin: 0;">Email Verification Test</p>
        </div>

        <div class="content">
            <div class="success">
                <h2 style="color: #065f46; margin: 0;">✅ Embedded Logo Test</h2>
            </div>

            <p>This is a test email with the YTM logo embedded directly in the email.</p>

            <p><strong>If you can see the logo above, the email verification system is ready to deploy!</strong></p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="https://yourtrainingmonkey.com/verify-email?token=test-token-12345" class="button">
                    Test Verification Button
                </a>
            </div>
        </div>

        <div style="text-align: center; color: #6b7280; font-size: 0.9rem; margin-top: 20px;">
            <p>Your Training Monkey - Email Verification System</p>
        </div>
    </div>
</body>
</html>
    """

    # Attach text and HTML parts
    part1 = MIMEText(text_body, 'plain')
    part2 = MIMEText(html_body, 'html')
    msg_alternative.attach(part1)
    msg_alternative.attach(part2)

    # Read and attach the logo image (circular "Built for Trail Runners" design)
    logo_path = Path(__file__).parent / 'static' / 'images' / 'YTM_Logo_byandfor_300.png'

    with open(logo_path, 'rb') as img_file:
        img_data = img_file.read()
        image = MIMEImage(img_data, _subtype='png')
        image.add_header('Content-ID', '<ytm_logo>')
        image.add_header('Content-Disposition', 'inline', filename='ytm_logo.png')
        msg.attach(image)

    print("Logo embedded, sending email...")

    # Send email
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    print("✅ Test email with embedded logo sent!")
    print("\nCheck your inbox - the logo should be embedded and visible.")

except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
