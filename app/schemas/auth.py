from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from .user import User


class TokenContext(str, Enum):
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    SSO_CONFIRMATION_TOKEN = "sso_confirmation_token"


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: User


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    exp: Optional[datetime]
    iat: datetime
    context: TokenContext
    user_id: str
    sso_confirmation_code: Optional[str]
    random_value: str
