# create_admin.py
import sys
import os
from getpass import getpass

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth import User
from db_utils import initialize_db


def create_admin_user():
    initialize_db()  # Make sure DB is ready

    print("Create Admin User")
    print("-----------------")

    email = input("Email: ").strip()

    # Get password with confirmation
    while True:
        password = getpass("Password: ")
        if len(password) < 8:
            print("Password must be at least 8 characters long.")
            continue

        confirm = getpass("Confirm password: ")
        if password != confirm:
            print("Passwords don't match. Please try again.")
            continue
        break

    # Get HR parameters
    resting_hr = input("Resting Heart Rate (bpm) [60]: ").strip() or 60
    max_hr = input("Maximum Heart Rate (bpm) [180]: ").strip() or 180
    gender = input("Gender (male/female) [male]: ").strip().lower() or "male"

    # Create the user
    user = User.create(
        email=email,
        password=password,
        resting_hr=int(resting_hr),
        max_hr=int(max_hr),
        gender=gender
    )

    if user:
        print(f"Admin user '{email}' created successfully!")
    else:
        print("Failed to create admin user. Check logs for details.")


if __name__ == "__main__":
    create_admin_user()