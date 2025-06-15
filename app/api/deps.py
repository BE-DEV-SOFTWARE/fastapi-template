from typing import Callable, Generator

import jwt
from fastapi import Body, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi_sso.sso.base import SSOBase
from fastapi_sso.sso.facebook import FacebookSSO
from fastapi_sso.sso.github import GithubSSO
from fastapi_sso.sso.google import GoogleSSO
from jwt import ExpiredSignatureError, PyJWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.exceptions import HTTPException, HTTPNotEnoughPermissions
from app.core import security
from app.core.config import settings
from app.db.session import SessionLocal

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def get_generic_sso(provider: models.SSOProvider) -> SSOBase:
    if provider == models.Provider.GOOGLE and settings.GOOGLE_SSO_ENABLED:
        return get_google_sso()
    elif provider == models.Provider.FACEBOOK and settings.FACEBOOK_SSO_ENABLED:
        return get_facebook_sso()
    elif provider == models.Provider.GITHUB and settings.GITHUB_SSO_ENABLED:
        return get_github_sso()
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"SSO provider '{provider}' is not enabled or not available for this application",
        )


def get_google_sso() -> GoogleSSO:
    return GoogleSSO(
        settings.GOOGLE_CLIENT_ID,
        settings.GOOGLE_CLIENT_SECRET,
        f"{settings.SERVER_HOST}api/v1/auth/google/callback",
    )


def get_github_sso() -> GithubSSO:
    return GithubSSO(
        settings.GITHUB_CLIENT_ID,
        settings.GITHUB_CLIENT_SECRET,
        f"{settings.SERVER_HOST}api/v1/auth/github/callback",
    )


def get_facebook_sso() -> FacebookSSO:
    return FacebookSSO(
        settings.FACEBOOK_CLIENT_ID,
        settings.FACEBOOK_CLIENT_SECRET,
        f"{settings.SERVER_HOST}api/v1/auth/facebook/callback",
    )


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def verify_token(
    token: str, token_context: schemas.TokenContext
) -> schemas.TokenPayload:
    try:
        token_data = security.verify_token(token, token_context)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token expired",
        )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token, error while decoding token",
        )
    except ValidationError as validation_error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(validation_error),
        )
    except security.TokenContextError as token_context:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(token_context),
        )
    return token_data


def get_user_after_sso_confirmation(
    db: Session = Depends(get_db), sso_confirmation_token: str = Body(...)
) -> models.User:
    token_data = verify_token(
        sso_confirmation_token, schemas.TokenContext.SSO_CONFIRMATION_TOKEN
    )
    user = crud.user.get_by_sso_confirmation_code(
        db, token_data.user_id, token_data.sso_confirmation_code
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


def get_user_from_refresh_token(
    db: Session = Depends(get_db), refresh_token: str = Body(...)
) -> models.User:
    token_data = verify_token(refresh_token, schemas.TokenContext.REFRESH_TOKEN)
    user = crud.user.get(db, id=token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> models.User:
    try:
        token_data = verify_token(token, schemas.TokenContext.ACCESS_TOKEN)
    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token, could not validate credentials",
        )
    user = crud.user.get(db, id=token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


def require_role(*roles: models.Role) -> Callable:
    def check_role(
        current_user: models.User = Depends(get_current_user),
    ) -> models.User:
        if not current_user.role in roles:
            raise HTTPNotEnoughPermissions(current_user.language)
        return current_user

    return check_role
