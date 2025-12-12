#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send Simple Test Email (text-only for troubleshooting)
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Get configuration
smtp_host = os.environ.get('SMTP_HOST')
smtp_port = int(os.environ.get('SMTP_PORT', 587))
smtp_user = os.environ.get('SMTP_USER')
smtp_password = os.environ.get('SMTP_PASSWORD')
smtp_from = os.environ.get('SMTP_FROM_EMAIL')

test_email = "rob.houghton.ca@gmail.com"

print(f"Sending simple text email to: {test_email}")

try:
    # Create simple text message
    msg = MIMEText("This is a simple test from Your Training Monkey email system. If you receive this, SMTP is working.")
    msg['Subject'] = "Simple Test - YTM Email System"
    msg['From'] = smtp_from
    msg['To'] = test_email

    # Send email
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    print("✅ Simple test email sent!")

except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)
