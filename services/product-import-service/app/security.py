from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import os

PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
DEFAULT_PASSWORD_ITERATIONS = 600_000
SALT_BYTES = 16


def hash_password(password: str, *, iterations: int = DEFAULT_PASSWORD_ITERATIONS) -> str:
    if not password:
        raise ValueError("Password cannot be empty.")
    if iterations <= 0:
        raise ValueError("Password hash iterations must be positive.")

    salt = os.urandom(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{PASSWORD_HASH_ALGORITHM}${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False

    try:
        algorithm, iterations_text, salt_hex, digest_hex = password_hash.split("$", 3)
        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_hex)
        expected_digest = bytes.fromhex(digest_hex)
    except (ValueError, TypeError):
        return False

    if algorithm != PASSWORD_HASH_ALGORITHM or iterations <= 0:
        return False

    actual_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual_digest, expected_digest)


def verify_basic_auth_header(
    authorization_header: str | None,
    expected_username: str | None,
    expected_password_hash: str | None,
) -> bool:
    if not expected_username or not expected_password_hash:
        return False

    credentials = _parse_basic_auth_header(authorization_header)
    if credentials is None:
        return False

    username, password = credentials
    return hmac.compare_digest(username, expected_username) and verify_password(password, expected_password_hash)


def _parse_basic_auth_header(authorization_header: str | None) -> tuple[str, str] | None:
    if not authorization_header:
        return None

    scheme, separator, encoded_credentials = authorization_header.partition(" ")
    if not separator or scheme.lower() != "basic" or not encoded_credentials:
        return None

    try:
        decoded_credentials = base64.b64decode(encoded_credentials, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return None

    username, credential_separator, password = decoded_credentials.partition(":")
    if not credential_separator:
        return None

    return username, password
