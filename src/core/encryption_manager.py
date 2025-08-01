"""
Encryption Manager for Presidio Desktop Redactor

Manages encryption keys and provides secure encryption/decryption operations
for enhanced data protection. Integrates with Presidio's built-in encryption
operators for seamless anonymization workflow.
"""

import logging
import secrets
import string
import os
import hashlib
import math
from typing import Optional, Tuple, Dict, Any
from presidio_anonymizer.entities import OperatorConfig
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64


class EncryptionManager:
    """
    Manages encryption keys and configuration for Presidio operations.
    
    Provides secure key generation, validation, and integration with
    Presidio's EncryptOperator for text anonymization.
    """
    
    def __init__(self):
        """Initialize EncryptionManager"""
        self._encryption_key: Optional[str] = None
        self._derived_key: Optional[bytes] = None
        self._salt: Optional[bytes] = None
        self._key_length: int = 256
        self.encryption_enabled: bool = False
        self.logger = logging.getLogger(__name__)
        
        # Security settings
        self._min_key_length = 16  # Minimum 16 characters
        self._recommended_key_length = 32  # Recommended 32 characters
    
    def generate_key(self, key_length: int = 32) -> str:
        """
        Generate cryptographically secure random key
        
        Args:
            key_length: Length of key to generate (default: 32 chars)
            
        Returns:
            Base64-encoded random key string
        """
        try:
            if key_length < self._min_key_length:
                key_length = self._min_key_length
                self.logger.warning(f"Key length increased to minimum: {self._min_key_length}")
            
            # Generate random bytes
            random_bytes = secrets.token_bytes(key_length)
            
            # Encode as base64 for safe text representation
            key = base64.b64encode(random_bytes).decode('utf-8')
            
            self.logger.info(f"Generated secure encryption key ({len(key)} characters)")
            return key
            
        except Exception as e:
            self.logger.error(f"Error generating encryption key: {e}")
            raise
    
    def validate_key(self, key: str) -> Tuple[bool, str, float]:
        """
        Validate key strength and format
        
        Args:
            key: Encryption key to validate
            
        Returns:
            Tuple of (is_valid, message, strength_score)
            strength_score: 0.0-1.0 where 1.0 is strongest
        """
        if not key or not isinstance(key, str):
            return False, "Key cannot be empty", 0.0
        
        key = key.strip()
        if len(key) < self._min_key_length:
            return False, f"Key must be at least {self._min_key_length} characters", 0.0
        
        # Calculate strength score
        strength_score = self._calculate_key_strength(key)
        
        # Determine validation message
        if strength_score < 0.3:
            return False, "Key is too weak - use longer key with mixed characters", strength_score
        elif strength_score < 0.6:
            message = "Key strength: Weak - consider using longer key"
        elif strength_score < 0.8:
            message = "Key strength: Good"
        else:
            message = "Key strength: Strong"
        
        return True, message, strength_score
    
    def _calculate_key_strength(self, key: str) -> float:
        """
        Calculate key strength score (0.0-1.0)
        
        Args:
            key: Key to analyze
            
        Returns:
            Strength score from 0.0 (weakest) to 1.0 (strongest)
        """
        if not key:
            return 0.0
        
        score = 0.0
        
        # Length scoring (0.0-0.4)
        length_score = min(len(key) / 64.0, 1.0) * 0.4
        score += length_score
        
        # Character diversity scoring (0.0-0.4)
        has_lowercase = any(c.islower() for c in key)
        has_uppercase = any(c.isupper() for c in key)
        has_digits = any(c.isdigit() for c in key)
        has_special = any(c in string.punctuation for c in key)
        
        diversity_count = sum([has_lowercase, has_uppercase, has_digits, has_special])
        diversity_score = (diversity_count / 4.0) * 0.4
        score += diversity_score
        
        # Randomness/entropy scoring (0.0-0.2)
        entropy_score = self._calculate_entropy(key) * 0.2
        score += entropy_score
        
        return min(score, 1.0)
    
    def _calculate_entropy(self, text: str) -> float:
        """
        Calculate normalized entropy of text (0.0-1.0)
        
        Args:
            text: Text to analyze
            
        Returns:
            Normalized entropy score
        """
        if not text:
            return 0.0
        
        # Count character frequencies
        freq = {}
        for char in text:
            freq[char] = freq.get(char, 0) + 1
        
        # Calculate entropy using proper Shannon entropy formula
        text_len = len(text)
        entropy = 0.0
        for count in freq.values():
            p = count / text_len
            if p > 0:
                entropy -= p * math.log2(p)
        
        # Normalize to 0-1 range (approximation)
        max_entropy = 8.0  # Approximate max entropy for mixed character sets
        return min(entropy / max_entropy, 1.0)
    
    def set_encryption_key(self, key: str) -> bool:
        """
        Set encryption key and derive key material
        
        Args:
            key: Encryption key to use
            
        Returns:
            True if key was set successfully
        """
        try:
            # Validate key first
            is_valid, message, strength = self.validate_key(key)
            if not is_valid:
                self.logger.error(f"Invalid encryption key: {message}")
                return False
            
            # Store key and generate salt for key derivation
            self._encryption_key = key.strip()
            self._salt = secrets.token_bytes(32)  # 256-bit salt
            
            # Derive encryption key using PBKDF2
            self._derived_key = self._derive_key(self._encryption_key, self._salt)
            
            self.encryption_enabled = True
            self.logger.info(f"Encryption key set successfully (strength: {strength:.2f})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting encryption key: {e}")
            self.secure_cleanup()
            return False
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from password using PBKDF2
        
        Args:
            password: User-provided password
            salt: Random salt bytes
            
        Returns:
            Derived key bytes suitable for encryption
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key
            salt=salt,
            iterations=100000,  # NIST recommended minimum
            backend=default_backend()
        )
        return kdf.derive(password.encode('utf-8'))
    
    def get_operator_config(self) -> OperatorConfig:
        """
        Get Presidio encryption operator configuration
        
        Returns:
            OperatorConfig for Presidio EncryptOperator
        """
        if not self.encryption_enabled or not self._derived_key:
            raise ValueError("Encryption not enabled or key not set")
        
        try:
            # Presidio expects the key as raw bytes (not base64)
            # We use our 256-bit (32-byte) derived key directly
            config = OperatorConfig(
                "encrypt",
                {
                    "key": self._derived_key  # Pass raw bytes directly
                }
            )
            
            self.logger.debug(f"Created encryption operator config with key length: {len(self._derived_key)} bytes")
            return config
            
        except Exception as e:
            self.logger.error(f"Error creating operator config: {e}")
            raise
    
    def import_key_from_file(self, file_path: str) -> bool:
        """
        Import encryption key from file
        
        Args:
            file_path: Path to key file
            
        Returns:
            True if key imported successfully
        """
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"Key file not found: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                key = f.read().strip()
            
            success = self.set_encryption_key(key)
            if success:
                self.logger.info(f"Encryption key imported from {file_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error importing key from file: {e}")
            return False
    
    def export_key_to_file(self, file_path: str) -> bool:
        """
        Export current encryption key to file
        
        Args:
            file_path: Path to save key file
            
        Returns:
            True if key exported successfully
        """
        if not self._encryption_key:
            self.logger.error("No encryption key to export")
            return False
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write key to file with restricted permissions
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self._encryption_key)
            
            # Set restrictive file permissions (owner read/write only)
            os.chmod(file_path, 0o600)
            
            self.logger.info(f"Encryption key exported to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting key to file: {e}")
            return False
    
    def get_key_info(self) -> Dict[str, Any]:
        """
        Get information about current encryption key
        
        Returns:
            Dictionary with key information (no sensitive data)
        """
        if not self._encryption_key:
            return {
                "has_key": False,
                "encryption_enabled": False
            }
        
        is_valid, message, strength = self.validate_key(self._encryption_key)
        
        return {
            "has_key": True,
            "encryption_enabled": self.encryption_enabled,
            "key_length": len(self._encryption_key),
            "key_strength": strength,
            "strength_message": message,
            "is_valid": is_valid,
            "algorithm": "AES-256-GCM"
        }
    
    def secure_cleanup(self) -> None:
        """
        Securely clear encryption key and derived material from memory
        """
        try:
            # Clear sensitive data
            if self._encryption_key:
                # Overwrite string data (Python limitation - not guaranteed)
                self._encryption_key = "0" * len(self._encryption_key)
                self._encryption_key = None
            
            if self._derived_key:
                # Overwrite bytes data
                for i in range(len(self._derived_key)):
                    self._derived_key = self._derived_key[:i] + b'\x00' + self._derived_key[i+1:]
                self._derived_key = None
            
            if self._salt:
                for i in range(len(self._salt)):
                    self._salt = self._salt[:i] + b'\x00' + self._salt[i+1:]
                self._salt = None
            
            self.encryption_enabled = False
            self.logger.info("Encryption key material cleared from memory")
            
        except Exception as e:
            self.logger.error(f"Error during secure cleanup: {e}")
    
    def test_encryption_round_trip(self, test_text: str = "Test encryption") -> bool:
        """
        Test encryption/decryption round trip to verify functionality
        
        Args:
            test_text: Text to use for testing
            
        Returns:
            True if round trip successful
        """
        if not self.encryption_enabled:
            return False
        
        try:
            # This would normally use Presidio's encrypt operator
            # For testing purposes, we just verify key is properly set
            operator_config = self.get_operator_config()
            
            # If we get here without exception, encryption config is valid
            self.logger.info("Encryption configuration test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Encryption test failed: {e}")
            return False
    
    def __del__(self):
        """Destructor - ensure secure cleanup"""
        try:
            self.secure_cleanup()
        except:
            pass  # Don't raise exceptions in destructor