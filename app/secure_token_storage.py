#!/usr/bin/env python3
"""
Secure Token Storage for Training Monkey™ Dashboard
Implements encryption, audit logging, and security measures for OAuth tokens
"""

import os
import json
import base64
import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import db_utils

logger = logging.getLogger(__name__)


class SecureTokenStorage:
    """Secure token storage with encryption and audit logging"""

    def __init__(self, user_id: int):
        """Initialize secure token storage for a user"""
        self.user_id = user_id
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for the user"""
        try:
            # Try to get existing key from database
            result = db_utils.execute_query(
                "SELECT encryption_key FROM user_settings WHERE id = %s",
                (self.user_id,),
                fetch=True
            )
            
            if result and result[0] and result[0].get('encryption_key'):
                # Decode existing key
                return base64.urlsafe_b64decode(result[0]['encryption_key'])
            else:
                # Generate new encryption key
                new_key = Fernet.generate_key()
                
                # Store in database
                db_utils.execute_query(
                    "UPDATE user_settings SET encryption_key = %s WHERE id = %s",
                    (base64.urlsafe_b64encode(new_key).decode(), self.user_id),
                    fetch=False
                )
                
                logger.info(f"Generated new encryption key for user {self.user_id}")
                return new_key
                
        except Exception as e:
            logger.error(f"Error getting/creating encryption key for user {self.user_id}: {str(e)}")
            # Fallback to environment-based key
            return self._get_fallback_encryption_key()
    
    def _get_fallback_encryption_key(self) -> bytes:
        """Get fallback encryption key from environment"""
        try:
            # Try to get from environment
            env_key = os.environ.get('TOKEN_ENCRYPTION_KEY')
            if env_key:
                return base64.urlsafe_b64decode(env_key)
            
            # Generate from app secret
            app_secret = os.environ.get('SECRET_KEY', 'default-secret-key')
            salt = b'training_monkey_salt'  # Fixed salt for consistency
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(app_secret.encode()))
            logger.warning(f"Using fallback encryption key for user {self.user_id}")
            return key
            
        except Exception as e:
            logger.error(f"Error creating fallback encryption key: {str(e)}")
            # Last resort: generate random key
            return Fernet.generate_key()
    
    def _encrypt_token(self, token: str) -> str:
        """Encrypt a token string"""
        try:
            encrypted_data = self.cipher_suite.encrypt(token.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Error encrypting token: {str(e)}")
            raise
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token string"""
        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_token.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Error decrypting token: {str(e)}")
            raise
    
    def _generate_token_hash(self, token: str) -> str:
        """Generate a hash of the token for integrity checking"""
        try:
            # Use HMAC with a secret key for integrity
            secret = os.environ.get('TOKEN_INTEGRITY_SECRET', 'default-integrity-secret')
            return hmac.new(
                secret.encode(),
                token.encode(),
                hashlib.sha256
            ).hexdigest()
        except Exception as e:
            logger.error(f"Error generating token hash: {str(e)}")
            return ""
    
    def _log_token_operation(self, operation: str, success: bool, details: Dict[str, Any] = None):
        """Log token operations for audit trail"""
        try:
            audit_data = {
                'user_id': self.user_id,
                'operation': operation,
                'success': success,
                'timestamp': datetime.now().isoformat(),
                'ip_address': details.get('ip_address', 'unknown'),
                'user_agent': details.get('user_agent', 'unknown'),
                'details': json.dumps(details or {})
            }
            
            # Store in audit log
            db_utils.execute_query(
                """INSERT INTO token_audit_log 
                   (user_id, operation, success, timestamp, ip_address, user_agent, details)
                   VALUES (%s)""",
                (
                    audit_data['user_id'],
                    audit_data['operation'],
                    audit_data['success'],
                    audit_data['timestamp'],
                    audit_data['ip_address'],
                    audit_data['user_agent'],
                    audit_data['details']
                ),
                fetch=False
            )
            
            # Log to application log
            if success:
                logger.info(f"Token operation '{operation}' successful for user {self.user_id}")
            else:
                logger.warning(f"Token operation '{operation}' failed for user {self.user_id}")
                
        except Exception as e:
            logger.error(f"Error logging token operation: {str(e)}")
    
    def save_tokens_secure(self, tokens: Dict[str, Any], athlete_id: Optional[int] = None, 
                          context: Dict[str, Any] = None) -> bool:
        """Securely save tokens to database with encryption"""
        try:
            logger.info(f"Securely saving tokens for user {self.user_id}")
            
            # Validate tokens
            if not tokens.get('access_token'):
                raise ValueError("Access token is required")
            
            # Encrypt sensitive tokens
            encrypted_access_token = self._encrypt_token(tokens['access_token'])
            encrypted_refresh_token = self._encrypt_token(tokens.get('refresh_token', ''))
            
            # Generate integrity hashes
            access_token_hash = self._generate_token_hash(tokens['access_token'])
            refresh_token_hash = self._generate_token_hash(tokens.get('refresh_token', ''))
            
            # Add metadata
            token_metadata = {
                'encrypted_at': datetime.now().isoformat(),
                'version': '2.0',
                'algorithm': 'Fernet',
                'integrity_checked': True
            }
            
            # Save to database
            query = """
                UPDATE user_settings 
                SET strava_access_token = %s, strava_refresh_token = %s,
                    strava_token_expires_at = %s,
                    strava_athlete_id = %s,
                    strava_token_created_at = CURRENT_TIMESTAMP,
                    access_token_hash = %s,
                    refresh_token_hash = %s,
                    token_metadata = %s
                WHERE id = %s
            """
            
            db_utils.execute_query(query, (
                encrypted_access_token,
                encrypted_refresh_token,
                tokens.get('expires_at'),
                athlete_id,
                access_token_hash,
                refresh_token_hash,
                json.dumps(token_metadata),
                self.user_id
            ))
            
            # Log successful operation
            self._log_token_operation('save_tokens', True, context or {})
            
            logger.info(f"Tokens securely saved for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error securely saving tokens for user {self.user_id}: {str(e)}")
            self._log_token_operation('save_tokens', False, {'error': str(e), **(context or {})})
            return False
    
    def load_tokens_secure(self, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Securely load tokens from database with decryption and integrity checking"""
        try:
            logger.info(f"Securely loading tokens for user {self.user_id}")
            
            query = """
                SELECT strava_access_token, strava_refresh_token, strava_token_expires_at,
                       strava_athlete_id, access_token_hash, refresh_token_hash, token_metadata
                FROM user_settings 
                WHERE id = %s
            """
            
            result = db_utils.execute_query(query, (self.user_id,), fetch=True)
            
            if not result or not result[0] or not result[0]['strava_access_token']:
                logger.info(f"No tokens found for user {self.user_id}")
                return None
            
            row = result[0]
            
            # Decrypt tokens
            try:
                access_token = self._decrypt_token(row['strava_access_token'])
                refresh_token = self._decrypt_token(row['strava_refresh_token']) if row['strava_refresh_token'] else ''
            except Exception as decrypt_error:
                logger.error(f"Error decrypting tokens for user {self.user_id}: {str(decrypt_error)}")
                self._log_token_operation('load_tokens', False, {'error': 'decryption_failed', **(context or {})})
                return None
            
            # Verify integrity
            if row.get('access_token_hash'):
                expected_hash = self._generate_token_hash(access_token)
                if expected_hash != row['access_token_hash']:
                    logger.error(f"Token integrity check failed for user {self.user_id}")
                    self._log_token_operation('load_tokens', False, {'error': 'integrity_check_failed', **(context or {})})
                    return None
            
            if row.get('refresh_token_hash') and refresh_token:
                expected_hash = self._generate_token_hash(refresh_token)
                if expected_hash != row['refresh_token_hash']:
                    logger.error(f"Refresh token integrity check failed for user {self.user_id}")
                    self._log_token_operation('load_tokens', False, {'error': 'refresh_token_integrity_failed', **(context or {})})
                    return None
            
            # Parse metadata
            metadata = {}
            if row.get('token_metadata'):
                try:
                    metadata = json.loads(row['token_metadata'])
                except:
                    metadata = {}
            
            tokens = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_at': row['strava_token_expires_at'],
                'athlete_id': row['strava_athlete_id'],
                'metadata': metadata
            }
            
            # Log successful operation
            self._log_token_operation('load_tokens', True, context or {})
            
            logger.info(f"Tokens securely loaded for user {self.user_id}")
            return tokens
            
        except Exception as e:
            logger.error(f"Error securely loading tokens for user {self.user_id}: {str(e)}")
            self._log_token_operation('load_tokens', False, {'error': str(e), **(context or {})})
            return None
    
    def rotate_encryption_key(self, context: Dict[str, Any] = None) -> bool:
        """Rotate encryption key for enhanced security"""
        try:
            logger.info(f"Rotating encryption key for user {self.user_id}")
            
            # Load current tokens
            current_tokens = self.load_tokens_secure(context)
            if not current_tokens:
                logger.warning(f"No tokens to rotate for user {self.user_id}")
                return False
            
            # Generate new encryption key
            new_key = Fernet.generate_key()
            new_cipher_suite = Fernet(new_key)
            
            # Re-encrypt tokens with new key
            new_encrypted_access_token = base64.urlsafe_b64encode(
                new_cipher_suite.encrypt(current_tokens['access_token'].encode())
            ).decode()
            
            new_encrypted_refresh_token = base64.urlsafe_b64encode(
                new_cipher_suite.encrypt(current_tokens['refresh_token'].encode())
            ).decode() if current_tokens['refresh_token'] else ''
            
            # Update database with new key and re-encrypted tokens
            db_utils.execute_query(
                """UPDATE user_settings 
                   SET encryption_key = %s, strava_access_token = %s,
                       strava_refresh_token = %s,
                       token_metadata = %s
                   WHERE id = %s""",
                (
                    base64.urlsafe_b64encode(new_key).decode(),
                    new_encrypted_access_token,
                    new_encrypted_refresh_token,
                    json.dumps({
                        'key_rotated_at': datetime.now().isoformat(),
                        'version': '2.1',
                        'algorithm': 'Fernet'
                    }),
                    self.user_id
                ),
                fetch=False
            )
            
            # Update instance key
            self.encryption_key = new_key
            self.cipher_suite = new_cipher_suite
            
            # Log successful rotation
            self._log_token_operation('rotate_key', True, context or {})
            
            logger.info(f"Encryption key rotated successfully for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error rotating encryption key for user {self.user_id}: {str(e)}")
            self._log_token_operation('rotate_key', False, {'error': str(e), **(context or {})})
            return False
    
    def get_token_security_status(self) -> Dict[str, Any]:
        """Get security status of stored tokens"""
        try:
            query = """
                SELECT encryption_key, access_token_hash, refresh_token_hash, 
                       token_metadata, strava_token_created_at
                FROM user_settings 
                WHERE id = %s
            """
            
            result = db_utils.execute_query(query, (self.user_id,), fetch=True)
            
            if not result or not result[0]:
                return {
                    'has_tokens': False,
                    'encrypted': False,
                    'integrity_protected': False,
                    'security_score': 0
                }
            
            row = result[0]
            
            # Parse metadata
            metadata = {}
            if row.get('token_metadata'):
                try:
                    metadata = json.loads(row['token_metadata'])
                except:
                    metadata = {}
            
            # Calculate security score
            security_score = 0
            if row.get('encryption_key'):
                security_score += 40  # Encryption
            if row.get('access_token_hash'):
                security_score += 30  # Integrity protection
            if row.get('refresh_token_hash'):
                security_score += 20  # Refresh token protection
            if metadata.get('version') == '2.0':
                security_score += 10  # Latest version
            
            return {
                'has_tokens': True,
                'encrypted': bool(row.get('encryption_key')),
                'integrity_protected': bool(row.get('access_token_hash')),
                'refresh_protected': bool(row.get('refresh_token_hash')),
                'version': metadata.get('version', '1.0'),
                'created_at': row.get('strava_token_created_at'),
                'security_score': security_score,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting token security status for user {self.user_id}: {str(e)}")
            return {
                'has_tokens': False,
                'encrypted': False,
                'integrity_protected': False,
                'security_score': 0,
                'error': str(e)
            }
    
    def cleanup_expired_audit_logs(self, days_to_keep: int = 90) -> int:
        """Clean up old audit log entries"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            result = db_utils.execute_query(
                "DELETE FROM token_audit_log WHERE timestamp < %s",
                (cutoff_date.isoformat(),),
                fetch=False
            )
            
            logger.info(f"Cleaned up audit logs older than {days_to_keep} days")
            return 1  # Success indicator
            
        except Exception as e:
            logger.error(f"Error cleaning up audit logs: {str(e)}")
            return 0


