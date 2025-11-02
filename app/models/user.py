from enum import Enum
from typing import TYPE_CHECKING, List, Literal, Optional

from sqlalchemy import Boolean, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

from .archivable import Archivable

if TYPE_CHECKING:
    from .file import File  # noqa: F401
    from .item import Item  # noqa: F401


class Language(str, Enum):
    EN = "en"
    FR = "fr"


DEFAULT_LANGUAGE = Language.EN


class Role(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    CUSTOMER = "customer"


class Provider(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"
    FACEBOOK = "facebook"
    GITHUB = "github"


# Modify this to match the SSO providers you are using in your project
SSOProvider = Literal[Provider.GOOGLE, Provider.FACEBOOK, Provider.GITHUB]


class User(Base, Archivable):
    # Override the table name to avoid any confusion with SQL reserved word "user" during generated migration scripts
    __tablename__ = "person"
    # Authentication
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[Optional[str]]
    role: Mapped[Role] = mapped_column(String, default=Role.CUSTOMER)
    language: Mapped[Language] = mapped_column(String, default=DEFAULT_LANGUAGE)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    sso_confirmation_code: Mapped[Optional[str]]
    # Personal information
    first_name: Mapped[str] = mapped_column(String, default="")
    last_name: Mapped[str] = mapped_column(String, default="")
    phone: Mapped[Optional[str]]
    address: Mapped[Optional[str]]
    city: Mapped[Optional[str]]
    postcode: Mapped[Optional[str]]
    state: Mapped[Optional[str]]
    provider: Mapped[Provider] = mapped_column(String, default=Provider.EMAIL)
    sso_provider_id: Mapped[Optional[str]] = mapped_column(String, index=True)
    profile_pic: Mapped[Optional["File"]] = relationship(
        "File", backref="user", uselist=False, cascade="all, delete"
    )
    items: Mapped[List["Item"]] = relationship(
        "Item", backref="user", lazy="dynamic", cascade="all, delete"
    )

    @hybrid_property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

    @is_admin.expression
    def is_admin(cls):
        return cls.role == Role.ADMIN

    @hybrid_property
    def is_moderator(self) -> bool:
        return self.role == Role.MODERATOR

    @is_moderator.expression
    def is_moderator(cls):
        return cls.role == Role.MODERATOR

    @hybrid_property
    def is_customer(self) -> bool:
        return self.role == Role.CUSTOMER

    @is_customer.expression
    def is_customer(cls):
        return cls.role == Role.CUSTOMER

    @hybrid_property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @full_name.expression
    def full_name(cls):
        return cls.first_name + " " + cls.last_name

    @property
    def profile_picture_url(self) -> Optional[str]:
        return (
            self.profile_pic.user_profile_pic_url
            if self.profile_pic is not None
            else None
        )
