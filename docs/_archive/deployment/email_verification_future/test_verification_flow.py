#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Test: Email Verification Flow
Tests the complete double opt-in email verification process
"""
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import db_utils
from email_verification import (
    send_verification_email,
    verify_token,
    is_email_verified,
    needs_verification,
    create_verification_token
)

print("=" * 80)
print("EMAIL VERIFICATION FLOW - END-TO-END TEST")
print("=" * 80)

# Test email address
TEST_EMAIL = "rob.houghton.ca@gmail.com"
TEST_USER_NAME = "Test User (E2E Verification)"

print(f"\nTest Email: {TEST_EMAIL}")
print(f"Test User: {TEST_USER_NAME}")

# Step 1: Check if test user exists or create one
print("\n" + "=" * 80)
print("STEP 1: Prepare Test User")
print("=" * 80)

try:
    # Check for existing test user
    existing_user = db_utils.execute_query(
        "SELECT id, email, email_verified FROM user_settings WHERE email = %s",
        (TEST_EMAIL,),
        fetch=True
    )

    if existing_user and len(existing_user) > 0:
        user_id = existing_user[0]['id']
        print(f"✅ Found existing test user (ID: {user_id})")
        print(f"   Email: {existing_user[0]['email']}")
        print(f"   Currently verified: {existing_user[0].get('email_verified', False)}")

        # Reset verification status for testing
        print("\n   Resetting verification status for fresh test...")
        db_utils.execute_query(
            """UPDATE user_settings
               SET email_verified = false,
                   email_verification_token = NULL,
                   email_verification_expires_at = NULL
               WHERE id = %s""",
            (user_id,),
            fetch=False
        )
        print("   ✅ Reset complete - user now unverified")

    else:
        print(f"⚠️  No existing user found with email {TEST_EMAIL}")
        print("\nTo properly test, we need a user in the database.")
        print("Options:")
        print("1. Sign up through the app first, or")
        print("2. Use an existing user's email address")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error preparing test user: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 2: Test verification email sending
print("\n" + "=" * 80)
print("STEP 2: Send Verification Email")
print("=" * 80)

try:
    print(f"Sending verification email to {TEST_EMAIL}...")

    success, error = send_verification_email(user_id, TEST_EMAIL)

    if success:
        print("✅ Verification email sent successfully!")
        print(f"\n📧 Check inbox: {TEST_EMAIL}")
        print("   The email should contain:")
        print("   - Your Training Monkey logo (circular design)")
        print("   - 'Verify My Email' button")
        print("   - Verification link")

        # Get the token from database to show what the link looks like
        token_data = db_utils.execute_query(
            """SELECT email_verification_token, email_verification_expires_at
               FROM user_settings WHERE id = %s""",
            (user_id,),
            fetch=True
        )

        if token_data and token_data[0]['email_verification_expires_at']:
            expires_at = token_data[0]['email_verification_expires_at']
            print(f"\n   Token expires at: {expires_at}")
            print(f"   (Valid for 48 hours)")

    else:
        print(f"❌ Failed to send verification email: {error}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error sending verification email: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Check verification status (should be unverified)
print("\n" + "=" * 80)
print("STEP 3: Check Verification Status (Before)")
print("=" * 80)

try:
    is_verified = is_email_verified(user_id)
    needs_verify = needs_verification(user_id)

    print(f"   Email verified: {is_verified}")
    print(f"   Needs verification: {needs_verify}")

    if not is_verified and needs_verify:
        print("✅ Status correct - user is unverified and needs verification")
    else:
        print("⚠️  Unexpected status")

except Exception as e:
    print(f"❌ Error checking status: {e}")

# Step 4: Wait for user to click email link
print("\n" + "=" * 80)
print("STEP 4: Manual Verification")
print("=" * 80)

print("\n📧 PLEASE DO THE FOLLOWING:")
print("   1. Check your email inbox for the verification email")
print("   2. Click the 'Verify My Email' button in the email")
print("   3. OR copy and paste the verification link from the email")
print("\nAfter clicking the link, the page should:")
print("   - Show a success message")
print("   - Log you in")
print("   - Redirect to the onboarding page")

input("\n👉 Press ENTER after you've clicked the verification link in the email...")

# Step 5: Check verification status (should be verified now)
print("\n" + "=" * 80)
print("STEP 5: Check Verification Status (After)")
print("=" * 80)

try:
    is_verified = is_email_verified(user_id)
    needs_verify = needs_verification(user_id)

    print(f"   Email verified: {is_verified}")
    print(f"   Needs verification: {needs_verify}")

    if is_verified and not needs_verify:
        print("✅ VERIFICATION SUCCESSFUL!")
        print("   User is now verified and can access the dashboard")
    else:
        print("❌ Verification did not complete")
        print("   Expected: verified=True, needs_verification=False")
        print(f"   Actual: verified={is_verified}, needs_verification={needs_verify}")

except Exception as e:
    print(f"❌ Error checking final status: {e}")

# Final Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

try:
    final_status = db_utils.execute_query(
        """SELECT email, email_verified, email_verification_token,
                  email_verification_expires_at
           FROM user_settings WHERE id = %s""",
        (user_id,),
        fetch=True
    )

    if final_status:
        status = final_status[0]
        print(f"\nFinal User Status:")
        print(f"   Email: {status['email']}")
        print(f"   Verified: {status['email_verified']}")
        print(f"   Has pending token: {status['email_verification_token'] is not None}")

        if status['email_verified']:
            print("\n✅ DOUBLE OPT-IN FLOW WORKING CORRECTLY!")
            print("\nThe complete flow has been verified:")
            print("   ✅ 1. Verification email sent with logo")
            print("   ✅ 2. User clicked verification link")
            print("   ✅ 3. Email marked as verified in database")
            print("   ✅ 4. User can now access the application")
        else:
            print("\n⚠️  User not verified - please check the verification link")

except Exception as e:
    print(f"❌ Error getting final status: {e}")

print("\n" + "=" * 80)
