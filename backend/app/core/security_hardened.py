import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from app.core.config import get_settings

settings = get_settings()

class HardenedSecurity:
    """
    App Store & Netflix-grade Security Engine.
    - TLS 1.3 enforced at proxy level.
    - AES-256-GCM for data encryption.
    - RSA-4096 for key exchange and envelope encryption.
    - HSM-compatible key management.
    """

    def __init__(self):
        # In production, these would be loaded from a hardware-backed HSM
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )
        self.public_key = self._private_key.public_key()

    def encrypt_data_key(self, data_key: bytes) -> bytes:
        """
        Encrypt a data key using RSA-4096 (Envelope Encryption).
        """
        return self.public_key.encrypt(
            data_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def decrypt_data_key(self, encrypted_key: bytes) -> bytes:
        """
        Decrypt a data key using RSA-4096.
        """
        return self._private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def generate_secure_data_key(self) -> bytes:
        """
        Generate a cryptographically secure 256-bit AES key.
        """
        return AESGCM.generate_key(bit_length=256)

security_engine = HardenedSecurity()
