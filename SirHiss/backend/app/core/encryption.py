"""
Encryption utilities for sensitive data like API credentials
"""

import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.config import settings


class CredentialEncryption:
    """Handles encryption/decryption of API credentials"""
    
    def __init__(self):
        self._fernet = None
    
    @property
    def fernet(self):
        if self._fernet is None:
            # Derive key from settings
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=settings.ENCRYPTION_SALT.encode(),
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt_credentials(self, credentials: dict) -> str:
        """Encrypt a dictionary of credentials"""
        json_string = json.dumps(credentials)
        encrypted_bytes = self.fernet.encrypt(json_string.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()
    
    def decrypt_credentials(self, encrypted_string: str) -> dict:
        """Decrypt credentials back to dictionary"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_string.encode())
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            json_string = decrypted_bytes.decode()
            return json.loads(json_string)
        except Exception as e:
            raise ValueError(f"Failed to decrypt credentials: {str(e)}")


# Global instance
credential_encryption = CredentialEncryption()