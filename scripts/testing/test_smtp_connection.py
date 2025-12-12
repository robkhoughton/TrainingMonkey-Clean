#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMTP Connection Test Script
Tests email sending configuration before deployment
"""

import os
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
try:
    from dotenv import load_dotenv
    from pathlib import Path

    # Load .env from parent directory (project root)
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
    print(f"✅ Loaded .env file from {env_path}")
except Exception as e:
    print(f"⚠️  Error loading .env file: {e}")

print("\n" + "="*60)
print("SMTP CONFIGURATION TEST")
print("="*60)

# Check environment variables
print("\n1. Checking environment variables...")
smtp_host = os.environ.get('SMTP_HOST')
smtp_port = os.environ.get('SMTP_PORT')
smtp_user = os.environ.get('SMTP_USER')
smtp_password = os.environ.get('SMTP_PASSWORD')
smtp_from = os.environ.get('SMTP_FROM_EMAIL')
app_base_url = os.environ.get('APP_BASE_URL')

config_ok = True

if not smtp_host:
    print("   ❌ SMTP_HOST not set")
    config_ok = False
else:
    print(f"   ✅ SMTP_HOST: {smtp_host}")

if not smtp_port:
    print("   ❌ SMTP_PORT not set")
    config_ok = False
else:
    print(f"   ✅ SMTP_PORT: {smtp_port}")

if not smtp_user:
    print("   ❌ SMTP_USER not set")
    config_ok = False
else:
    print(f"   ✅ SMTP_USER: {smtp_user}")

if not smtp_password:
    print("   ❌ SMTP_PASSWORD not set")
    config_ok = False
else:
    # Show first/last 2 chars only for security
    masked = smtp_password[:2] + '*'*(len(smtp_password)-4) + smtp_password[-2:] if len(smtp_password) > 4 else '****'
    print(f"   ✅ SMTP_PASSWORD: {masked}")

if not smtp_from:
    print("   ⚠️  SMTP_FROM_EMAIL not set (will use default)")
    smtp_from = 'noreply@yourtrainingmonkey.com'
else:
    print(f"   ✅ SMTP_FROM_EMAIL: {smtp_from}")

if not app_base_url:
    print("   ⚠️  APP_BASE_URL not set (will use default)")
    app_base_url = 'https://yourtrainingmonkey.com'
else:
    print(f"   ✅ APP_BASE_URL: {app_base_url}")

if not config_ok:
    print("\n❌ Configuration incomplete. Please set missing environment variables.")
    print("\nExample .env file:")
    print("""
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourtrainingmonkey.com
APP_BASE_URL=https://yourtrainingmonkey.com
""")
    sys.exit(1)

# Test SMTP connection
print("\n2. Testing SMTP connection...")
try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    # Create test connection
    with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
        print("   ✅ Connected to SMTP server")

        server.starttls()
        print("   ✅ TLS encryption enabled")

        server.login(smtp_user, smtp_password)
        print("   ✅ Authentication successful")

    print("\n✅ SMTP connection test passed!")

except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ Authentication failed: {e}")
    print("\nTroubleshooting:")
    print("  - If using Gmail, make sure you're using an App Password, not your regular password")
    print("  - Generate App Password: https://myaccount.google.com/apppasswords")
    print("  - Make sure 2-Factor Authentication is enabled on your Google account")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("  - Check SMTP_HOST and SMTP_PORT are correct")
    print("  - Check your firewall isn't blocking port 587")
    print("  - Try using port 465 with SSL instead")
    sys.exit(1)

# Ask if user wants to send test email
print("\n3. Send test email?")
test_email = input("   Enter your email address to receive test verification email (or press Enter to skip): ").strip()

if test_email and '@' in test_email:
    print(f"\n   Sending test email to {test_email}...")

    try:
        # Create test message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Test Email - Your Training Monkey Verification System"
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
            <h1>🐵 Your Training Monkey</h1>
            <p>Email Verification Test</p>
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
        with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        print(f"   ✅ Test email sent successfully to {test_email}")
        print(f"\n   Check your inbox (and spam folder) for the test email.")
        print(f"   If you receive it, SMTP is working correctly!")

    except Exception as e:
        print(f"   ❌ Failed to send test email: {e}")
        sys.exit(1)

else:
    print("   Skipped test email")

# Final summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
print("✅ Environment variables configured")
print("✅ SMTP connection successful")
print("✅ Authentication working")
if test_email and '@' in test_email:
    print("✅ Test email sent")
    print(f"\n📧 Check {test_email} inbox for test email")
print("\n🚀 Your email verification system is ready to deploy!")
print("="*60)
