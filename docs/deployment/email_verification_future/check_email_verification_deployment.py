#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check if email verification system is deployed by checking database schema
"""
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import db_utils

print("=" * 60)
print("CHECKING EMAIL VERIFICATION DEPLOYMENT STATUS")
print("=" * 60)

# Check if email verification columns exist in user_settings
print("\n1. Checking database schema for email verification columns...")

try:
    # Get table structure
    result = db_utils.execute_query("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'user_settings'
        AND column_name IN ('email_verified', 'email_verification_token', 'email_verification_expires_at')
        ORDER BY column_name
    """, fetch=True)

    if result and len(result) > 0:
        print("\n✅ Email verification columns found in database:")
        for col in result:
            print(f"   - {col['column_name']} ({col['data_type']}, nullable: {col['is_nullable']})")

        # Check if any users have verification data
        print("\n2. Checking if verification system has been used...")

        verification_stats = db_utils.execute_query("""
            SELECT
                COUNT(*) as total_users,
                COUNT(CASE WHEN email_verified = true THEN 1 END) as verified_users,
                COUNT(CASE WHEN email_verification_token IS NOT NULL THEN 1 END) as pending_verification
            FROM user_settings
            WHERE email NOT LIKE '%@training-monkey.com%'
        """, fetch=True)

        if verification_stats:
            stats = verification_stats[0]
            print(f"   Total users with real emails: {stats['total_users']}")
            print(f"   Verified users: {stats['verified_users']}")
            print(f"   Pending verification: {stats['pending_verification']}")

        print("\n" + "=" * 60)
        print("✅ EMAIL VERIFICATION IS DEPLOYED")
        print("=" * 60)
        print("The database schema includes email verification columns.")
        print("The system is ready to use.")

    else:
        print("\n❌ Email verification columns NOT found in database")
        print("\n" + "=" * 60)
        print("❌ EMAIL VERIFICATION IS NOT DEPLOYED")
        print("=" * 60)
        print("\nRequired columns missing from user_settings table:")
        print("  - email_verified (boolean)")
        print("  - email_verification_token (text)")
        print("  - email_verification_expires_at (timestamp)")
        print("\nYou need to run the database migration first.")

except Exception as e:
    print(f"\n❌ Error checking database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
