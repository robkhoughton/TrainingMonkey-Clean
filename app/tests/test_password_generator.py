"""
Test suite for password generator module
"""

import unittest
import re
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from password_generator import SecurePasswordGenerator


class TestSecurePasswordGenerator(unittest.TestCase):
    """Test cases for SecurePasswordGenerator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = SecurePasswordGenerator()
    
    def test_generate_password_basic(self):
        """Test basic password generation"""
        password = self.generator.generate_password('basic')
        
        # Check length
        self.assertEqual(len(password), 12)
        
        # Check character requirements
        self.assertTrue(any(c in self.generator.lowercase for c in password))
        self.assertTrue(any(c in self.generator.uppercase for c in password))
        self.assertTrue(any(c in self.generator.digits for c in password))
        self.assertTrue(any(c in self.generator.special_chars for c in password))
    
    def test_generate_password_strong(self):
        """Test strong password generation"""
        password = self.generator.generate_password('strong')
        
        # Check length
        self.assertEqual(len(password), 16)
        
        # Check character requirements
        self.assertTrue(any(c in self.generator.lowercase for c in password))
        self.assertTrue(any(c in self.generator.uppercase for c in password))
        self.assertTrue(any(c in self.generator.digits for c in password))
        self.assertTrue(any(c in self.generator.special_chars for c in password))
    
    def test_generate_password_very_strong(self):
        """Test very strong password generation"""
        password = self.generator.generate_password('very_strong')
        
        # Check length
        self.assertEqual(len(password), 20)
        
        # Check character requirements
        self.assertTrue(any(c in self.generator.lowercase for c in password))
        self.assertTrue(any(c in self.generator.uppercase for c in password))
        self.assertTrue(any(c in self.generator.digits for c in password))
        self.assertTrue(any(c in self.generator.special_chars for c in password))
    
    def test_generate_password_custom_length(self):
        """Test password generation with custom length"""
        password = self.generator.generate_password('strong', length=24)
        
        # Check length
        self.assertEqual(len(password), 24)
        
        # Check character requirements
        self.assertTrue(any(c in self.generator.lowercase for c in password))
        self.assertTrue(any(c in self.generator.uppercase for c in password))
        self.assertTrue(any(c in self.generator.digits for c in password))
        self.assertTrue(any(c in self.generator.special_chars for c in password))
    
    def test_generate_password_invalid_strength(self):
        """Test password generation with invalid strength level"""
        with self.assertRaises(ValueError):
            self.generator.generate_password('invalid_strength')
    
    def test_generate_password_length_too_short(self):
        """Test password generation with length too short for requirements"""
        with self.assertRaises(ValueError):
            self.generator.generate_password('strong', length=5)
    
    def test_generate_memorable_password(self):
        """Test memorable password generation"""
        password = self.generator.generate_memorable_password(4, '-')
        
        # Check format (words separated by separator with numbers and special char)
        parts = password.split('-')
        self.assertEqual(len(parts), 6)  # 4 words + 2 numbers + 1 special char
        
        # Check that it contains words, numbers, and special characters
        self.assertTrue(any(part.isalpha() for part in parts))
        self.assertTrue(any(part.isdigit() for part in parts))
        self.assertTrue(any(any(c in self.generator.special_chars for c in part) for part in parts))
    
    def test_generate_pronounceable_password(self):
        """Test pronounceable password generation"""
        password = self.generator.generate_pronounceable_password(12)
        
        # Check length
        self.assertEqual(len(password), 12)
        
        # Check that it contains mixed character types
        self.assertTrue(any(c in self.generator.lowercase for c in password))
        self.assertTrue(any(c in self.generator.uppercase for c in password))
        self.assertTrue(any(c in self.generator.digits for c in password))
        self.assertTrue(any(c in self.generator.special_chars for c in password))
    
    def test_verify_password_requirements(self):
        """Test password requirement verification"""
        # Valid password
        config = {
            'length': 12,
            'min_lowercase': 2,
            'min_uppercase': 2,
            'min_digits': 2,
            'min_special': 1
        }
        
        valid_password = "Ab12!cDeFgHi"
        self.assertTrue(self.generator._verify_password_requirements(valid_password, config))
        
        # Invalid password (too short)
        invalid_password = "Ab12!"
        self.assertFalse(self.generator._verify_password_requirements(invalid_password, config))
        
        # Invalid password (missing character types)
        invalid_password = "abcdefghijkl"
        self.assertFalse(self.generator._verify_password_requirements(invalid_password, config))
    
    def test_get_password_strength_info(self):
        """Test password strength information retrieval"""
        info = self.generator.get_password_strength_info('strong')
        
        self.assertEqual(info['strength'], 'strong')
        self.assertEqual(info['length'], 16)
        self.assertIn('requirements', info)
        self.assertIn('entropy_bits', info)
        self.assertIn('description', info)
    
    def test_get_password_strength_info_invalid(self):
        """Test password strength info with invalid strength"""
        with self.assertRaises(ValueError):
            self.generator.get_password_strength_info('invalid')
    
    def test_validate_generated_password(self):
        """Test password validation"""
        # Valid password
        valid_password = "StrongPass123!"
        validation = self.generator.validate_generated_password(valid_password)
        
        self.assertTrue(validation['is_valid'])
        self.assertEqual(len(validation['errors']), 0)
        self.assertIn('strength_score', validation)
        
        # Invalid password
        invalid_password = "weak"
        validation = self.generator.validate_generated_password(invalid_password)
        
        self.assertFalse(validation['is_valid'])
        self.assertGreater(len(validation['errors']), 0)
    
    def test_calculate_strength_score(self):
        """Test password strength score calculation"""
        # Strong password
        strong_password = "StrongPass123!"
        score = self.generator._calculate_strength_score(strong_password)
        self.assertGreater(score, 70)
        
        # Weak password
        weak_password = "weak"
        score = self.generator._calculate_strength_score(weak_password)
        self.assertLess(score, 50)
    
    def test_password_uniqueness(self):
        """Test that generated passwords are unique"""
        passwords = set()
        
        # Generate multiple passwords
        for _ in range(10):
            password = self.generator.generate_password('strong')
            passwords.add(password)
        
        # All passwords should be unique
        self.assertEqual(len(passwords), 10)
    
    def test_memorable_password_uniqueness(self):
        """Test that memorable passwords are unique"""
        passwords = set()
        
        # Generate multiple memorable passwords
        for _ in range(10):
            password = self.generator.generate_memorable_password()
            passwords.add(password)
        
        # All passwords should be unique
        self.assertEqual(len(passwords), 10)
    
    def test_pronounceable_password_uniqueness(self):
        """Test that pronounceable passwords are unique"""
        passwords = set()
        
        # Generate multiple pronounceable passwords
        for _ in range(10):
            password = self.generator.generate_pronounceable_password()
            passwords.add(password)
        
        # All passwords should be unique
        self.assertEqual(len(passwords), 10)
    
    def test_password_entropy(self):
        """Test that generated passwords have good entropy"""
        password = self.generator.generate_password('very_strong')
        
        # Calculate approximate entropy
        char_set_size = len(self.generator.lowercase) + len(self.generator.uppercase) + len(self.generator.digits) + len(self.generator.special_chars)
        entropy = len(password) * (char_set_size ** 0.5)
        
        # Should have reasonable entropy
        self.assertGreater(entropy, 50)
    
    def test_character_distribution(self):
        """Test that generated passwords have good character distribution"""
        password = self.generator.generate_password('strong')
        
        # Count character types
        lowercase_count = sum(1 for c in password if c in self.generator.lowercase)
        uppercase_count = sum(1 for c in password if c in self.generator.uppercase)
        digit_count = sum(1 for c in password if c in self.generator.digits)
        special_count = sum(1 for c in password if c in self.generator.special_chars)
        
        # Should have reasonable distribution
        self.assertGreater(lowercase_count, 0)
        self.assertGreater(uppercase_count, 0)
        self.assertGreater(digit_count, 0)
        self.assertGreater(special_count, 0)
        
        # Total should equal password length
        self.assertEqual(lowercase_count + uppercase_count + digit_count + special_count, len(password))


if __name__ == '__main__':
    unittest.main()
