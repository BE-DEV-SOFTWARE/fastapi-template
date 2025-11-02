from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic.types import UUID4
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .user import User


class OneTimePassword(Base):
    verification_code: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    user_id: Mapped[Optional[UUID4]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id")
    )
    email: Mapped[str] = mapped_column(String, unique=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
