"""Quick script to check recent user emails"""
import sys
sys.path.insert(0, 'C:\\Users\\robho\\Documents\\TrainingMonkey-Clean\\app')

from db_utils import get_db_connection

try:
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check recent users
        print("\n=== RECENT USER SIGNUPS (Last 10) ===")
        cursor.execute("""
            SELECT id, email, registration_date, created_at,
                   CASE WHEN email LIKE '%@training-monkey.com' THEN 'SYNTHETIC' ELSE 'REAL' END as email_type
            FROM user_settings
            ORDER BY COALESCE(registration_date, created_at) DESC
            LIMIT 10
        """)

        for row in cursor.fetchall():
            print(f"ID: {row['id']}")
            print(f"  Email: {row['email']}")
            print(f"  Type: {row['email_type']}")
            print(f"  Registered: {row['registration_date'] or row['created_at']}")
            print()

        # Check email distribution
        print("\n=== EMAIL DISTRIBUTION ===")
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN email LIKE '%@training-monkey.com' THEN 1 END) as synthetic,
                COUNT(CASE WHEN email NOT LIKE '%@training-monkey.com' THEN 1 END) as real
            FROM user_settings
        """)

        row = cursor.fetchone()
        total = row['total']
        synthetic = row['synthetic']
        real = row['real']
        print(f"Total users: {total}")
        print(f"Synthetic emails: {synthetic} ({synthetic*100//total if total > 0 else 0}%)")
        print(f"Real emails: {real} ({real*100//total if total > 0 else 0}%)")

        # Check if email verification columns exist
        print("\n=== EMAIL VERIFICATION COLUMNS ===")
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'user_settings'
            AND column_name LIKE '%email%'
            ORDER BY column_name
        """)

        print("Email-related columns:")
        for row in cursor.fetchall():
            print(f"  - {row['column_name']}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
