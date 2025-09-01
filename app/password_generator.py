"""
Secure Password Generation Module

This module provides secure password generation functionality for new user accounts.
It generates cryptographically secure passwords that meet all validation requirements.
"""

import secrets
import string
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SecurePasswordGenerator:
    """Generates cryptographically secure passwords"""
    
    def __init__(self):
        # Character sets for password generation
        self.lowercase = string.ascii_lowercase
        self.uppercase = string.ascii_uppercase
        self.digits = string.digits
        self.special_chars = "!@#$%^&*(),.?\":{}|<>"
        
        # Password strength levels
        self.strength_levels = {
            'basic': {
                'length': 12,
                'min_lowercase': 2,
                'min_uppercase': 2,
                'min_digits': 2,
                'min_special': 1
            },
            'strong': {
                'length': 16,
                'min_lowercase': 3,
                'min_uppercase': 3,
                'min_digits': 3,
                'min_special': 2
            },
            'very_strong': {
                'length': 20,
                'min_lowercase': 4,
                'min_uppercase': 4,
                'min_digits': 4,
                'min_special': 3
            }
        }
    
    def generate_password(self, strength: str = 'strong', length: Optional[int] = None) -> str:
        """
        Generate a secure password with specified strength level
        
        Args:
            strength: Password strength level ('basic', 'strong', 'very_strong')
            length: Custom password length (overrides strength level length)
            
        Returns:
            Generated secure password
        """
        if strength not in self.strength_levels:
            raise ValueError(f"Invalid strength level: {strength}. Must be one of {list(self.strength_levels.keys())}")
        
        config = self.strength_levels[strength].copy()
        if length:
            config['length'] = max(length, sum([
                config['min_lowercase'],
                config['min_uppercase'], 
                config['min_digits'],
                config['min_special']
            ]))
        
        return self._generate_password_with_requirements(config)
    
    def _generate_password_with_requirements(self, config: Dict) -> str:
        """
        Generate password meeting specific character requirements
        
        Args:
            config: Dictionary with length and minimum character requirements
            
        Returns:
            Generated password
        """
        length = config['length']
        min_lowercase = config['min_lowercase']
        min_uppercase = config['min_uppercase']
        min_digits = config['min_digits']
        min_special = config['min_special']
        
        # Calculate remaining characters after minimums
        remaining_length = length - (min_lowercase + min_uppercase + min_digits + min_special)
        
        if remaining_length < 0:
            raise ValueError("Password length too short for minimum character requirements")
        
        # Start with required characters
        password_chars = []
        
        # Add minimum required characters
        password_chars.extend(secrets.choice(self.lowercase) for _ in range(min_lowercase))
        password_chars.extend(secrets.choice(self.uppercase) for _ in range(min_uppercase))
        password_chars.extend(secrets.choice(self.digits) for _ in range(min_digits))
        password_chars.extend(secrets.choice(self.special_chars) for _ in range(min_special))
        
        # Fill remaining length with random characters from all sets
        all_chars = self.lowercase + self.uppercase + self.digits + self.special_chars
        password_chars.extend(secrets.choice(all_chars) for _ in range(remaining_length))
        
        # Shuffle the password to avoid predictable patterns
        password_list = list(password_chars)
        secrets.SystemRandom().shuffle(password_list)
        
        password = ''.join(password_list)
        
        # Verify the generated password meets requirements
        if not self._verify_password_requirements(password, config):
            # If verification fails, try again (should be rare)
            logger.warning("Generated password failed verification, regenerating...")
            return self._generate_password_with_requirements(config)
        
        return password
    
    def _verify_password_requirements(self, password: str, config: Dict) -> bool:
        """
        Verify that generated password meets all requirements
        
        Args:
            password: Password to verify
            config: Requirements configuration
            
        Returns:
            True if password meets all requirements
        """
        if len(password) != config['length']:
            return False
        
        # Count character types
        lowercase_count = sum(1 for c in password if c in self.lowercase)
        uppercase_count = sum(1 for c in password if c in self.uppercase)
        digit_count = sum(1 for c in password if c in self.digits)
        special_count = sum(1 for c in password if c in self.special_chars)
        
        return (
            lowercase_count >= config['min_lowercase'] and
            uppercase_count >= config['min_uppercase'] and
            digit_count >= config['min_digits'] and
            special_count >= config['min_special']
        )
    
    def generate_memorable_password(self, word_count: int = 4, separator: str = '-') -> str:
        """
        Generate a memorable password using word-based approach
        
        Args:
            word_count: Number of words to use
            separator: Character to separate words
            
        Returns:
            Memorable password
        """
        # Common words that are easy to remember but not in common password lists
        words = [
            'apple', 'banana', 'cherry', 'dragon', 'eagle', 'forest', 'garden', 'harbor',
            'island', 'jungle', 'knight', 'lighthouse', 'mountain', 'ocean', 'penguin',
            'quasar', 'river', 'sunset', 'tiger', 'umbrella', 'volcano', 'whale', 'xylophone',
            'yellow', 'zebra', 'astronaut', 'butterfly', 'crystal', 'diamond', 'elephant',
            'firefly', 'galaxy', 'harmony', 'infinity', 'jupiter', 'kangaroo', 'lightning',
            'mermaid', 'nebula', 'octopus', 'phoenix', 'rainbow', 'sapphire', 'thunder',
            'unicorn', 'vortex', 'wonder', 'xenon', 'yellow', 'zenith'
        ]
        
        # Select random words
        selected_words = [secrets.choice(words) for _ in range(word_count)]
        
        # Add random numbers and special characters
        numbers = ''.join(secrets.choice(self.digits) for _ in range(2))
        special = secrets.choice(self.special_chars)
        
        # Combine and shuffle
        password_parts = selected_words + [numbers, special]
        secrets.SystemRandom().shuffle(password_parts)
        
        return separator.join(password_parts)
    
    def generate_pronounceable_password(self, length: int = 12) -> str:
        """
        Generate a pronounceable password using consonant-vowel patterns
        
        Args:
            length: Password length
            
        Returns:
            Pronounceable password
        """
        consonants = 'bcdfghjklmnpqrstvwxz'
        vowels = 'aeiouy'
        
        password = []
        
        for i in range(length):
            if i % 2 == 0:  # Even positions get consonants
                char = secrets.choice(consonants)
                # 20% chance to capitalize
                if secrets.randbelow(5) == 0:
                    char = char.upper()
            else:  # Odd positions get vowels
                char = secrets.choice(vowels)
            
            password.append(char)
        
        # Add some numbers and special characters
        if length >= 8:
            # Replace some characters with numbers/special chars
            num_replacements = max(1, length // 6)
            special_replacements = max(1, length // 8)
            
            for _ in range(num_replacements):
                pos = secrets.randbelow(len(password))
                password[pos] = secrets.choice(self.digits)
            
            for _ in range(special_replacements):
                pos = secrets.randbelow(len(password))
                password[pos] = secrets.choice(self.special_chars)
        
        return ''.join(password)
    
    def get_password_strength_info(self, strength: str) -> Dict:
        """
        Get information about a password strength level
        
        Args:
            strength: Password strength level
            
        Returns:
            Dictionary with strength information
        """
        if strength not in self.strength_levels:
            raise ValueError(f"Invalid strength level: {strength}")
        
        config = self.strength_levels[strength]
        
        # Calculate entropy (approximate)
        char_set_size = len(self.lowercase) + len(self.uppercase) + len(self.digits) + len(self.special_chars)
        entropy = config['length'] * (char_set_size ** 0.5)
        
        return {
            'strength': strength,
            'length': config['length'],
            'requirements': config,
            'entropy_bits': round(entropy, 1),
            'description': self._get_strength_description(strength)
        }
    
    def _get_strength_description(self, strength: str) -> str:
        """Get human-readable description of password strength"""
        descriptions = {
            'basic': 'Good for general use, meets minimum security requirements',
            'strong': 'Recommended for most accounts, high security',
            'very_strong': 'Maximum security, suitable for sensitive accounts'
        }
        return descriptions.get(strength, 'Unknown strength level')
    
    def validate_generated_password(self, password: str) -> Dict:
        """
        Validate a generated password against our requirements
        
        Args:
            password: Password to validate
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        # Check length
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        elif len(password) < 12:
            warnings.append("Consider using a longer password for better security")
        
        # Check character types
        if not any(c in self.lowercase for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c in self.uppercase for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c in self.digits for c in password):
            errors.append("Password must contain at least one number")
        
        if not any(c in self.special_chars for c in password):
            errors.append("Password must contain at least one special character")
        
        # Check for common patterns
        if password.lower() in ['password', '123456', 'qwerty']:
            errors.append("Password is too common")
        
        # Check for sequential characters
        if any(password[i] == password[i+1] == password[i+2] for i in range(len(password)-2)):
            warnings.append("Password contains repeated characters")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'length': len(password),
            'strength_score': self._calculate_strength_score(password)
        }
    
    def _calculate_strength_score(self, password: str) -> int:
        """Calculate a simple strength score (0-100)"""
        score = 0
        
        # Length contribution
        score += min(25, len(password) * 2)
        
        # Character variety contribution
        char_types = 0
        if any(c in self.lowercase for c in password):
            char_types += 1
        if any(c in self.uppercase for c in password):
            char_types += 1
        if any(c in self.digits for c in password):
            char_types += 1
        if any(c in self.special_chars for c in password):
            char_types += 1
        
        score += char_types * 15
        
        # Bonus for longer passwords
        if len(password) >= 16:
            score += 10
        elif len(password) >= 12:
            score += 5
        
        return min(100, score)


# Global instance
password_generator = SecurePasswordGenerator()
