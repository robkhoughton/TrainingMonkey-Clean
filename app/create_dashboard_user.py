from werkzeug.security import generate_password_hash
from db_utils import get_db_connection, initialize_db


def create_user():
    print("\nCreate New Dashboard User")
    print("-------------------------")

    # Make sure database is initialized
    initialize_db()

    email = input("Enter email address: ")
    password = input("Enter password: ")
    resting_hr = int(input("Enter resting heart rate [60]: ") or "60")
    max_hr = int(input("Enter maximum heart rate [180]: ") or "180")
    gender = input("Enter gender (male/female) [male]: ").lower() or "male"

    # Validate gender
    if gender not in ['male', 'female']:
        gender = 'male'

    # Generate password hash
    password_hash = generate_password_hash(password)

    try:
        with get_db_connection() as conn:
            # First make sure user_settings table exists
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password_hash TEXT,
                resting_hr INTEGER,
                max_hr INTEGER,
                gender TEXT,
                last_sync_date TEXT
            )
            ''')
            conn.commit()

            # Create new user
            cursor.execute(
                """
                INSERT INTO user_settings (email, password_hash, resting_hr, max_hr, gender) 
                VALUES (%s)
                """,
                (email, password_hash, resting_hr, max_hr, gender)
            )
            conn.commit()
            print(f"\nNew user {email} created successfully!")

    except Exception as e:
        print(f"\nError: {str(e)}")


if __name__ == "__main__":
    create_user()