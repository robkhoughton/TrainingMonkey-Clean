# enhanced_token_management.py
# Simple, reliable token management for Strava Training Dashboard

import time
import logging
from datetime import datetime
from stravalib.client import Client
import db_utils

logger = logging.getLogger(__name__)


class SimpleTokenManager:
    """Simple token management with database storage"""

    def __init__(self, user_id=1):
        """Initialize for single user"""
        self.user_id = user_id
        self.token_buffer_minutes = 30  # Refresh 30 minutes before expiration

    def get_user_strava_credentials(self):
        """Get Strava credentials for this specific user from database"""
        try:
            # Check for user-specific credentials in database
            query = """
                SELECT user_strava_client_id, user_strava_client_secret 
                FROM user_settings 
                WHERE id = ?
            """
            result = db_utils.execute_query(query, (self.user_id,), fetch=True)

            if result and result[0] and result[0]['user_strava_client_id']:
                logger.info(f"Using user-specific Strava credentials for user {self.user_id}")
                return result[0]['user_strava_client_id'], result[0]['user_strava_client_secret']

            # Fallback: Try shared config file (for backward compatibility)
            logger.info(f"No user-specific credentials found for user {self.user_id}, trying shared config")

            from strava_training_load import load_config
            config = load_config()
            client_id, client_secret, _ = config or (None, None, None)

            if client_id and client_secret:
                logger.info(f"Using shared Strava credentials for user {self.user_id}")
                return client_id, client_secret

            # No credentials found anywhere
            logger.error(f"No Strava credentials available for user {self.user_id}")
            return None, None

        except Exception as e:
            logger.error(f"Error getting Strava credentials for user {self.user_id}: {str(e)}")
            return None, None

    def save_user_strava_credentials(self, client_id, client_secret):
        """Save user's Strava app credentials to database"""
        try:
            logger.info(f"Saving Strava credentials for user {self.user_id}")

            query = """
                UPDATE user_settings 
                SET user_strava_client_id = ?, user_strava_client_secret = ?
                WHERE id = ?
            """

            db_utils.execute_query(query, (client_id, client_secret, self.user_id))

            logger.info(f"Successfully saved Strava credentials for user {self.user_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving Strava credentials for user {self.user_id}: {str(e)}")
            return False

    def save_tokens_to_database(self, tokens, athlete_id=None):
        """Save tokens to database - simple and reliable"""
        try:
            logger.info(f"Saving tokens to database for user {self.user_id}")

            # Simple update query
            query = """
                UPDATE user_settings 
                SET strava_access_token = ?,
                    strava_refresh_token = ?,
                    strava_token_expires_at = ?,
                    strava_athlete_id = ?,
                    strava_token_created_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """

            db_utils.execute_query(query, (
                tokens['access_token'],
                tokens.get('refresh_token'),
                tokens.get('expires_at'),
                athlete_id,
                self.user_id
            ))

            logger.info("Tokens saved successfully to database")
            return True

        except Exception as e:
            logger.error(f"Error saving tokens to database: {str(e)}")
            return False

    def load_tokens_from_database(self):
        """Load tokens from database - simple and reliable"""
        try:
            query = """
                SELECT strava_access_token, strava_refresh_token, strava_token_expires_at,
                       strava_athlete_id
                FROM user_settings 
                WHERE id = ?
            """

            result = db_utils.execute_query(query, (self.user_id,), fetch=True)

            if result and result[0] and result[0]['strava_access_token']:
                tokens = {
                    'access_token': result[0]['strava_access_token'],
                    'refresh_token': result[0]['strava_refresh_token'],
                    'expires_at': result[0]['strava_token_expires_at'],
                    'athlete_id': result[0]['strava_athlete_id']
                }
                logger.info("Tokens loaded successfully from database")
                return tokens
            else:
                logger.info("No tokens found in database")
                return None

        except Exception as e:
            logger.error(f"Error loading tokens from database: {str(e)}")
            return None

    def is_token_expired_or_expiring_soon(self, tokens=None):
        """Check if token needs refresh - simple check"""
        if not tokens:
            tokens = self.load_tokens_from_database()

        if not tokens or 'expires_at' not in tokens:
            logger.info("No tokens or expiration time - treating as expired")
            return True

        current_time = int(time.time())
        expires_at = tokens['expires_at']
        buffer_seconds = self.token_buffer_minutes * 60

        time_until_expiry = expires_at - current_time
        needs_refresh = time_until_expiry <= buffer_seconds

        if needs_refresh:
            logger.info(f"Token needs refresh - expires in {time_until_expiry // 60} minutes")
        else:
            logger.info(f"Token still valid - expires in {time_until_expiry // 3600} hours")

        return needs_refresh

    def refresh_strava_tokens(self):
        """Refresh tokens using user-specific credentials from database"""
        try:
            logger.info(f"Starting token refresh for user {self.user_id}...")

            tokens = self.load_tokens_from_database()
            if not tokens or 'refresh_token' not in tokens:
                logger.error(f"No refresh token available for user {self.user_id}")
                return None

            # Get user-specific credentials from database (FIXED)
            client_id, client_secret = self.get_user_strava_credentials()

            if not client_id or not client_secret:
                logger.error(f"No client credentials available for user {self.user_id}")
                return None

            logger.info(f"Refreshing tokens for user {self.user_id} using client_id: {client_id[:8]}...")

            # Refresh the token
            from stravalib.client import Client
            client = Client()

            try:
                refresh_response = client.refresh_access_token(
                    client_id=client_id,
                    client_secret=client_secret,
                    refresh_token=tokens['refresh_token']
                )

                logger.info(f"Strava API refresh successful for user {self.user_id}")

            except Exception as strava_error:
                logger.error(f"Strava API refresh failed for user {self.user_id}: {str(strava_error)}")
                return None

            # Save new tokens
            new_tokens = {
                'access_token': refresh_response['access_token'],
                'refresh_token': refresh_response['refresh_token'],
                'expires_at': refresh_response['expires_at']
            }

            success = self.save_tokens_to_database(new_tokens, tokens.get('athlete_id'))

            if success:
                logger.info(f"Token refresh completed successfully for user {self.user_id}")
                return new_tokens
            else:
                logger.error(f"Failed to save refreshed tokens for user {self.user_id}")
                return None

        except Exception as e:
            logger.error(f"Error refreshing tokens for user {self.user_id}: {str(e)}")
            return None

    def get_working_strava_client(self):
        """Get a working Strava client - handles refresh automatically"""
        try:
            logger.info("Getting working Strava client...")

            # Load current tokens
            tokens = self.load_tokens_from_database()

            if not tokens:
                logger.error("No tokens available - need to run OAuth flow")
                return None

            # Check if refresh needed
            if self.is_token_expired_or_expiring_soon(tokens):
                logger.info("Token needs refresh - refreshing now...")
                tokens = self.refresh_strava_tokens()

                if not tokens:
                    logger.error("Token refresh failed")
                    return None

            # Create client with valid token
            client = Client(access_token=tokens['access_token'])

            # Quick test to make sure it works
            try:
                athlete = client.get_athlete()
                logger.info(f"Successfully connected as {athlete.firstname} {athlete.lastname}")
                return client
            except Exception as e:
                logger.error(f"Token validation failed: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"Error getting working client: {str(e)}")
            return None

    def get_simple_token_status(self):
        """Get simple token status for monitoring"""
        try:
            tokens = self.load_tokens_from_database()

            if not tokens:
                return {
                    'status': 'no_tokens',
                    'message': 'No tokens found - need OAuth setup',
                    'needs_auth': True
                }

            current_time = int(time.time())
            expires_at = tokens.get('expires_at', 0)
            time_until_expiry = expires_at - current_time

            if time_until_expiry <= 0:
                status = 'expired'
                message = 'Tokens have expired'
            elif time_until_expiry <= (self.token_buffer_minutes * 60):
                status = 'expiring_soon'
                message = f'Tokens expire in {time_until_expiry // 60} minutes'
            else:
                status = 'valid'
                message = f'Tokens valid for {time_until_expiry // 3600} hours'

            return {
                'status': status,
                'message': message,
                'expires_in_hours': round(time_until_expiry / 3600, 1),
                'athlete_id': tokens.get('athlete_id'),
                'needs_auth': status == 'expired'
            }

        except Exception as e:
            logger.error(f"Error getting token status: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'needs_auth': True
            }


# Simple functions that use the token manager
def get_valid_strava_client(user_id=1):
    """Simple function to get a working Strava client"""
    token_manager = SimpleTokenManager(user_id)
    return token_manager.get_working_strava_client()


def check_token_status(user_id=1):
    """Simple function to check token status"""
    token_manager = SimpleTokenManager(user_id)
    return token_manager.get_simple_token_status()


def refresh_tokens_if_needed(user_id=1):
    """Simple function to refresh tokens if needed"""
    token_manager = SimpleTokenManager(user_id)

    if token_manager.is_token_expired_or_expiring_soon():
        logger.info("Tokens need refresh - refreshing now...")
        return token_manager.refresh_strava_tokens()
    else:
        logger.info("Tokens still valid - no refresh needed")
        return token_manager.load_tokens_from_database()