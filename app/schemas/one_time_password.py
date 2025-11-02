from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr
from pydantic.types import UUID4


class OneTimePasswordBase(BaseModel):
    email: EmailStr
    user_id: Optional[UUID4] = None


class OneTimePasswordCreate(OneTimePasswordBase):
    pass


class OneTimePasswordUpdate(OneTimePasswordBase):
    pass


class OneTimePasswordInDBBase(OneTimePasswordBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    verification_code: str
    created_at: datetime
    expires_at: datetime


class OneTimePassword(OneTimePasswordInDBBase):
    pass
