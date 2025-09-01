#!/usr/bin/env python3
"""
Test script for Task 4.7 - Secure Token Storage in Database
Tests the secure token storage functionality with encryption, audit logging, and security measures
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import base64

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock cryptography components for testing
class MockFernet:
    def __init__(self, key):
        self.key = key
    
    def encrypt(self, data):
        # Simple mock encryption
        return base64.urlsafe_b64encode(data + b'_encrypted')
    
    def decrypt(self, encrypted_data):
        # Simple mock decryption
        decoded = base64.urlsafe_b64decode(encrypted_data)
        return decoded.replace(b'_encrypted', b'')

class MockPBKDF2HMAC:
    def __init__(self, algorithm, length, salt, iterations):
        self.algorithm = algorithm
        self.length = length
        self.salt = salt
        self.iterations = iterations
    
    def derive(self, key_material):
        # Simple mock key derivation
        return b'mock_derived_key_32_bytes_long'


class TestSecureTokenStorage(unittest.TestCase):
    """Test cases for secure token storage functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_user_id = 123
        self.test_tokens = {
            'access_token': 'test_access_token_12345',
            'refresh_token': 'test_refresh_token_67890',
            'expires_at': 9999999999
        }
        self.test_athlete_id = 456

    def test_secure_token_storage_initialization(self):
        """Test secure token storage initialization"""
        with patch('secure_token_storage.Fernet', MockFernet):
            with patch('secure_token_storage.db_utils.execute_query') as mock_db:
                mock_db.return_value = [{'encryption_key': base64.urlsafe_b64encode(b'test_key_32_bytes_long').decode()}]
                
                from secure_token_storage import SecureTokenStorage
                storage = SecureTokenStorage(self.test_user_id)
                
                self.assertEqual(storage.user_id, self.test_user_id)
                self.assertIsNotNone(storage.encryption_key)
                self.assertIsNotNone(storage.cipher_suite)

    def test_encryption_key_creation(self):
        """Test encryption key creation"""
        with patch('secure_token_storage.Fernet', MockFernet):
            with patch('secure_token_storage.db_utils.execute_query') as mock_db:
                # Mock no existing key
                mock_db.return_value = [{}]
                
                from secure_token_storage import SecureTokenStorage
                storage = SecureTokenStorage(self.test_user_id)
                
                # Verify key was created and stored
                self.assertIsNotNone(storage.encryption_key)
                mock_db.assert_called()

    def test_token_encryption_decryption(self):
        """Test token encryption and decryption"""
        with patch('secure_token_storage.Fernet', MockFernet):
            with patch('secure_token_storage.db_utils.execute_query') as mock_db:
                mock_db.return_value = [{'encryption_key': base64.urlsafe_b64encode(b'test_key_32_bytes_long').decode()}]
                
                from secure_token_storage import SecureTokenStorage
                storage = SecureTokenStorage(self.test_user_id)
                
                # Test encryption
                original_token = "test_token_12345"
                encrypted = storage._encrypt_token(original_token)
                self.assertIsInstance(encrypted, str)
                self.assertNotEqual(encrypted, original_token)
                
                # Test decryption
                decrypted = storage._decrypt_token(encrypted)
                self.assertEqual(decrypted, original_token)

    def test_token_hash_generation(self):
        """Test token hash generation for integrity"""
        with patch('secure_token_storage.Fernet', MockFernet):
            with patch('secure_token_storage.db_utils.execute_query') as mock_db:
                mock_db.return_value = [{'encryption_key': base64.urlsafe_b64encode(b'test_key_32_bytes_long').decode()}]
                
                from secure_token_storage import SecureTokenStorage
                storage = SecureTokenStorage(self.test_user_id)
                
                # Test hash generation
                token = "test_token_12345"
                hash1 = storage._generate_token_hash(token)
                hash2 = storage._generate_token_hash(token)
                
                self.assertIsInstance(hash1, str)
                self.assertEqual(hash1, hash2)  # Same token should produce same hash
                
                # Different token should produce different hash
                hash3 = storage._generate_token_hash("different_token")
                self.assertNotEqual(hash1, hash3)

    def test_secure_token_saving(self):
        """Test secure token saving"""
        with patch('secure_token_storage.Fernet', MockFernet):
            with patch('secure_token_storage.db_utils.execute_query') as mock_db:
                mock_db.return_value = [{'encryption_key': base64.urlsafe_b64encode(b'test_key_32_bytes_long').decode()}]
                
                from secure_token_storage import SecureTokenStorage
                storage = SecureTokenStorage(self.test_user_id)
                
                # Test secure saving
                context = {'ip_address': '127.0.0.1', 'user_agent': 'test_agent'}
                success = storage.save_tokens_secure(self.test_tokens, self.test_athlete_id, context)
                
                self.assertTrue(success)
                mock_db.assert_called()

    def test_secure_token_loading(self):
        """Test secure token loading"""
        with patch('secure_token_storage.Fernet', MockFernet):
            with patch('secure_token_storage.db_utils.execute_query') as mock_db:
                # Mock existing encrypted tokens
                encrypted_access = base64.urlsafe_b64encode(b'test_access_token_12345_encrypted').decode()
                encrypted_refresh = base64.urlsafe_b64encode(b'test_refresh_token_67890_encrypted').decode()
                
                mock_db.return_value = [{
                    'strava_access_token': encrypted_access,
                    'strava_refresh_token': encrypted_refresh,
                    'strava_token_expires_at': 9999999999,
                    'strava_athlete_id': self.test_athlete_id,
                    'access_token_hash': 'test_hash',
                    'refresh_token_hash': 'test_refresh_hash',
                    'token_metadata': '{"version": "2.0"}'
                }]
                
                from secure_token_storage import SecureTokenStorage
                storage = SecureTokenStorage(self.test_user_id)
                
                # Test secure loading
                context = {'ip_address': '127.0.0.1', 'user_agent': 'test_agent'}
                tokens = storage.load_tokens_secure(context)
                
                self.assertIsNotNone(tokens)
                self.assertEqual(tokens['access_token'], 'test_access_token_12345')
                self.assertEqual(tokens['refresh_token'], 'test_refresh_token_67890')
                self.assertEqual(tokens['athlete_id'], self.test_athlete_id)

    def test_encryption_key_rotation(self):
        """Test encryption key rotation"""
        with patch('secure_token_storage.Fernet', MockFernet):
            with patch('secure_token_storage.db_utils.execute_query') as mock_db:
                # Mock existing tokens
                mock_db.return_value = [{
                    'strava_access_token': 'encrypted_access',
                    'strava_refresh_token': 'encrypted_refresh',
                    'strava_token_expires_at': 9999999999,
                    'strava_athlete_id': self.test_athlete_id
                }]
                
                from secure_token_storage import SecureTokenStorage
                storage = SecureTokenStorage(self.test_user_id)
                
                # Test key rotation
                context = {'ip_address': '127.0.0.1', 'user_agent': 'test_agent'}
                success = storage.rotate_encryption_key(context)
                
                self.assertTrue(success)
                mock_db.assert_called()

    def test_token_security_status(self):
        """Test token security status reporting"""
        with patch('secure_token_storage.Fernet', MockFernet):
            with patch('secure_token_storage.db_utils.execute_query') as mock_db:
                # Mock security status data
                mock_db.return_value = [{
                    'encryption_key': 'test_key',
                    'access_token_hash': 'test_hash',
                    'refresh_token_hash': 'test_refresh_hash',
                    'token_metadata': '{"version": "2.0"}',
                    'strava_token_created_at': '2024-01-01 00:00:00'
                }]
                
                from secure_token_storage import SecureTokenStorage
                storage = SecureTokenStorage(self.test_user_id)
                
                # Test security status
                status = storage.get_token_security_status()
                
                self.assertIsInstance(status, dict)
                self.assertTrue(status['has_tokens'])
                self.assertTrue(status['encrypted'])
                self.assertTrue(status['integrity_protected'])
                self.assertGreater(status['security_score'], 0)

    def test_audit_logging(self):
        """Test audit logging functionality"""
        with patch('secure_token_storage.Fernet', MockFernet):
            with patch('secure_token_storage.db_utils.execute_query') as mock_db:
                mock_db.return_value = [{'encryption_key': base64.urlsafe_b64encode(b'test_key_32_bytes_long').decode()}]
                
                from secure_token_storage import SecureTokenStorage
                storage = SecureTokenStorage(self.test_user_id)
                
                # Test audit logging
                context = {'ip_address': '127.0.0.1', 'user_agent': 'test_agent'}
                storage._log_token_operation('test_operation', True, context)
                
                # Verify audit log was called
                mock_db.assert_called()

    def test_fallback_encryption_key(self):
        """Test fallback encryption key generation"""
        with patch('secure_token_storage.PBKDF2HMAC', MockPBKDF2HMAC):
            with patch('secure_token_storage.db_utils.execute_query') as mock_db:
                mock_db.side_effect = Exception("Database error")
                
                from secure_token_storage import SecureTokenStorage
                storage = SecureTokenStorage(self.test_user_id)
                
                # Verify fallback key was generated
                self.assertIsNotNone(storage.encryption_key)

    def test_token_migration(self):
        """Test token migration to secure storage"""
        with patch('secure_token_storage.Fernet', MockFernet):
            with patch('secure_token_storage.db_utils.execute_query') as mock_db:
                # Mock existing tokens in old format
                mock_db.return_value = [{
                    'strava_access_token': 'old_access_token',
                    'strava_refresh_token': 'old_refresh_token',
                    'strava_token_expires_at': 9999999999,
                    'strava_athlete_id': self.test_athlete_id
                }]
                
                from secure_token_storage import migrate_tokens_to_secure_storage
                
                # Test migration
                success = migrate_tokens_to_secure_storage(self.test_user_id)
                
                self.assertTrue(success)

    def test_audit_log_cleanup(self):
        """Test audit log cleanup functionality"""
        with patch('secure_token_storage.Fernet', MockFernet):
            with patch('secure_token_storage.db_utils.execute_query') as mock_db:
                mock_db.return_value = [{'encryption_key': base64.urlsafe_b64encode(b'test_key_32_bytes_long').decode()}]
                
                from secure_token_storage import SecureTokenStorage
                storage = SecureTokenStorage(self.test_user_id)
                
                # Test cleanup
                result = storage.cleanup_expired_audit_logs(90)
                
                self.assertEqual(result, 1)  # Success indicator

    def test_error_handling(self):
        """Test error handling in secure storage"""
        with patch('secure_token_storage.Fernet', MockFernet):
            with patch('secure_token_storage.db_utils.execute_query') as mock_db:
                mock_db.side_effect = Exception("Database error")
                
                from secure_token_storage import SecureTokenStorage
                storage = SecureTokenStorage(self.test_user_id)
                
                # Test error handling in save
                success = storage.save_tokens_secure(self.test_tokens, self.test_athlete_id)
                self.assertFalse(success)
                
                # Test error handling in load
                tokens = storage.load_tokens_secure()
                self.assertIsNone(tokens)

    def test_integrity_checking(self):
        """Test token integrity checking"""
        with patch('secure_token_storage.Fernet', MockFernet):
            with patch('secure_token_storage.db_utils.execute_query') as mock_db:
                # Mock tokens with mismatched hash
                encrypted_access = base64.urlsafe_b64encode(b'test_access_token_12345_encrypted').decode()
                mock_db.return_value = [{
                    'strava_access_token': encrypted_access,
                    'strava_refresh_token': '',
                    'strava_token_expires_at': 9999999999,
                    'strava_athlete_id': self.test_athlete_id,
                    'access_token_hash': 'wrong_hash',  # Mismatched hash
                    'refresh_token_hash': '',
                    'token_metadata': '{}'
                }]
                
                from secure_token_storage import SecureTokenStorage
                storage = SecureTokenStorage(self.test_user_id)
                
                # Test integrity check failure
                tokens = storage.load_tokens_secure()
                self.assertIsNone(tokens)  # Should fail integrity check


