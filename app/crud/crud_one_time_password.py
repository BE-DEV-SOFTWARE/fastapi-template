import random
from datetime import datetime, timezone, timedelta, UTC
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic.types import UUID4
from app.crud.base import CRUDBase, apply_changes
from app.models.one_time_password import OneTimePassword
from app.schemas.one_time_password import OneTimePasswordCreate, OneTimePasswordUpdate
from app.core.config import settings


class CRUDOneTimePassword(CRUDBase[OneTimePassword, OneTimePasswordCreate, OneTimePasswordUpdate]):
    def generate_code(self) -> str:
        while True:
            code = "".join(random.choices("123456789", k=6))
            if code != "123456":
                return code

    def get_by_verification_code(self, db: Session, *, verification_code: str) -> Optional[OneTimePassword]:
        return (
            db.query(OneTimePassword)
            .filter(OneTimePassword.verification_code == verification_code)
            .first()
        )
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[OneTimePassword]:
        return db.query(OneTimePassword).filter(OneTimePassword.email == email).first()
    
    def get_all_by_user_id(self, db: Session, *, user_id: UUID4) -> List[OneTimePassword]:
        return db.query(OneTimePassword).filter(OneTimePassword.user_id == user_id).all()

    def create_for_email(
        self, db: Session, *, email: str, user_id: Optional[UUID4]
    ) -> OneTimePassword:
        db.query(OneTimePassword).filter(OneTimePassword.email == email).delete()
        db.commit()
        
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRATION_MINUTES)
        
        otp_in = OneTimePasswordCreate(email=email, user_id=user_id)
        db_obj = OneTimePassword(
            **otp_in.model_dump(),
            code=self.generate_code(),
            expires_at=expires_at,
        )
        apply_changes(db, db_obj)
        return db_obj

    def get_valid_otp(self, db: Session, *, verification_code: str) -> Optional[OneTimePassword]:
        otp = self.get_by_verification_code(db, verification_code=verification_code)
        return (
            otp
            if otp and otp.expires_at > datetime.now(timezone.utc)
            else None
        )

    def create_apple_review_team_otp(self, db: Session, user) -> OneTimePassword:
        assert user.email == settings.APPLE_REVIEW_TEAM_EMAIL, "User is not the Apple review team user"
        self.delete_apple_review_team_otp(db)
        now = datetime.now(timezone.utc)
        delta = timedelta(days=settings.APPLE_REVIEW_TEAM_OTP_EXPIRATION_DAYS)
        expires_at = now + delta
        db_obj = OneTimePassword(
            code=self.generate_code(),
            user_id=user.id,
            email=user.email,
            expires_at=expires_at,
        )
        apply_changes(db, db_obj)
        return db_obj

    def get_apple_review_team_otp(self, db: Session) -> Optional[OneTimePassword]:
        return self.get_by_email(db, email=settings.APPLE_REVIEW_TEAM_EMAIL)
    
    def delete_apple_review_team_otp(self, db: Session) -> Optional[OneTimePassword]:
        otp = self.get_apple_review_team_otp(db)
        if otp is not None:
            return self.remove(db, otp)
        return None

    def update(
        self, db: Session, *, db_obj: OneTimePassword, obj_in: OneTimePasswordUpdate
    ) -> OneTimePassword:
        raise NotImplementedError("One-time passwords are not updatable")
    
    def get_expired_otps(self, db: Session) -> List[OneTimePassword]:
        return db.query(OneTimePassword).filter(OneTimePassword.expires_at < datetime.now(UTC)).all()


one_time_password = CRUDOneTimePassword(OneTimePassword)

