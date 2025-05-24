"""
Secure API key management module for financial data providers.

This module handles secure storage, encryption, and retrieval of API keys
for various financial data providers.
"""
import os
import json
import logging
import base64
from typing import Dict, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class ApiKeyManager:
    """Secure API key management for financial data providers."""
    
    def __init__(self, config_dir: str = None):
        """Initialize the API key manager.
        
        Args:
            config_dir: Directory to store encrypted configuration.
                        Defaults to app config directory.
        """
        self.logger = logging.getLogger(__name__)
        
        # Set configuration directory
        if config_dir is None:
            self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        else:
            self.config_dir = config_dir
            
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Path to encrypted API keys file
        self.keys_file = os.path.join(self.config_dir, 'api_keys.enc')
        
        # Path to salt file
        self.salt_file = os.path.join(self.config_dir, 'salt.bin')
        
        # Generate or load salt
        self.salt = self._get_or_create_salt()
        
        # Default encryption key (will be derived from app secret)
        self._encryption_key = None
    
    def _get_or_create_salt(self) -> bytes:
        """Get existing salt or create a new one.
        
        Returns:
            Salt bytes for key derivation.
        """
        if os.path.exists(self.salt_file):
            with open(self.salt_file, 'rb') as f:
                return f.read()
        else:
            # Generate a new salt
            salt = os.urandom(16)
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            return salt
    
    def _derive_key(self, secret: str) -> bytes:
        """Derive encryption key from secret and salt.
        
        Args:
            secret: Secret key for encryption.
            
        Returns:
            Derived encryption key.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(secret.encode()))
    
    def initialize_encryption(self, app_secret: str):
        """Initialize encryption with application secret.
        
        Args:
            app_secret: Secret key for encryption.
        """
        self._encryption_key = self._derive_key(app_secret)
        self.logger.info("Encryption initialized")
    
    def store_api_keys(self, api_keys: Dict[str, str]) -> bool:
        """Securely store API keys.
        
        Args:
            api_keys: Dictionary of API keys by provider.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self._encryption_key:
            self.logger.error("Encryption not initialized")
            return False
        
        try:
            # Create Fernet cipher
            cipher = Fernet(self._encryption_key)
            
            # Encrypt API keys
            encrypted_data = cipher.encrypt(json.dumps(api_keys).encode())
            
            # Write to file
            with open(self.keys_file, 'wb') as f:
                f.write(encrypted_data)
            
            self.logger.info("API keys stored securely")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing API keys: {str(e)}")
            return False
    
    def get_api_keys(self) -> Dict[str, str]:
        """Retrieve and decrypt API keys.
        
        Returns:
            Dictionary of API keys by provider.
        """
        if not self._encryption_key:
            self.logger.error("Encryption not initialized")
            return {}
        
        if not os.path.exists(self.keys_file):
            self.logger.warning("No API keys file found")
            return {}
        
        try:
            # Create Fernet cipher
            cipher = Fernet(self._encryption_key)
            
            # Read encrypted data
            with open(self.keys_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt data
            decrypted_data = cipher.decrypt(encrypted_data)
            
            # Parse JSON
            api_keys = json.loads(decrypted_data.decode())
            
            self.logger.info("API keys retrieved successfully")
            return api_keys
            
        except Exception as e:
            self.logger.error(f"Error retrieving API keys: {str(e)}")
            return {}
    
    def update_api_key(self, provider: str, api_key: str) -> bool:
        """Update a single API key.
        
        Args:
            provider: Provider name.
            api_key: API key value.
            
        Returns:
            True if successful, False otherwise.
        """
        # Get existing keys
        api_keys = self.get_api_keys()
        
        # Update the specified key
        api_keys[provider] = api_key
        
        # Store updated keys
        return self.store_api_keys(api_keys)
    
    def delete_api_key(self, provider: str) -> bool:
        """Delete a single API key.
        
        Args:
            provider: Provider name.
            
        Returns:
            True if successful, False otherwise.
        """
        # Get existing keys
        api_keys = self.get_api_keys()
        
        # Remove the specified key if it exists
        if provider in api_keys:
            del api_keys[provider]
            
            # Store updated keys
            return self.store_api_keys(api_keys)
        
        return True  # Key didn't exist, so technically successful
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get a single API key.
        
        Args:
            provider: Provider name.
            
        Returns:
            API key if found, None otherwise.
        """
        api_keys = self.get_api_keys()
        return api_keys.get(provider)
