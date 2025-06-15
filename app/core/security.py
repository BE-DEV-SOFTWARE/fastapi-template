import hashlib
import random
import string
from datetime import UTC, datetime, timedelta
from os import urandom
from typing import Optional

import jwt
from pydantic import UUID4

from app.core.config import settings
from app.schemas.auth import TokenContext, TokenPayload

# Parameters for scrypt function
# Those parameters can be adjusted based on target system's capabilities
N = 16_384  # CPU/Memory cost factor
R = 8  # Block size
P = 4  # Parallelization factor
MAXMEM = 0  # 0 indicates to use the default value (32 MiB in OpenSSL 1.1.0)
DKLEN = 64  # Length of the derived key (common choice for security)


class TokenContextError(Exception):
    def __init__(self, context: TokenContext, expected_context: TokenContext):
        super().__init__(
            f"Unexpected token context. Expected: {expected_context}, got {context}"
        )


def scrypt(password: str, salt: bytes) -> None:
    return hashlib.scrypt(
        str(password).encode(), salt=salt, n=N, r=R, p=P, maxmem=MAXMEM, dklen=DKLEN
    )


def create_token(
    user_id: UUID4,
    context: TokenContext,
    *,
    sso_confirmation_code: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = None
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    token_payload = TokenPayload(
        user_id=str(user_id),
        sso_confirmation_code=sso_confirmation_code,
        exp=expire,
        context=context,
        iat=datetime.now(UTC),
        random_value="".join(
            random.choices(string.ascii_uppercase + string.digits, k=16)
        ),
    )
    to_encode = token_payload.model_dump()
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY)
    return encoded_jwt


def create_access_token(user_id: UUID4) -> str:
    expires_delta = timedelta(seconds=settings.ACCESS_TOKEN_EXPIRES_SECONDS)
    return create_token(user_id, TokenContext.ACCESS_TOKEN, expires_delta=expires_delta)


def create_refresh_token(user_id: UUID4) -> str:
    expires_delta = timedelta(seconds=settings.REFRESH_TOKEN_EXPIRES_SECONDS)
    return create_token(
        user_id, TokenContext.REFRESH_TOKEN, expires_delta=expires_delta
    )


def create_sso_confirmation_token(user_id: UUID4, sso_confirmation_code: str) -> str:
    expires_delta = timedelta(seconds=settings.SSO_CONFIRMATION_TOKEN_EXPIRES_SECONDS)
    return create_token(
        user_id,
        TokenContext.ACCESS_TOKEN,
        sso_confirmation_code=sso_confirmation_code,
        expires_delta=expires_delta,
    )


def verify_token(token: str, context: TokenContext) -> TokenPayload:
    decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    token_data = TokenPayload(**decoded_token)
    if token_data.context != context:
        raise TokenContextError(token_data.context, context)
    return token_data


def verify_password(plain_password: str, password_hash: str) -> bool:
    # Split the password_hash to extract the salt
    salted_password_hash = bytes.fromhex(password_hash)
    stored_salt = salted_password_hash[:16]
    stored_key = salted_password_hash[16:]

    # Derive the key from the provided plain_password and salt
    derived_key = scrypt(plain_password.encode(), salt=stored_salt)

    # Compare the derived key with the stored key
    return derived_key == stored_key


def get_password_hash(password: str) -> str:
    # Generate a random salt
    salt = urandom(16)

    # Derive the key from the password and salt
    derived_key = scrypt(str(password).encode(), salt=salt)

    # Concatenate the salt and derived key for storage
    salted_password_hash = salt + derived_key

    # Convert the salted password hash to hexadecimal format for storage
    return salted_password_hash.hex()


def generate_sso_confirmation_code() -> str:
    # Generate a 8 characters random code to be used as SSO confirmation code
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(UTC)
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email}, settings.SECRET_KEY
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return decoded_token["email"]
    except jwt.PyJWTError:
        return None
