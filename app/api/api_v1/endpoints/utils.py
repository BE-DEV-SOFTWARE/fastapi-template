from fastapi import APIRouter, Depends, status
from pydantic.networks import EmailStr

from app import models, schemas
from app.api import deps
from app.email_service.test import send_test_email
from app.models import Role

router = APIRouter()


@router.post(
    "/test-email/",
    status_code=status.HTTP_201_CREATED,
)
def test_email(
    email_to: EmailStr,
    _: models.User = Depends(deps.require_role(Role.ADMIN)),
) -> schemas.Msg:
    """
    Test emails.
    """
    send_test_email(email_to=email_to)
    return {"msg": "Test email sent"}
