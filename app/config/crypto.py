import itsdangerous
from anyio.to_thread import run_sync
from cryptography.fernet import Fernet
from passlib.context import CryptContext

from app.config import settings

password_context = CryptContext(schemes=["pbkdf2_sha256"])


def make_password(plain_password: str) -> str:
    """Hash a plain password."""
    return password_context.hash(plain_password)


async def amake_password(plain_password: str) -> str:
    """Hash a plain password."""
    return await run_sync(make_password, plain_password)


def verify_password(hashed_password: str, plain_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return password_context.verify(plain_password, hashed_password)


async def averify_password(hashed_password: str, plain_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return await run_sync(verify_password, hashed_password, plain_password)


def get_encryption_key() -> str:
    """Get the encryption key from the settings."""
    return settings.encryption_key


def encrypt_value(data: bytes, key: str | None = None) -> bytes:
    """Encrypt a value using the encryption key.
    This function is not suitable for encrypting large amounts of data.

    It users the Fernet symmetric encryption algorithm
    which is AES128 in CBC mode with a SHA256 HMAC message authentication code.
    See https://github.com/fernet/spec/blob/master/Spec.md"""
    encryptor = Fernet(key or get_encryption_key())
    return encryptor.encrypt(data)


async def aencrypt_value(data: bytes, key: str | None = None) -> bytes:
    """Encrypt a value using the encryption key.
    This function is not suitable for encrypting large amounts of data.

    It users the Fernet symmetric encryption algorithm
    which is AES128 in CBC mode with a SHA256 HMAC message authentication code.
    See https://github.com/fernet/spec/blob/master/Spec.md"""
    return await run_sync(encrypt_value, data, key)


def decrypt_value(data: bytes, key: str | None = None, ttl: int | None = None) -> bytes:
    """Decrypt a value using the encryption key."""
    encryptor = Fernet(key or get_encryption_key())
    return encryptor.decrypt(data, ttl)


async def adecrypt_value(data: bytes, key: str | None = None, ttl: int | None = None) -> bytes:
    """Decrypt a value using the encryption key."""
    return await run_sync(decrypt_value, data, key, ttl)


def sign_value(data: bytes | str, secret_key: str | None = None) -> bytes:
    """Sign a value using the encryption key."""
    secret_key = secret_key or settings.secret_key
    signer = itsdangerous.TimestampSigner(secret_key)
    return signer.sign(data)


def get_signed_value(data: bytes | str, max_age: int | None = None, secret_key: str | None = None) -> bytes:
    """Verify a signed value using the key.
    :raises itsdangerous.BadSignature"""
    secret_key = secret_key or settings.secret_key
    signer = itsdangerous.TimestampSigner(secret_key)
    return signer.unsign(data, max_age)