# Global utility functions
def create_token_audit_table():
    """Create token audit log table if it doesn't exist"""
    try:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS token_audit_log (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            operation VARCHAR(50) NOT NULL,
            success BOOLEAN NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            ip_address VARCHAR(45),
            user_agent TEXT,
            details JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        db_utils.execute_query(create_table_query, fetch=False)
        logger.info("Token audit log table created/verified")
        
    except Exception as e:
        logger.error(f"Error creating token audit table: {str(e)}")


def get_user_token_security_status(user_id: int) -> Dict[str, Any]:
    """Get token security status for a user"""
    storage = SecureTokenStorage(user_id)
    return storage.get_token_security_status()


def migrate_tokens_to_secure_storage(user_id: int) -> bool:
    """Migrate existing tokens to secure storage"""
    try:
        logger.info(f"Migrating tokens to secure storage for user {user_id}")
        
        # Load existing tokens using old method
        from enhanced_token_management import SimpleTokenManager
        old_manager = SimpleTokenManager(user_id)
        old_tokens = old_manager.load_tokens_from_database()
        
        if not old_tokens:
            logger.info(f"No tokens to migrate for user {user_id}")
            return True
        
        # Save using secure storage
        secure_storage = SecureTokenStorage(user_id)
        success = secure_storage.save_tokens_secure(old_tokens, old_tokens.get('athlete_id'))
        
        if success:
            logger.info(f"Successfully migrated tokens for user {user_id}")
        else:
            logger.error(f"Failed to migrate tokens for user {user_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error migrating tokens for user {user_id}: {str(e)}")
        return False



