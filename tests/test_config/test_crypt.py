import base64
import secrets

from passlib.context import CryptContext

from app.config.crypto import (
    adecrypt_value,
    aencrypt_value,
    amake_password,
    averify_password,
    decrypt_value,
    encrypt_value,
    hash_value,
    make_password,
    verify_hashed_value,
    verify_password,
)


def test_password_verification() -> None:
    plain_password = "password"
    hashed_password = make_password(plain_password)
    assert verify_password(hashed_password, plain_password)


async def test_password_async_verification() -> None:
    plain_password = "password"
    hashed_password = await amake_password(plain_password)
    assert await averify_password(hashed_password, plain_password)


def test_password_migration() -> None:
    plain_password = "password"

    password_context = CryptContext(schemes=["pbkdf2_sha512"])
    hashed_password_sha512 = password_context.hash(plain_password)

    password_context = CryptContext(schemes=["pbkdf2_sha256"])
    hashed_password_sha256 = password_context.hash(plain_password)

    password_context = CryptContext(schemes=["pbkdf2_sha256", "pbkdf2_sha512"])
    assert password_context.verify(plain_password, hashed_password_sha512)
    assert password_context.verify(plain_password, hashed_password_sha256)


def test_encryption() -> None:
    key = base64.encodebytes(secrets.token_bytes(32)).decode()
    data = b"hello, world!"
    assert decrypt_value(encrypt_value(data, key=key), key=key) == data


async def test_encryption_async() -> None:
    key = base64.encodebytes(secrets.token_bytes(32)).decode()
    data = b"hello, world!"
    assert await adecrypt_value(await aencrypt_value(data, key=key), key=key) == data


def test_encryption_with_key_from_settings() -> None:
    data = b"hello, world!"
    assert decrypt_value(encrypt_value(data)) == data


def test_hash_value() -> None:
    hashed = hash_value(b"hello, world!")
    assert verify_hashed_value(hashed, b"hello, world!")

    hashed = hash_value("hello, world!")
    assert verify_hashed_value(hashed, "hello, world!")