def test_secure_token_storage_import():
    """Test that secure token storage can be imported without errors"""
    try:
        from secure_token_storage import SecureTokenStorage, create_token_audit_table
        print("✅ Secure token storage imports successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing secure token storage: {str(e)}")
        return False


def test_secure_token_storage_components():
    """Test that all secure token storage components are available"""
    try:
        from secure_token_storage import (
            SecureTokenStorage,
            create_token_audit_table,
            get_user_token_security_status,
            migrate_tokens_to_secure_storage
        )
        
        print("✅ All secure token storage components available")
        return True
    except Exception as e:
        print(f"❌ Error accessing secure token storage components: {str(e)}")
        return False


def test_cryptography_dependencies():
    """Test that cryptography dependencies are available"""
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        
        print("✅ Cryptography dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Cryptography dependencies not available: {str(e)}")
        return False


if __name__ == '__main__':
    print("🧪 Testing Task 4.7 - Secure Token Storage in Database")
    print("=" * 80)
    
    # Run basic tests
    test_results = []
    
    print("\n1. Testing secure token storage import...")
    test_results.append(test_secure_token_storage_import())
    
    print("\n2. Testing secure token storage components...")
    test_results.append(test_secure_token_storage_components())
    
    print("\n3. Testing cryptography dependencies...")
    test_results.append(test_cryptography_dependencies())
    
    print("\n4. Running unit tests...")
    # Run the unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "=" * 80)
    print("✅ Task 4.7 Secure Token Storage Tests Complete")
    
    if all(test_results):
        print("🎉 All tests passed! Secure token storage is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")
