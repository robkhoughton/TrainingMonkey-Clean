# auth.py

import logging
from flask_login import LoginManager, UserMixin, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from db_utils import execute_query, get_db_connection, USE_POSTGRES  # Add USE_POSTGRES here

login_manager = LoginManager()
logger = logging.getLogger(__name__)

class User(UserMixin):
    def __init__(self, id, email, password_hash, resting_hr=None, max_hr=None, gender=None, is_admin=False):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.resting_hr = resting_hr
        self.max_hr = max_hr
        self.gender = gender
        self.is_admin = is_admin # Store is_admin attribute

    @staticmethod
    def get(user_id):
        user_data = execute_query(
            "SELECT id, email, password_hash, resting_hr, max_hr, gender, is_admin FROM user_settings WHERE id = %s",
            (user_id,),
            fetch=True
        )

        if not user_data:
            return None

        user_dict = dict(user_data[0])
        return User(
            id=user_dict['id'],
            email=user_dict['email'],
            password_hash=user_dict['password_hash'],
            resting_hr=user_dict.get('resting_hr'),
            max_hr=user_dict.get('max_hr'),
            gender=user_dict.get('gender'),
            is_admin=user_dict.get('is_admin', False) # Safely get is_admin, default to False
        )

    @staticmethod
    def get_by_email(email):
        logger.info(f"auth: Attempting to get user by email: {email}")

        # Use ? syntax - db_utils will convert to %s for PostgreSQL
        user_data = execute_query(
            "SELECT id, email, password_hash, resting_hr, max_hr, gender, is_admin FROM user_settings WHERE email = ?",
            (email,),
            fetch=True
        )

        if not user_data:
            logger.warning(f"auth: User not found for email: {email}")
            return None

        user_dict = dict(user_data[0])
        logger.info(f"auth: Found user data: {user_dict}")

        return User(
            id=user_dict['id'],
            email=user_dict['email'],
            password_hash=user_dict['password_hash'],
            resting_hr=user_dict.get('resting_hr'),
            max_hr=user_dict.get('max_hr'),
            gender=user_dict.get('gender'),
            is_admin=user_dict.get('is_admin', False)
        )

    @staticmethod
    def create(email, password, resting_hr=None, max_hr=None, gender=None):
        password_hash = generate_password_hash(password)
        query = """
                INSERT INTO user_settings (
                    email, password_hash, resting_hr, max_hr, gender
                ) VALUES (%s, %s, %s, %s, %s) RETURNING id;
                """
        params = (email, password_hash, resting_hr, max_hr, gender)
        try:
            result = execute_query(query, params, fetch=True)
            return result[0]['id'] if result else None
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            return None

    @staticmethod
    def create_admin_user(email, password, resting_hr, max_hr, gender):
        import os
        logger.info(f"auth: Creating admin user: {email}")
        password_hash = generate_password_hash(password)

        try:
            # Use a single transaction for both insert and verification
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Build the insert query
                query = """
                    INSERT INTO user_settings (
                        email, password_hash, resting_hr, max_hr, gender, is_admin
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """

                # For PostgreSQL, add RETURNING clause and convert syntax
                is_postgres = os.environ.get('DATABASE_URL') is not None
                if is_postgres:
                    query += " RETURNING id"
                    query = query.replace('?', '%s')

                params = (email, password_hash, resting_hr, max_hr, gender, True)
                logger.info(f"auth: Executing query with params: {params}")

                cursor.execute(query, params)

                if is_postgres:
                    result = cursor.fetchone()
                    user_id = result['id'] if result else None
                else:
                    user_id = cursor.lastrowid

                # Commit the transaction
                conn.commit()
                logger.info(f"auth: Transaction committed. User ID: {user_id}")

                return user_id

        except Exception as e:
            logger.error(f"auth: Error creating admin user: {e}", exc_info=True)
            raise

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    logger.info(f"auth: Loading user with ID: {user_id}")
    return User.get(user_id)