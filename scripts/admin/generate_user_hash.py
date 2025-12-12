# generate_user_hash.py - Create password hash for new user
from werkzeug.security import generate_password_hash


def create_user_hash():
    print("=== Create New User Password Hash ===")
    print()

    # Get user details
    email = input("Enter email for new user: ").strip()
    password = input("Enter password (min 8 chars): ").strip()

    # Validate input
    if len(password) < 8:
        print("❌ Password must be at least 8 characters long")
        return

    if "@" not in email:
        print("❌ Please enter a valid email address")
        return

    # Get optional HR parameters
    print("\nOptional heart rate parameters (press Enter for defaults):")
    resting_hr = input("Resting Heart Rate [60]: ").strip() or "60"
    max_hr = input("Maximum Heart Rate [180]: ").strip() or "180"
    gender = input("Gender (male/female) [male]: ").strip().lower() or "male"

    # Generate secure hash
    password_hash = generate_password_hash(password)

    print("\n" + "=" * 60)
    print("✅ PASSWORD HASH GENERATED SUCCESSFULLY")
    print("=" * 60)
    print()
    print("Copy and paste this SQL command into Google Cloud SQL:")
    print()
    print("INSERT INTO user_settings (email, password_hash, resting_hr, max_hr, gender, is_admin)")
    print(f"VALUES ('{email}', '{password_hash}', {resting_hr}, {max_hr}, '{gender}', false);")
    print()
    print("=" * 60)
    print("Save this information securely:")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"Resting HR: {resting_hr}")
    print(f"Max HR: {max_hr}")
    print(f"Gender: {gender}")
    print("=" * 60)


if __name__ == "__main__":
    create_user_hash()