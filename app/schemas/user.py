from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr
from pydantic.types import UUID4

from app.models.user import DEFAULT_LANGUAGE, Language, Provider, Role
from app.schemas.archivable import Archivable


# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = "user@example.com"
    first_name: Optional[str] = "John"
    last_name: Optional[str] = "Doe"
    language: Optional[Language] = DEFAULT_LANGUAGE


# Properties to receive via API on creation of an Email User
class UserCreate(UserBase):
    email: EmailStr
    sso_provider_id: Optional[str] = None
    password: Optional[str] = None
    provider: Optional[Provider] = Provider.EMAIL


# Properties to receive via API on update
class UserUpdate(UserBase):
    pass


class UserInDBBase(UserBase, Archivable):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    confirmed: Optional[bool]
    role: Role
    language: Language
    provider: Provider
    is_admin: bool
    is_moderator: bool
    is_customer: bool
    profile_picture_url: Optional[str]


# Additional properties to return via API
class User(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    full_name: Optional[str] = "John Doe"
    password_hash: str
