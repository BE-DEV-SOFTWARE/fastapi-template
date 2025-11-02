from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.schemas import UserCreate


def test_request_and_verify_otp(client: TestClient, db: Session) -> None:
    email = "test_otp@example.com"

    r = client.post(
        f"{settings.API_V1_STR}/auth/otp/request",
        json={"email": email},
    )
    assert r.status_code == status.HTTP_200_OK

    response_msg = r.json()["msg"]
    assert "Development mode" in response_msg

    otp_code = response_msg.split()[-1]
    assert len(otp_code) == 6
    assert otp_code.isdigit()

    r = client.post(
        f"{settings.API_V1_STR}/auth/otp/verify",
        json={"email": email, "code": otp_code},
    )
    assert r.status_code == status.HTTP_200_OK
    assert "access_token" in r.json()
    assert "user" in r.json()


def test_otp_login_existing_user(client: TestClient, db: Session) -> None:
    email = "existing_user@example.com"
    password = "testpassword123"

    user = crud.user.get_by_email(db, email=email)
    if user is None:
        user_in = UserCreate(email=email, password=password)
        user = crud.user.create(db=db, obj_in=user_in)
    assert user is not None

    r = client.post(
        f"{settings.API_V1_STR}/auth/otp/request",
        json={"email": email},
    )
    assert r.status_code == status.HTTP_200_OK

    response_msg = r.json()["msg"]
    otp_code = response_msg.split()[-1]

    r = client.post(
        f"{settings.API_V1_STR}/auth/otp/verify",
        json={"email": email, "code": otp_code},
    )
    assert r.status_code == status.HTTP_200_OK
    tokens = r.json()
    assert tokens["user"]["email"] == email


def test_persistent_otp_login(client: TestClient, db: Session) -> None:
    email = "persistent_otp_user@example.com"

    user = crud.user.get_by_email(db, email=email)
    if user is None:
        user_in = UserCreate(email=email, password="somepassword")
        user = crud.user.create(db=db, obj_in=user_in)
    assert user is not None

    r = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": email, "password": settings.PERSISTENT_OTP},
    )
    assert r.status_code == status.HTTP_200_OK
    assert "access_token" in r.json()
    assert r.json()["user"]["email"] == email


def test_apple_review_team_otp(
    client: TestClient, db: Session, superuser_token_headers: dict
) -> None:
    apple_email = settings.APPLE_REVIEW_TEAM_EMAIL

    r = client.post(
        f"{settings.API_V1_STR}/auth/generate-apple-review-team-otp",
        headers=superuser_token_headers,
    )
    assert r.status_code == status.HTTP_200_OK
    otp_response = r.json()
    assert "verification_code" in otp_response
    apple_otp_code = otp_response["verification_code"]

    r = client.post(
        f"{settings.API_V1_STR}/auth/otp/verify",
        json={"email": apple_email, "code": apple_otp_code},
    )
    assert r.status_code == status.HTTP_200_OK
    assert "access_token" in r.json()
    assert r.json()["user"]["email"] == apple_email
