"""RSA-OAEP encryption service for payload-level credential encryption.

Uses pycryptodome for RSA key management and OAEP decryption (SHA-256).
Frontend clients encrypt credentials with the public key; the backend
decrypts with the private key.
"""

import base64
import json
import logging
from typing import Any, Dict

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256

from config import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """Handles RSA-OAEP decryption of encrypted payloads from frontend clients."""

    _private_key: RSA.RsaKey | None = None
    _public_key_pem: str | None = None

    @classmethod
    def _load_keys(cls) -> None:
        """Load RSA keys from configuration (PEM strings)."""
        if cls._private_key is not None:
            return

        private_pem = settings.rsa_private_key_pem
        if not private_pem:
            raise RuntimeError(
                "RSA_PRIVATE_KEY_PEM is not configured. "
                "Run 'python generate_rsa_keys.py' to generate keys."
            )

        # Handle escaped newlines from environment variables
        private_pem = private_pem.replace("\\n", "\n")

        cls._private_key = RSA.import_key(private_pem)

        public_pem = settings.rsa_public_key_pem
        if public_pem:
            cls._public_key_pem = public_pem.replace("\\n", "\n")
        else:
            # Derive public key from private key
            cls._public_key_pem = cls._private_key.publickey().export_key().decode()

        logger.info("RSA key pair loaded successfully.")

    @classmethod
    def get_public_key_pem(cls) -> str:
        """Return the RSA public key in PEM format for frontend clients."""
        cls._load_keys()
        assert cls._public_key_pem is not None
        return cls._public_key_pem

    @classmethod
    def decrypt_payload(cls, encrypted_base64: str) -> Dict[str, Any]:
        """Decrypt a base64-encoded RSA-OAEP ciphertext and parse as JSON.

        Args:
            encrypted_base64: Base64-encoded ciphertext produced by the
                frontend using the RSA public key with OAEP/SHA-256 padding.

        Returns:
            Parsed JSON dictionary from the decrypted plaintext.

        Raises:
            ValueError: If decryption fails or the payload is not valid JSON.
        """
        cls._load_keys()
        assert cls._private_key is not None

        try:
            ciphertext = base64.b64decode(encrypted_base64)
        except Exception as exc:
            raise ValueError("Invalid base64-encoded payload.") from exc

        try:
            cipher = PKCS1_OAEP.new(cls._private_key, hashAlgo=SHA256)
            plaintext = cipher.decrypt(ciphertext)
        except Exception as exc:
            raise ValueError(
                "Decryption failed. Ensure the payload was encrypted "
                "with the correct public key using RSA-OAEP/SHA-256."
            ) from exc

        try:
            return json.loads(plaintext.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("Decrypted payload is not valid JSON.") from exc

    @classmethod
    def decrypt_field(cls, encrypted_base64: str) -> str:
        """Decrypt a single base64-encoded RSA-OAEP encrypted string field.

        Args:
            encrypted_base64: Base64-encoded ciphertext of a single string
                value, encrypted with the RSA public key using OAEP/SHA-256.

        Returns:
            The decrypted plaintext string.

        Raises:
            ValueError: If decryption fails.
        """
        cls._load_keys()
        assert cls._private_key is not None

        try:
            ciphertext = base64.b64decode(encrypted_base64)
        except Exception as exc:
            raise ValueError("Invalid base64-encoded field.") from exc

        try:
            cipher = PKCS1_OAEP.new(cls._private_key, hashAlgo=SHA256)
            plaintext = cipher.decrypt(ciphertext)
        except Exception as exc:
            raise ValueError(
                "Decryption failed. Ensure the field was encrypted "
                "with the correct public key using RSA-OAEP/SHA-256."
            ) from exc

        return plaintext.decode("utf-8")
