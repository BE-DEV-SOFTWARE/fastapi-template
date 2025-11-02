from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from .user import User


class TokenContext(str, Enum):
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    SSO_CONFIRMATION_TOKEN = "sso_confirmation_token"


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    access_token_expiration_date: datetime = Field(
        description="The date and time when the access token expires in UTC"
    )
    refresh_token_expiration_date: datetime = Field(
        description="The date and time when the refresh token expires in UTC"
    )
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


class OTPRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    code: str = Field(..., pattern=r"^\d{6}$")
    email: EmailStr
