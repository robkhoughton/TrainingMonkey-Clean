# enhanced_token_management.py
# Simple, reliable token management for Strava Training Dashboard

import time
import logging
import json
import os
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
        


    def get_centralized_strava_credentials(self):
        """Get centralized Strava credentials from strava_config.json"""
        try:
            # Try to load from strava_config.json
            config_path = os.path.join(os.path.dirname(__file__), 'strava_config.json')
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                client_id = config.get('client_id')
                client_secret = config.get('client_secret')
                
                if client_id and client_secret:
                    logger.info(f"Using centralized Strava credentials for user {self.user_id}")
                    return client_id, client_secret
                else:
                    logger.warning(f"Centralized config file exists but missing client_id or client_secret")
            
            # Fallback: Try environment variables (for backward compatibility)
            logger.info(f"Centralized config not found or incomplete for user {self.user_id}, trying environment variables")
            
            client_id = os.environ.get('STRAVA_CLIENT_ID')
            client_secret = os.environ.get('STRAVA_CLIENT_SECRET')
            
            if client_id and client_secret:
                logger.info(f"Using environment variable Strava credentials for user {self.user_id}")
                return client_id, client_secret

            # No credentials found anywhere
            logger.error(f"No centralized Strava credentials available for user {self.user_id}")
            return None, None

        except Exception as e:
            logger.error(f"Error getting centralized Strava credentials for user {self.user_id}: {str(e)}")
            return None, None

    def validate_centralized_credentials(self, client_id, client_secret):
        """Validate that centralized credentials are properly formatted"""
        try:
            if not client_id or not client_secret:
                return False, "Missing client_id or client_secret"
            
            # Basic format validation
            if not isinstance(client_id, str) or len(client_id) < 5:
                return False, "Invalid client_id format"
            
            if not isinstance(client_secret, str) or len(client_secret) < 10:
                return False, "Invalid client_secret format"
            
            return True, "Credentials appear valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def get_centralized_credentials_status(self):
        """Get status of centralized credentials"""
        try:
            client_id, client_secret = self.get_centralized_strava_credentials()
            
            if not client_id or not client_secret:
                return {
                    'status': 'unavailable',
                    'message': 'No centralized credentials found',
                    'has_credentials': False,
                    'source': None
                }
            
            # Determine source
            config_path = os.path.join(os.path.dirname(__file__), 'strava_config.json')
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    if config.get('client_id') == client_id:
                        source = 'strava_config.json'
                    else:
                        source = 'environment_variables'
                except:
                    source = 'environment_variables'
            else:
                source = 'environment_variables'
            
            # Validate credentials
            is_valid, validation_message = self.validate_centralized_credentials(client_id, client_secret)
            
            return {
                'status': 'valid' if is_valid else 'invalid',
                'message': validation_message,
                'has_credentials': True,
                'source': source,
                'client_id_preview': f"{client_id[:8]}..." if client_id else None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error checking credentials: {str(e)}",
                'has_credentials': False,
                'source': None
            }



    def save_tokens_to_database(self, tokens, athlete_id=None):
        """Save tokens to database with secure storage integration"""
        try:
            logger.info(f"Saving tokens to database for user {self.user_id}")

            # TEMPORARY FIX: Skip secure storage for existing users to avoid encryption issues
            # TODO: Implement proper token migration from plain text to encrypted storage
            logger.info(f"Using basic storage for user {self.user_id} (secure storage temporarily disabled)")

            # Fallback to basic storage
            query = """
                UPDATE user_settings 
                SET strava_access_token = %s, strava_refresh_token = %s,
                    strava_token_expires_at = %s,
                    strava_athlete_id = %s,
                    strava_token_created_at = NOW()
                WHERE id = %s
            """

            db_utils.execute_query(query, (
                tokens['access_token'],
                tokens.get('refresh_token'),
                tokens.get('expires_at'),
                athlete_id,
                self.user_id
            ))

            logger.info("Tokens saved successfully to database (basic storage)")
            return True

        except Exception as e:
            logger.error(f"Error saving tokens to database: {str(e)}")
            return False

    def load_tokens_from_database(self):
        """Load tokens from database with secure storage integration"""
        try:
            # TEMPORARY FIX: Skip secure storage for existing users to avoid encryption issues
            # TODO: Implement proper token migration from plain text to encrypted storage
            logger.info(f"Using basic storage for user {self.user_id} (secure storage temporarily disabled)")

            # Fallback to basic storage
            query = """
                SELECT strava_access_token, strava_refresh_token, strava_token_expires_at,
                       strava_athlete_id
                FROM user_settings 
                WHERE id = %s
            """

            result = db_utils.execute_query(query, (self.user_id,), fetch=True)

            if result and result[0] and result[0]['strava_access_token']:
                tokens = {
                    'access_token': result[0]['strava_access_token'],
                    'refresh_token': result[0]['strava_refresh_token'],
                    'expires_at': result[0]['strava_token_expires_at'],
                    'athlete_id': result[0]['strava_athlete_id']
                }
                logger.info("Tokens loaded successfully from database (basic storage)")
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

    def refresh_strava_tokens(self, max_retries=3, retry_delay=2):
        """Enhanced token refresh with retry logic and centralized credentials"""
        try:
            logger.info(f"Starting enhanced token refresh for user {self.user_id}...")

            # Validate refresh prerequisites
            validation_result = self._validate_refresh_prerequisites()
            if not validation_result['valid']:
                logger.error(f"Refresh prerequisites not met for user {self.user_id}: {validation_result['message']}")
                return None

            tokens = validation_result['tokens']
            client_id = validation_result['client_id']
            client_secret = validation_result['client_secret']

            # Attempt refresh with retry logic
            for attempt in range(max_retries):
                try:
                    logger.info(f"Token refresh attempt {attempt + 1}/{max_retries} for user {self.user_id}")
                    
                    refresh_result = self._attempt_token_refresh(
                        client_id, client_secret, tokens['refresh_token']
                    )
                    
                    if refresh_result['success']:
                        # Save new tokens
                        success = self.save_tokens_to_database(
                            refresh_result['tokens'], 
                            tokens.get('athlete_id')
                        )
                        
                        if success:
                            logger.info(f"Token refresh completed successfully for user {self.user_id} on attempt {attempt + 1}")
                            return refresh_result['tokens']
                        else:
                            logger.error(f"Failed to save refreshed tokens for user {self.user_id}")
                            return None
                    else:
                        # Handle specific error types
                        if self._is_retryable_error(refresh_result['error']):
                            if attempt < max_retries - 1:
                                logger.warning(f"Retryable error on attempt {attempt + 1}: {refresh_result['error']}")
                                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                                continue
                            else:
                                logger.error(f"Max retries reached for user {self.user_id}: {refresh_result['error']}")
                                return None
                        else:
                            # Non-retryable error - check if it's an invalid refresh token
                            error_message = refresh_result['error']
                            if 'invalid refresh token' in error_message.lower() or 'invalid' in error_message.lower():
                                # Handle invalid refresh token specifically
                                return self._handle_invalid_refresh_token(error_message)
                            else:
                                logger.error(f"Non-retryable error for user {self.user_id}: {error_message}")
                                return None

                except Exception as e:
                    logger.error(f"Unexpected error during refresh attempt {attempt + 1} for user {self.user_id}: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    else:
                        return None

            logger.error(f"All refresh attempts failed for user {self.user_id}")
            return None

        except Exception as e:
            logger.error(f"Error in enhanced token refresh for user {self.user_id}: {str(e)}")
            return None

    def _validate_refresh_prerequisites(self):
        """Validate that all prerequisites for token refresh are met"""
        try:
            # Check if tokens exist
            tokens = self.load_tokens_from_database()
            if not tokens or 'refresh_token' not in tokens:
                return {
                    'valid': False,
                    'message': 'No refresh token available',
                    'tokens': None,
                    'client_id': None,
                    'client_secret': None
                }

            # Check if refresh token is not empty
            if not tokens['refresh_token']:
                return {
                    'valid': False,
                    'message': 'Refresh token is empty',
                    'tokens': None,
                    'client_id': None,
                    'client_secret': None
                }

            # Get centralized credentials
            client_id, client_secret = self.get_centralized_strava_credentials()
            if not client_id or not client_secret:
                return {
                    'valid': False,
                    'message': 'No centralized credentials available',
                    'tokens': tokens,
                    'client_id': None,
                    'client_secret': None
                }

            # Validate credentials format
            is_valid, validation_message = self.validate_centralized_credentials(client_id, client_secret)
            if not is_valid:
                return {
                    'valid': False,
                    'message': f'Invalid credentials format: {validation_message}',
                    'tokens': tokens,
                    'client_id': client_id,
                    'client_secret': client_secret
                }

            return {
                'valid': True,
                'message': 'All prerequisites met',
                'tokens': tokens,
                'client_id': client_id,
                'client_secret': client_secret
            }

        except Exception as e:
            return {
                'valid': False,
                'message': f'Validation error: {str(e)}',
                'tokens': None,
                'client_id': None,
                'client_secret': None
            }

    def _attempt_token_refresh(self, client_id, client_secret, refresh_token):
        """Attempt a single token refresh operation"""
        try:
            from stravalib.client import Client
            client = Client()

            logger.info(f"Attempting token refresh with client_id: {client_id[:8]}...")

            refresh_response = client.refresh_access_token(
                client_id=client_id,
                client_secret=client_secret,
                refresh_token=refresh_token
            )

            # Validate refresh response
            if not refresh_response or 'access_token' not in refresh_response:
                return {
                    'success': False,
                    'error': 'Invalid refresh response from Strava API',
                    'tokens': None
                }

            new_tokens = {
                'access_token': refresh_response['access_token'],
                'refresh_token': refresh_response.get('refresh_token', refresh_token),  # Fallback to old if not provided
                'expires_at': refresh_response['expires_at']
            }

            logger.info(f"Strava API refresh successful")
            return {
                'success': True,
                'error': None,
                'tokens': new_tokens
            }

        except Exception as e:
            error_message = str(e)
            logger.error(f"Token refresh attempt failed: {error_message}")
            return {
                'success': False,
                'error': error_message,
                'tokens': None
            }

    def _is_retryable_error(self, error_message):
        """Determine if an error is retryable"""
        if not error_message:
            return False
        
        error_lower = error_message.lower()
        
        # Retryable errors
        retryable_patterns = [
            'timeout',
            'connection',
            'network',
            'temporary',
            'rate limit',
            'too many requests',
            'server error',
            'internal error',
            'service unavailable'
        ]
        
        # Non-retryable errors
        non_retryable_patterns = [
            'invalid refresh token',
            'invalid client',
            'unauthorized',
            'forbidden',
            'not found',
            'bad request'
        ]
        
        # Check for non-retryable errors first
        for pattern in non_retryable_patterns:
            if pattern in error_lower:
                return False
        
        # Check for retryable errors
        for pattern in retryable_patterns:
            if pattern in error_lower:
                return True
        
        # Default to retryable for unknown errors
        return True

    def _handle_invalid_refresh_token(self, error_message):
        """Handle invalid refresh token by cleaning up and marking for re-auth"""
        try:
            logger.warning(f"Handling invalid refresh token for user {self.user_id}: {error_message}")
            
            # Clear invalid tokens from database
            self._clear_invalid_tokens()
            
            # Log the cleanup action
            logger.info(f"Cleared invalid tokens for user {self.user_id} - re-authentication required")
            
            return {
                'success': False,
                'error': 'Refresh token is invalid - re-authentication required',
                'needs_reauth': True,
                'cleaned_up': True
            }
            
        except Exception as e:
            logger.error(f"Error handling invalid refresh token for user {self.user_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Error handling invalid token: {str(e)}',
                'needs_reauth': True,
                'cleaned_up': False
            }

    def _clear_invalid_tokens(self):
        """Clear invalid tokens from database"""
        try:
            query = """
                UPDATE user_settings 
                SET strava_access_token = NULL, 
                    strava_refresh_token = NULL,
                    strava_token_expires_at = NULL,
                    strava_token_created_at = NULL
                WHERE id = %s
            """
            
            db_utils.execute_query(query, (self.user_id,))
            logger.info(f"Cleared invalid tokens for user {self.user_id}")
            
        except Exception as e:
            logger.error(f"Error clearing invalid tokens for user {self.user_id}: {str(e)}")
            raise



    def get_working_strava_client(self, auto_refresh=True, validate_connection=True):
        """Get a working Strava client with enhanced refresh and validation"""
        try:
            logger.info(f"Getting working Strava client for user {self.user_id}...")

            # Load current tokens
            tokens = self.load_tokens_from_database()

            if not tokens:
                logger.error(f"No tokens available for user {self.user_id} - need to run OAuth flow")
                return None

            # Check if refresh needed
            if auto_refresh and self.is_token_expired_or_expiring_soon(tokens):
                logger.info(f"Token needs refresh for user {self.user_id} - refreshing now...")
                refresh_result = self.refresh_strava_tokens()

                if not refresh_result:
                    logger.error(f"Token refresh failed for user {self.user_id}")
                    return None
                
                tokens = refresh_result

            # Create client with valid token
            client = Client(access_token=tokens['access_token'])

            # Validate connection if requested
            if validate_connection:
                validation_result = self._validate_client_connection(client)
                if not validation_result['valid']:
                    logger.error(f"Client validation failed for user {self.user_id}: {validation_result['error']}")
                    
                    # Try one more refresh if validation fails
                    if auto_refresh:
                        logger.info(f"Attempting emergency refresh for user {self.user_id}...")
                        emergency_refresh_result = self.refresh_strava_tokens()
                        if emergency_refresh_result:
                            tokens = emergency_refresh_result
                            client = Client(access_token=tokens['access_token'])
                            validation_result = self._validate_client_connection(client)
                            if not validation_result['valid']:
                                logger.error(f"Emergency refresh also failed for user {self.user_id}")
                                return None
                        else:
                            return None
                    else:
                        return None

                logger.info(f"Successfully connected as {validation_result['athlete_name']} for user {self.user_id}")
            else:
                logger.info(f"Client created without validation for user {self.user_id}")

            return client

        except Exception as e:
            logger.error(f"Error getting working client for user {self.user_id}: {str(e)}")
            return None

    def _validate_client_connection(self, client):
        """Validate that the client can successfully connect to Strava API"""
        try:
            athlete = client.get_athlete()
            
            if not athlete:
                return {
                    'valid': False,
                    'error': 'No athlete data returned from Strava API',
                    'athlete_name': None
                }

            athlete_name = f"{athlete.firstname} {athlete.lastname}"
            
            return {
                'valid': True,
                'error': None,
                'athlete_name': athlete_name
            }

        except Exception as e:
            error_message = str(e)
            
            # Categorize the error
            if 'unauthorized' in error_message.lower() or 'invalid' in error_message.lower():
                error_type = 'authentication'
            elif 'rate limit' in error_message.lower() or 'too many requests' in error_message.lower():
                error_type = 'rate_limit'
            elif 'timeout' in error_message.lower() or 'connection' in error_message.lower():
                error_type = 'network'
            else:
                error_type = 'unknown'
            
            return {
                'valid': False,
                'error': f"{error_type}: {error_message}",
                'athlete_name': None
            }

    def _validate_tokens_with_strava(self, tokens):
        """Validate tokens by making a test API call to Strava"""
        try:
            from stravalib.client import Client
            
            # Create a client with the access token
            client = Client(access_token=tokens.get('access_token'))
            
            # Make a simple API call to validate the token
            # Using get_athlete() as it's a lightweight call
            athlete = client.get_athlete()
            
            # If we get here without an exception, the token is valid
            logger.debug(f"Token validation successful for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Token validation failed for user {self.user_id}: {str(e)}")
            return False

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

            # Check if tokens are completely invalid (NULL values)
            if not tokens.get('access_token') or not tokens.get('refresh_token'):
                return {
                    'status': 'invalid_tokens',
                    'message': 'Tokens are invalid - need to reconnect Strava',
                    'needs_auth': True
                }
            
            # Validate tokens with Strava API if they exist
            # Temporarily disabled to debug token validation issues
            # if not self._validate_tokens_with_strava(tokens):
            #     return {
            #         'status': 'invalid_tokens',
            #         'message': 'Tokens are invalid with Strava API - need to reconnect Strava',
            #         'needs_auth': True
            #     }

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
                'needs_auth': status in ['expired', 'invalid_tokens']
            }

        except Exception as e:
            logger.error(f"Error getting token status: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'needs_auth': True
            }

    def get_enhanced_token_status(self):
        """Get enhanced token status with centralized credentials info"""
        try:
            # Get basic token status
            basic_status = self.get_simple_token_status()
            
            # Get centralized credentials status
            credentials_status = self.get_centralized_credentials_status()
            
            # Combine the information
            enhanced_status = {
                **basic_status,
                'centralized_credentials': credentials_status,
                'token_management_type': 'centralized',
                'refresh_available': credentials_status.get('has_credentials', False) and basic_status.get('status') != 'no_tokens'
            }
            
            return enhanced_status

        except Exception as e:
            logger.error(f"Error getting enhanced token status: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting enhanced status: {str(e)}",
                'needs_auth': True,
                'centralized_credentials': {'status': 'error', 'message': str(e)},
                'token_management_type': 'centralized',
                'refresh_available': False
            }

    def get_token_health_summary(self):
        """Get comprehensive token health summary for monitoring"""
        try:
            enhanced_status = self.get_enhanced_token_status()
            
            # Determine overall health
            token_status = enhanced_status.get('status', 'unknown')
            credentials_status = enhanced_status.get('centralized_credentials', {}).get('status', 'unknown')
            
            if token_status == 'valid' and credentials_status == 'valid':
                overall_health = 'healthy'
                health_score = 100
            elif token_status == 'expiring_soon' and credentials_status == 'valid':
                overall_health = 'warning'
                health_score = 75
            elif token_status == 'expired' and credentials_status == 'valid':
                overall_health = 'critical'
                health_score = 25
            elif credentials_status != 'valid':
                overall_health = 'critical'
                health_score = 0
            else:
                overall_health = 'unknown'
                health_score = 50
            
            return {
                'overall_health': overall_health,
                'health_score': health_score,
                'token_status': token_status,
                'credentials_status': credentials_status,
                'needs_attention': overall_health in ['warning', 'critical'],
                'can_refresh': enhanced_status.get('refresh_available', False),
                'last_checked': datetime.now().isoformat(),
                'user_id': self.user_id
            }

        except Exception as e:
            logger.error(f"Error getting token health summary: {str(e)}")
            return {
                'overall_health': 'error',
                'health_score': 0,
                'error': str(e),
                'needs_attention': True,
                'can_refresh': False,
                'last_checked': datetime.now().isoformat(),
                'user_id': self.user_id
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


def get_centralized_credentials():
    """Get centralized Strava credentials for use by other modules"""
    try:
        import json
        import os
        
        # Try to load from strava_config.json
        config_path = os.path.join(os.path.dirname(__file__), 'strava_config.json')
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            client_id = config.get('client_id')
            client_secret = config.get('client_secret')
            
            if client_id and client_secret:
                logger.info("Successfully loaded centralized Strava credentials")
                return client_id, client_secret
        
        # Fallback: Try environment variables
        logger.info("Centralized config not found, trying environment variables")
        
        client_id = os.environ.get('STRAVA_CLIENT_ID')
        client_secret = os.environ.get('STRAVA_CLIENT_SECRET')
        
        if client_id and client_secret:
            logger.info("Successfully loaded Strava credentials from environment variables")
            return client_id, client_secret

        logger.error("No centralized Strava credentials available")
        return None, None

    except Exception as e:
        logger.error(f"Error getting centralized Strava credentials: {str(e)}")
        return None, None


def get_centralized_credentials_status():
    """Get status of centralized credentials for monitoring"""
    token_manager = SimpleTokenManager()
    return token_manager.get_centralized_credentials_status()


def get_enhanced_token_status(user_id=1):
    """Get enhanced token status with centralized credentials info"""
    token_manager = SimpleTokenManager(user_id)
    return token_manager.get_enhanced_token_status()


def get_token_health_summary(user_id=1):
    """Get comprehensive token health summary for monitoring"""
    token_manager = SimpleTokenManager(user_id)
    return token_manager.get_token_health_summary()


def validate_centralized_setup():
    """Validate that the centralized OAuth setup is properly configured"""
    try:
        # Check credentials
        credentials_status = get_centralized_credentials_status()
        
        # Check config file
        config_path = os.path.join(os.path.dirname(__file__), 'strava_config.json')
        config_exists = os.path.exists(config_path)
        
        # Check environment variables
        env_client_id = os.environ.get('STRAVA_CLIENT_ID')
        env_client_secret = os.environ.get('STRAVA_CLIENT_SECRET')
        env_available = bool(env_client_id and env_client_secret)
        
        validation_result = {
            'overall_status': 'unknown',
            'credentials_status': credentials_status,
            'config_file_exists': config_exists,
            'environment_variables_available': env_available,
            'recommendations': []
        }
        
        # Determine overall status
        if credentials_status.get('status') == 'valid':
            validation_result['overall_status'] = 'ready'
        elif credentials_status.get('has_credentials'):
            validation_result['overall_status'] = 'needs_attention'
            validation_result['recommendations'].append('Check credential format and validity')
        else:
            validation_result['overall_status'] = 'not_configured'
            validation_result['recommendations'].append('Configure centralized credentials in strava_config.json or environment variables')
        
        # Add specific recommendations
        if not config_exists and not env_available:
            validation_result['recommendations'].append('Create strava_config.json file with client_id and client_secret')
        
        if config_exists and not credentials_status.get('has_credentials'):
            validation_result['recommendations'].append('Check strava_config.json format and required fields')
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Error validating centralized setup: {str(e)}")
        return {
            'overall_status': 'error',
            'error': str(e),
            'recommendations': ['Check system configuration and file permissions']
        }


def refresh_tokens_for_user(user_id, max_retries=3):
    """Refresh tokens for a specific user with enhanced error handling"""
    try:
        token_manager = SimpleTokenManager(user_id)
        
        # Check if refresh is needed
        if not token_manager.is_token_expired_or_expiring_soon():
            logger.info(f"Tokens for user {user_id} are still valid - no refresh needed")
            return {
                'success': True,
                'message': 'Tokens are still valid',
                'refreshed': False,
                'user_id': user_id
            }
        
        # Attempt refresh
        refreshed_tokens = token_manager.refresh_strava_tokens(max_retries=max_retries)
        
        if refreshed_tokens:
            return {
                'success': True,
                'message': 'Tokens refreshed successfully',
                'refreshed': True,
                'user_id': user_id,
                'expires_at': refreshed_tokens.get('expires_at')
            }
        else:
            return {
                'success': False,
                'message': 'Token refresh failed',
                'refreshed': False,
                'user_id': user_id
            }
            
    except Exception as e:
        logger.error(f"Error refreshing tokens for user {user_id}: {str(e)}")
        return {
            'success': False,
            'message': f'Error during refresh: {str(e)}',
            'refreshed': False,
            'user_id': user_id
        }


def get_token_refresh_status(user_id):
    """Get detailed status about token refresh readiness"""
    try:
        token_manager = SimpleTokenManager(user_id)
        
        # Get current token status
        token_status = token_manager.get_simple_token_status()
        
        # Check if refresh is needed
        needs_refresh = token_manager.is_token_expired_or_expiring_soon()
        
        # Get centralized credentials status
        credentials_status = token_manager.get_centralized_credentials_status()
        
        # Determine refresh readiness
        if token_status.get('status') == 'no_tokens':
            refresh_readiness = 'no_tokens'
            readiness_message = 'No tokens available - OAuth setup required'
        elif not credentials_status.get('has_credentials'):
            refresh_readiness = 'no_credentials'
            readiness_message = 'No centralized credentials available'
        elif needs_refresh:
            refresh_readiness = 'ready'
            readiness_message = 'Tokens need refresh - ready to refresh'
        else:
            refresh_readiness = 'not_needed'
            readiness_message = 'Tokens are still valid - no refresh needed'
        
        return {
            'user_id': user_id,
            'token_status': token_status,
            'credentials_status': credentials_status,
            'needs_refresh': needs_refresh,
            'refresh_readiness': refresh_readiness,
            'readiness_message': readiness_message,
            'can_refresh': refresh_readiness == 'ready'
        }
        
    except Exception as e:
        logger.error(f"Error getting token refresh status for user {user_id}: {str(e)}")
        return {
            'user_id': user_id,
            'error': str(e),
            'refresh_readiness': 'error',
            'can_refresh': False
        }


def bulk_refresh_tokens(user_ids=None, max_retries=3):
    """Refresh tokens for multiple users"""
    try:
        if user_ids is None:
            # Get all users with tokens from database
            query = """
                SELECT id FROM user_settings 
                WHERE strava_access_token IS NOT NULL 
                  AND strava_refresh_token IS NOT NULL
            """
            result = db_utils.execute_query(query, fetch=True)
            user_ids = [user['id'] for user in result] if result else []
        
        if not user_ids:
            return {
                'success': True,
                'message': 'No users to refresh',
                'total_users': 0,
                'successful_refreshes': 0,
                'failed_refreshes': 0,
                'results': []
            }
        
        results = []
        successful = 0
        failed = 0
        
        for user_id in user_ids:
            refresh_result = refresh_tokens_for_user(user_id, max_retries)
            results.append(refresh_result)
            
            if refresh_result['success'] and refresh_result['refreshed']:
                successful += 1
            elif not refresh_result['success']:
                failed += 1
        
        return {
            'success': True,
            'message': f'Bulk refresh completed: {successful} successful, {failed} failed',
            'total_users': len(user_ids),
            'successful_refreshes': successful,
            'failed_refreshes': failed,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in bulk token refresh: {str(e)}")
        return {
            'success': False,
            'message': f'Bulk refresh error: {str(e)}',
            'total_users': 0,
            'successful_refreshes': 0,
            'failed_refreshes': 0,
            'results': []
        }

def get_all_users_needing_token_refresh():
    """Get all users who need token refresh (expired or expiring soon)"""
    try:
        query = """
            SELECT id, email, strava_access_token, strava_refresh_token, strava_token_expires_at
            FROM user_settings 
            WHERE strava_access_token IS NOT NULL 
              AND strava_refresh_token IS NOT NULL
              AND strava_token_expires_at IS NOT NULL
            ORDER BY id
        """
        
        users = db_utils.execute_query(query, fetch=True)
        users_needing_refresh = []
        
        current_time = int(time.time())
        buffer_seconds = 30 * 60  # 30 minutes buffer
        
        for user in users:
            user_id = user['id']
            expires_at = user.get('strava_token_expires_at', 0)
            
            if expires_at > 0:
                time_until_expiry = expires_at - current_time
                
                if time_until_expiry <= buffer_seconds:
                    users_needing_refresh.append({
                        'user_id': user_id,
                        'email': user['email'],
                        'expires_in_minutes': round(time_until_expiry / 60, 1),
                        'needs_refresh': True
                    })
        
        return users_needing_refresh
        
    except Exception as e:
        logger.error(f"Error getting users needing token refresh: {str(e)}")
        return []

def proactive_token_refresh_for_all_users():
    """Proactively refresh tokens for all users who need it"""
    try:
        users_needing_refresh = get_all_users_needing_token_refresh()
        
        if not users_needing_refresh:
            logger.info("No users need token refresh")
            return {
                'success': True,
                'message': 'No users need token refresh',
                'users_checked': 0,
                'users_refreshed': 0,
                'users_failed': 0
            }
        
        logger.info(f"Proactively refreshing tokens for {len(users_needing_refresh)} users")
        
        results = []
        successful_refreshes = 0
        failed_refreshes = 0
        
        for user_info in users_needing_refresh:
            user_id = user_info['user_id']
            try:
                logger.info(f"Proactively refreshing tokens for user {user_id}")
                
                token_manager = SimpleTokenManager(user_id)
                refresh_result = token_manager.refresh_strava_tokens()
                
                if refresh_result:
                    successful_refreshes += 1
                    results.append({
                        'user_id': user_id,
                        'email': user_info['email'],
                        'status': 'success',
                        'message': 'Tokens refreshed successfully'
                    })
                    logger.info(f"Successfully refreshed tokens for user {user_id}")
                else:
                    failed_refreshes += 1
                    results.append({
                        'user_id': user_id,
                        'email': user_info['email'],
                        'status': 'failed',
                        'message': 'Token refresh failed'
                    })
                    logger.error(f"Failed to refresh tokens for user {user_id}")
                    
            except Exception as e:
                failed_refreshes += 1
                results.append({
                    'user_id': user_id,
                    'email': user_info['email'],
                    'status': 'error',
                    'message': f'Error during refresh: {str(e)}'
                })
                logger.error(f"Error refreshing tokens for user {user_id}: {str(e)}")
        
        return {
            'success': True,
            'message': f'Proactive token refresh completed: {successful_refreshes} successful, {failed_refreshes} failed',
            'users_checked': len(users_needing_refresh),
            'users_refreshed': successful_refreshes,
            'users_failed': failed_refreshes,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in proactive token refresh: {str(e)}")
        return {
            'success': False,
            'message': f'Proactive refresh error: {str(e)}',
            'users_checked': 0,
            'users_refreshed': 0,
            'users_failed': 0
        }