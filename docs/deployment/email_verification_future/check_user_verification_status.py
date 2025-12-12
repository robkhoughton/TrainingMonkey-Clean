#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check verification status for a specific user
"""
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

import db_utils

# Check rob@yourtrainingmonkey.com user
TEST_EMAIL = "rob@yourtrainingmonkey.com"

print("=" * 80)
print(f"CHECKING USER: {TEST_EMAIL}")
print("=" * 80)

try:
    user = db_utils.execute_query(
        """SELECT id, email, email_verified, email_verification_token,
                  email_verification_expires_at, registration_date, created_at
           FROM user_settings
           WHERE email = %s""",
        (TEST_EMAIL,),
        fetch=True
    )

    if not user or len(user) == 0:
        print(f"\n❌ No user found with email: {TEST_EMAIL}")
    else:
        u = user[0]
        print(f"\nUser Found:")
        print(f"  ID: {u['id']}")
        print(f"  Email: {u['email']}")
        print(f"  Email Verified: {u.get('email_verified', 'N/A')}")
        print(f"  Verification Token: {u.get('email_verification_token', 'None')}")
        print(f"  Token Expires: {u.get('email_verification_expires_at', 'N/A')}")
        print(f"  Registration Date: {u.get('registration_date', 'N/A')}")
        print(f"  Created At: {u.get('created_at', 'N/A')}")

        # Check domain pattern
        email = u['email']
        print(f"\n" + "=" * 80)
        print("DOMAIN PATTERN ANALYSIS")
        print("=" * 80)

        patterns = [
            '@training-monkey.com',
            '@yourtrainingmonkey.com',
            'training-monkey.com',
            'yourtrainingmonkey.com'
        ]

        for pattern in patterns:
            match = pattern in email
            print(f"  '{pattern}' in email: {match}")

        print(f"\n" + "=" * 80)

        if u.get('email_verified') == True:
            print("❓ User is already verified - why?")
            print("   This email should have required verification.")
        elif u.get('email_verified') == False and u.get('email_verification_token'):
            print("✅ User has verification token but not verified yet")
        elif u.get('email_verified') == False and not u.get('email_verification_token'):
            print("❌ ISSUE: User not verified AND no token")
            print("   Verification was not triggered during signup!")
        else:
            print(f"❓ Unexpected state: verified={u.get('email_verified')}, token={u.get('email_verification_token')}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Also check what the synthetic email pattern actually is
print(f"\n" + "=" * 80)
print("CHECKING SYNTHETIC EMAIL PATTERN IN CODE")
print("=" * 80)

# Look for any synthetic email examples
try:
    synthetic_users = db_utils.execute_query(
        """SELECT DISTINCT email
           FROM user_settings
           WHERE email LIKE '%training%monkey%'
           LIMIT 10""",
        fetch=True
    )

    if synthetic_users and len(synthetic_users) > 0:
        print(f"\nFound {len(synthetic_users)} emails with 'training' and 'monkey':")
        for user in synthetic_users:
            print(f"  - {user['email']}")
    else:
        print("\nNo synthetic emails found in database")

except Exception as e:
    print(f"Error checking synthetic emails: {e}")
