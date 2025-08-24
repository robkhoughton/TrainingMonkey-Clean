#!/usr/bin/env python3
"""
Generate password hash for Your Training Monkey user creation
Run this locally to generate the hash, then use it in Cloud SQL
"""

from werkzeug.security import generate_password_hash

# Set the password for your third beta user
password = "secondUser"  # Replace with desired password

# Generate the hash (same method used by Flask app)
password_hash = generate_password_hash(password)

print("Password Hash Generation for Your Training Monkey")
print("=" * 55)
print(f"Original Password: {password}")
print(f"Generated Hash: {password_hash}")
print("\nCopy the hash above and use it in your SQL INSERT statement")
print("Replace 'scrypt:32768:8:1$PLACEHOLDER$HASH_GOES_HERE' with the generated hash")