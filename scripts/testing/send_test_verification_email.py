#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send Test Verification Email - Standalone Version
Tests the new email branding without requiring database connection
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent.parent
load_dotenv(dotenv_path=project_root / '.env')

print("="*60)
print("EMAIL VERIFICATION BRANDING TEST")
print("="*60)

# Configuration
test_email = input("\nEnter your email address to receive test: ").strip()

if not test_email:
    print("❌ Email address required")
    sys.exit(1)

# Get SMTP configuration
smtp_host = os.environ.get('SMTP_HOST')
smtp_port = int(os.environ.get('SMTP_PORT', '587'))
smtp_user = os.environ.get('SMTP_USER')
smtp_password = os.environ.get('SMTP_PASSWORD')
from_email = os.environ.get('SMTP_FROM_EMAIL', 'noreply@yourtrainingmonkey.com')

if not smtp_host or not smtp_user or not smtp_password:
    print("\n❌ SMTP not configured!")
    print("Required environment variables:")
    print("  - SMTP_HOST")
    print("  - SMTP_USER")
    print("  - SMTP_PASSWORD")
    sys.exit(1)

print(f"\nSending verification email to: {test_email}")
print(f"Using SMTP: {smtp_host}:{smtp_port}")
print(f"From: {from_email}")
print("\nThis email will include:")
print("  ✓ YTM blue gradient banner")
print("  ✓ Transparent logo (YTM_Logo_byandfor_300.webp)")
print("  ✓ Brand name with Y, T, M emphasis in sage green")
print("  ✓ Purple gradient button (secondary CTA)")
print("  ✓ Alert yellow warning box")
print("  ✓ System fonts for email client compatibility")
print("  ✓ No emoji icons")

confirm = input("\nSend test email? (y/n): ").strip().lower()
if confirm != 'y':
    print("Cancelled.")
    sys.exit(0)

# Create test verification link
verification_link = "https://yourtrainingmonkey.com/verify-email?token=test123abc456def789"

# Build email subject
subject = "Verify Your Email - Your Training Monkey"

