#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic: Email Verification Deployment Status
Checks what's actually deployed and working
"""
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

import db_utils

print("=" * 80)
print("EMAIL VERIFICATION DEPLOYMENT DIAGNOSTIC")
print("=" * 80)

# Test 1: Check if email_verification module exists and can be imported
print("\n1. Testing email_verification module import...")
try:
    import email_verification
    print("   ✅ email_verification module can be imported")

    # Check for required functions
    required_functions = [
        'send_verification_email',
        'verify_token',
        'is_email_verified',
        'needs_verification',
        'create_verification_token'
    ]

    for func_name in required_functions:
        if hasattr(email_verification, func_name):
            print(f"   ✅ Function '{func_name}' exists")
        else:
            print(f"   ❌ Function '{func_name}' MISSING")

except ImportError as e:
    print(f"   ❌ CANNOT IMPORT email_verification module!")
    print(f"   Error: {e}")
    print(f"   This is why verification failed!")
except Exception as e:
    print(f"   ❌ Error importing: {e}")

# Test 2: Check if template exists
print("\n2. Checking email_verification_pending.html template...")
template_path = Path(__file__).parent / 'templates' / 'email_verification_pending.html'
if template_path.exists():
    print(f"   ✅ Template exists at {template_path}")
else:
    print(f"   ❌ Template NOT FOUND at {template_path}")

# Test 3: Check test user status
print("\n3. Checking test user rob@yourtrainingmonkey.com...")
try:
    user = db_utils.execute_query(
        """SELECT id, email, email_verified, email_verification_token,
                  registration_date
           FROM user_settings
           WHERE email = %s""",
        ('rob@yourtrainingmonkey.com',),
        fetch=True
    )

    if user and len(user) > 0:
        u = user[0]
        print(f"   User ID: {u['id']}")
        print(f"   Email: {u['email']}")
        print(f"   Verified: {u.get('email_verified')}")
        print(f"   Has Token: {u.get('email_verification_token') is not None}")
        print(f"   Registered: {u.get('registration_date')}")

        if not u.get('email_verified') and not u.get('email_verification_token'):
            print("\n   ❌ PROBLEM: User not verified AND no token")
            print("   This means verification was never attempted")
    else:
        print("   ⚠️  User not found")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Check application logs for this user's signup
print("\n4. Checking for application logs...")
print("   Looking for log entries related to user signup...")

try:
    # Get most recent users to check log patterns
    recent = db_utils.execute_query(
        """SELECT id, email, registration_date
           FROM user_settings
           WHERE registration_date > NOW() - INTERVAL '24 hours'
           ORDER BY registration_date DESC
           LIMIT 5""",
        fetch=True
    )

    if recent:
        print(f"\n   Recent signups in last 24 hours:")
        for r in recent:
            print(f"   - ID {r['id']}: {r['email']} at {r['registration_date']}")
    else:
        print("   No recent signups found")

except Exception as e:
    print(f"   Error: {e}")

# Test 5: Test sending verification email to test user
print("\n5. Testing verification email send (dry run)...")
try:
    from email_verification import send_verification_email

    user = db_utils.execute_query(
        "SELECT id, email FROM user_settings WHERE email = %s",
        ('rob@yourtrainingmonkey.com',),
        fetch=True
    )

    if user and len(user) > 0:
        user_id = user[0]['id']
        email = user[0]['email']

        print(f"   Would send verification email to {email} (user {user_id})")
        print(f"   Email domain: {email.split('@')[1]}")
        print(f"   Is synthetic (@training-monkey.com): {'@training-monkey.com' in email}")
        print(f"   Should trigger verification: {'@training-monkey.com' not in email}")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Summary
print("\n" + "=" * 80)
print("DIAGNOSTIC SUMMARY")
print("=" * 80)

try:
    import email_verification
    module_ok = True
except:
    module_ok = False

template_ok = template_path.exists()

if module_ok and template_ok:
    print("✅ Email verification files are present")
    print("\nThe issue is likely:")
    print("1. Code bug in strava_app.py (lines 722-728 need return statements)")
    print("2. OR email sending failed but error was suppressed")
    print("\nRecommendation:")
    print("- Check application logs for user ID 100 signup")
    print("- Look for 'Error in verification flow' messages")
    print("- Fix the graceful degradation bug (add return statements)")
else:
    print("❌ Email verification files are MISSING")
    print("\nMissing components:")
    if not module_ok:
        print("- email_verification.py module")
    if not template_ok:
        print("- email_verification_pending.html template")
    print("\nThese files need to be deployed to production")

print("=" * 80)
