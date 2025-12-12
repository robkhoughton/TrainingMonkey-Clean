#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Email Verification with New Branding
Sends a real verification email using the actual email_verification module
"""

import os
import sys
from pathlib import Path

# Add app directory to path so we can import modules
app_dir = Path(__file__).parent.parent.parent / 'app'
sys.path.insert(0, str(app_dir))

# Change to app directory for relative imports
os.chdir(app_dir)

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables from project root
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / '.env'
if not env_path.exists():
    # Try app directory
    env_path = app_dir / '.env'
load_dotenv(dotenv_path=env_path)

# Import email verification core functions directly
try:
    from email_verification.core import send_verification_email
except ImportError:
    # If that doesn't work, try direct import
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "email_verification_core",
        app_dir / "email_verification" / "core.py"
    )
    email_verification_core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(email_verification_core)
    send_verification_email = email_verification_core.send_verification_email

print("="*60)
print("EMAIL VERIFICATION BRANDING TEST")
print("="*60)

# Configuration
test_user_id = 999999  # Fake user ID for testing
test_email = input("\nEnter your email address to receive test: ").strip()

if not test_email:
    print("❌ Email address required")
    sys.exit(1)

# Verify SMTP configuration
smtp_configured = all([
    os.environ.get('SMTP_HOST'),
    os.environ.get('SMTP_USER'),
    os.environ.get('SMTP_PASSWORD'),
])

if not smtp_configured:
    print("\n❌ SMTP not configured!")
    print("Required environment variables:")
    print("  - SMTP_HOST")
    print("  - SMTP_USER")
    print("  - SMTP_PASSWORD")
    print("  - SMTP_FROM_EMAIL (optional)")
    sys.exit(1)

print(f"\nSending verification email to: {test_email}")
print(f"Using SMTP: {os.environ.get('SMTP_HOST')}")
print(f"From: {os.environ.get('SMTP_FROM_EMAIL', 'noreply@yourtrainingmonkey.com')}")
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

print("\nSending...")
try:
    success, error = send_verification_email(
        user_id=test_user_id,
        email=test_email,
        base_url="https://yourtrainingmonkey.com"
    )

    if success:
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
    else:
        print(f"\n❌ Failed to send email: {error}")
        sys.exit(1)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
