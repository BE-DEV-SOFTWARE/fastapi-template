from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_sso.sso.base import SSOBase
from fastapi_sso.sso.google import OpenID
from pydantic import EmailStr
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, UTC

from app import crud, models, schemas
from app.api import deps
from app.api.exceptions import HTTPException
from app.core import security
from app.core.security import get_password_hash
from app.email_service.auth import send_reset_password_email, send_verification_code_email, send_new_account_email
from app.core.config import settings
from app.exceptions.auth import InvalidTokenException

router = APIRouter()


@router.post("/register")
def register_email_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
) -> schemas.AuthResponse:
    """
    Register as new user to the application.
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user with this username already exists in the system.",
        )
    user = crud.user.create(db, obj_in=user_in)
    send_new_account_email(user.email)

    return create_login_response(user)


@router.get("/{provider}/login")
async def sso_login(
    *, sso: SSOBase = Depends(deps.get_generic_sso), return_url: str
) -> Any:
    """
    Endpoint to use to login using an SSO provider. Call this endpoint to get the redirection link of the requested provider where all the authentication process between the user of the app and the provider will happen.
    """
    return await sso.get_login_redirect(state=return_url)


@router.get("/{provider}/callback")
async def sso_callback(
    *,
    db: Session = Depends(deps.get_db),
    sso: SSOBase = Depends(deps.get_generic_sso),
    request: Request,
    provider: models.SSOProvider,
) -> Any:
    """
    Callback url automatically called by the provider at the end of the authentication process. This endpoint is not meant to be called by the client directly
    """
    sso_user: OpenID = await sso.verify_and_process(request)
    token = create_sso_user(db, provider, sso_user)
    return RedirectResponse(f"{sso.state}?token={token}")


@router.post("/sso/confirm")
def get_sso_access_token(
    user: models.User = Depends(deps.get_user_after_sso_confirmation),
) -> schemas.AuthResponse:
    """
    The SSO authentication flow generate a token returned as a query parameters of the deep link redirection response of the callback endpoint. The auth/sso/confirm endpoint allows your client (mobile app, website, etc...) to get the authentication information of the user by trading the issued token for the actual authentication information of the user.
    """
    return create_login_response(user)


@router.post("/login")
def login(
    db: Session = Depends(deps.get_db), 
    form_data: OAuth2PasswordRequestForm = Depends(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> schemas.AuthResponse:
    """
    OAuth2 compatible token login, get an access token for future requests.
    Supports both password and OTP authentication (use email as username and OTP as password).
    """
    email = form_data.username
    password_or_otp = form_data.password
    
    user = crud.user.authenticate(db, email=email, password=password_or_otp)
    if user:
        return create_login_response(user)
    
    try:
        return authenticate_or_register_with_otp(
            db=db, 
            email=email, 
            verification_code=password_or_otp,
        )
    except InvalidTokenException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email, password, or OTP",
        )


@router.post("/refresh")
def refresh_token(user: models.User = Depends(deps.get_user_from_refresh_token)) -> schemas.AuthResponse:
    """
    Refresh authentication information using a refresh token
    """
    return create_login_response(user)


@router.post("/login/test-token", include_in_schema=(not settings.IS_PRODUCTION))
def test_token(current_user: models.User = Depends(deps.get_current_user)) -> schemas.User:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}")
def recover_password(
    background_tasks: BackgroundTasks, email: str, db: Session = Depends(deps.get_db)
) -> schemas.Msg:
    """
    Password Recovery
    """
    user = crud.user.get_by_email(db, email=email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = security.generate_password_reset_token(email=email)
    background_tasks.add_task(
        send_reset_password_email,
        email_to=user.email,
        email=email,
        token=password_reset_token,
    )
    return {"msg": "Password recovery email sent"}


@router.post("/reset-password/")
def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(deps.get_db),
) -> schemas.Msg:
    """
    Reset password
    """
    email = security.verify_password_reset_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    user = crud.user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this username does not exist in the system.",
        )
    password_hash = get_password_hash(new_password)
    user.password_hash = password_hash
    db.add(user)
    db.commit()
    return {"msg": "Password updated successfully"}


@router.post("/otp/request")
def request_otp(
    otp_request: schemas.OTPRequest,
    db: Session = Depends(deps.get_db),
) -> schemas.Msg:
    """
    Request a verification code to login.
    """
    email = otp_request.email.lower()
    if email == settings.APPLE_REVIEW_TEAM_EMAIL:
        return {"msg": "Gracefully handled: Apple review team cannot request a verification code"}
    
    user = crud.user.get_by_email(db, email=email)
    
    otp = crud.one_time_password.create_for_email(
        db=db, email=email, user_id=user.id if user else None
    )
    
    if settings.EMAILS_ENABLED:
        send_verification_code_email(
            email=email,
            verification_code=otp.verification_code
        )
        return {
            "msg": "If an account exists, a verification code has been sent"
        }
    else:
        return {
            "msg": f"Development mode: Your verification code is {otp.verification_code}"
        }


def authenticate_or_register_with_otp(
    *,
    db: Session,
    email: EmailStr,
    verification_code: str,
    background_tasks: Optional[BackgroundTasks] = None,
) -> schemas.AuthResponse:
    try:
        user = crud.user.authenticate_with_otp(
            db, 
            email=email, 
            verification_code=verification_code,
        )
        return create_login_response(user)
    except InvalidTokenException:
        user = crud.user.get_by_email(db, email=email)
        if user is None:
            new_user = schemas.UserCreate(email=email)
            user = crud.user.create(db, obj_in=new_user)
            if background_tasks is not None:
                background_tasks.add_task(send_new_account_email, email=email)
            return create_login_response(user)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication code",
            )


@router.post("/otp/verify")
def verify_otp(
    verify_otp_request: schemas.VerifyOTPRequest,
    db: Session = Depends(deps.get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> schemas.AuthResponse:
    """
    Authenticate user with OTP code. If the user doesn't exist, they will be automatically registered.
    This endpoint handles both login and registration seamlessly - if a user provides a valid OTP code
    but doesn't have an account, a new account will be created automatically.
    """
    email = verify_otp_request.email.lower()
    code = verify_otp_request.code
    
    return authenticate_or_register_with_otp(
        db=db,
        email=email,
        verification_code=code,
        background_tasks=background_tasks,
    )


def create_login_response(user: models.User) -> schemas.AuthResponse:
    access_token_expiration_date = datetime.now(UTC) + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRES_SECONDS)
    refresh_token_expiration_date = datetime.now(UTC) + timedelta(seconds=settings.REFRESH_TOKEN_EXPIRES_SECONDS)
    return schemas.AuthResponse(
        access_token=security.create_access_token(user.id),
        refresh_token=security.create_refresh_token(user.id),
        access_token_expiration_date=access_token_expiration_date,
        refresh_token_expiration_date=refresh_token_expiration_date,
        token_type="bearer",
        user=user,
    )


@router.post("/generate-apple-review-team-otp")
def generate_apple_review_team_otp(
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.require_role(models.Role.ADMIN)),
) -> schemas.OneTimePassword:
    """
    Generate a persistent OTP for Apple review team.
    This endpoint is only available to admins.
    The OTP will be valid for the Apple review team user and persist until explicitly deactivated.
    """
    apple_review_team_user = crud.user.get_by_email(
        db, email=settings.APPLE_REVIEW_TEAM_EMAIL)
    if apple_review_team_user is None:
        user_in = schemas.UserCreate(
            email=settings.APPLE_REVIEW_TEAM_EMAIL,
        )
        apple_review_team_user = crud.user.create(
            db=db,
            obj_in=user_in,
            role=models.Role.CUSTOMER,
        )
    otp = crud.one_time_password.create_apple_review_team_otp(
        db, apple_review_team_user)
    return otp


@router.delete("/delete-apple-review-team-otp")
def delete_apple_review_team_otp(
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.require_role(models.Role.ADMIN)),
) -> schemas.OneTimePassword:
    """
    Delete the current Apple review team OTP if any.
    This endpoint is only available to admins. It is to be used when the Apple review team is done with their testing and we don't need the OTP anymore.
    """
    otp = crud.one_time_password.delete_apple_review_team_otp(db)
    if otp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Apple review team OTP found"
        )
    return otp


def create_sso_user(db: Session, provider: models.Provider, openid_user: OpenID) -> str:
    user = crud.user.get_by_sso_provider_id(
        db, sso_provider_id=openid_user.id, provider=provider
    )

    if user is None:
        # Verify if user exists with email
        # This can happen when the user has already registered with email or facebook and now wants to login with Google
        user = crud.user.get_by_email(db, email=openid_user.email)
        if user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'The user with email "{openid_user.email}" already exists in the system.',
            )
        # Create user
        user_in = schemas.UserCreate(
            email=openid_user.email,
            sso_provider_id=openid_user.id,
            provider=provider,
            first_name=openid_user.first_name,
            last_name=openid_user.last_name,
        )
        user = crud.user.create(db, obj_in=user_in)
        send_new_account_email(user.email)
    user = crud.user.update_sso_confirmation_code(db, user)
    token = security.create_sso_confirmation_token(user.sso_confirmation_code)
    return token