# HTML body with new branding
html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; line-height: 1.6; color: #1f2937; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8fafc;">
    <div style="background: linear-gradient(90deg, rgba(230, 240, 255, 0.92) 0%, rgba(125, 156, 184, 0.92) 50%, rgba(27, 46, 75, 0.92) 100%); border-radius: 12px; padding: 30px; margin: 20px 0;">
        <!-- Header -->
        <div style="text-align: center; margin-bottom: 30px;">
            <img src="https://yourtrainingmonkey.com/static/images/YTM_Logo_byandfor_300.png" alt="Your Training Monkey Logo" style="max-width: 200px; height: auto; margin-bottom: 10px; display: block; margin-left: auto; margin-right: auto;">
            <h1 style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; color: white; font-size: 24px; font-weight: 600; margin: 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);">Verify Your Email Address</h1>
        </div>

        <!-- Content -->
        <div style="background: white; border-radius: 12px; padding: 30px; margin: 20px 0; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);">
            <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; margin: 0 0 16px 0; color: #1f2937; font-size: 16px; line-height: 1.6;">
                Welcome to <span style="font-weight: 900; letter-spacing: 0.10em; text-transform: uppercase; font-variant: small-caps;"><span style="font-size: 1.35em; color: #15803D; font-variant: normal; font-weight: 900; text-shadow: 2px 2px 3px rgba(21,128,61,0.4);">Y</span>OUR <span style="font-size: 1.35em; color: #15803D; font-variant: normal; font-weight: 900; text-shadow: 2px 2px 3px rgba(21,128,61,0.4);">T</span>RAINING <span style="font-size: 1.35em; color: #15803D; font-variant: normal; font-weight: 900; text-shadow: 2px 2px 3px rgba(21,128,61,0.4);">M</span>ONKEY</span>!
            </p>

            <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; margin: 0 0 16px 0; color: #1f2937; font-size: 16px; line-height: 1.6;">
                To complete your registration and start tracking your training, please verify your email address by clicking the button below:
            </p>

            <div style="text-align: center; margin: 25px 0;">
                <a href="{verification_link}" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 15px 40px; text-decoration: none; border-radius: 12px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);">Verify My Email</a>
            </div>

            <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; margin: 25px 0 8px 0; font-size: 14px; color: #64748b; line-height: 1.6;">
                Or copy and paste this link into your browser:
            </p>
            <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; word-break: break-all; color: #667eea; font-size: 13px; background: #f8fafc; padding: 10px; border-radius: 6px; margin: 0 0 16px 0; line-height: 1.6;">
                {verification_link}
            </p>

            <div style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 8px; padding: 15px; margin-top: 25px;">
                <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; margin: 0; color: #92400e; font-size: 16px; line-height: 1.6;">
                    <strong style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;">Important:</strong> This verification link expires in 48 hours. You won't be able to access your dashboard until you verify your email.
                </p>
            </div>

            <div style="background: #dbeafe; border: 2px solid #3b82f6; border-radius: 8px; padding: 15px; margin-top: 15px;">
                <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; margin: 0; color: #1e40af; font-size: 14px; line-height: 1.6;">
                    <strong>Note:</strong> This is a test email. The verification link is not functional.
                </p>
            </div>
        </div>

        <!-- Footer -->
        <div style="text-align: center; color: rgba(255, 255, 255, 0.9); font-size: 14px; margin-top: 20px;">
            <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; margin: 0 0 10px 0; line-height: 1.6;">
                If you didn't create an account with <span style="font-weight: 900; letter-spacing: 0.10em; text-transform: uppercase; font-variant: small-caps;"><span style="font-size: 1.35em; color: #16A34A; font-variant: normal; font-weight: 900; text-shadow: 2px 2px 3px rgba(22,163,74,0.4);">Y</span>OUR <span style="font-size: 1.35em; color: #16A34A; font-variant: normal; font-weight: 900; text-shadow: 2px 2px 3px rgba(22,163,74,0.4);">T</span>RAINING <span style="font-size: 1.35em; color: #16A34A; font-variant: normal; font-weight: 900; text-shadow: 2px 2px 3px rgba(22,163,74,0.4);">M</span>ONKEY</span>, you can safely ignore this email.
            </p>
            <p style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; margin: 0; line-height: 1.6;">
                Need help? Contact us at <a href="mailto:support@yourtrainingmonkey.com" style="color: #E6F0FF; text-decoration: underline;">support@yourtrainingmonkey.com</a>
            </p>
        </div>
    </div>
</body>
</html>
"""

# Plain text version
text_body = f"""
Your Training Monkey - Verify Your Email

Welcome to Your Training Monkey!

To complete your registration and start tracking your training, please verify your email address by clicking this link:

{verification_link}

IMPORTANT: This verification link expires in 48 hours. You won't be able to access your dashboard until you verify your email.

Note: This is a test email. The verification link is not functional.

If you didn't create an account with Your Training Monkey, you can safely ignore this email.

Need help? Contact us at support@yourtrainingmonkey.com

---
Your Training Monkey - Prevent Injuries, Train Smarter
"""

# Send email
print("\nSending...")
try:
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = test_email

    # Attach both versions
    part1 = MIMEText(text_body, 'plain')
    part2 = MIMEText(html_body, 'html')
    msg.attach(part1)
    msg.attach(part2)

    # Send via SMTP
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    print("\n" + "="*60)
    print("✅ VERIFICATION EMAIL SENT SUCCESSFULLY!")
    print("="*60)
    print(f"\nCheck {test_email} inbox (and spam folder)")
    print("\nVerify the new branding:")
    print("  ✓ Blue gradient banner (not green)")
    print("  ✓ Transparent logo displaying correctly")
    print("  ✓ Y, T, M letters in sage green (#6B8F7F)")
    print("  ✓ Purple 'Verify My Email' button")
    print("  ✓ Yellow alert box for expiration notice")
    print("  ✓ Proper fonts rendering (sans-serif)")
    print("  ✓ No emoji icons")
    print("\n" + "="*60)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
