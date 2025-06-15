from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, status
from pydantic.types import UUID4
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.api.exceptions import HTTPException, HTTPNotEnoughPermissions, HTTPUserNotFound
from app.email_service.auth import send_new_account_email
from app.models.user import Role

router = APIRouter()


@router.get("/")
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    with_archived: bool = False,
    _: models.User = Depends(deps.require_role(Role.ADMIN)),
) -> List[schemas.User]:
    """
    ADMIN: Retrieve users.
    """
    users = crud.user.get_multi(db, skip=skip, limit=limit, with_archived=with_archived)
    return users


@router.post("/")
async def create_user(
    *,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    role: Role = Role.CUSTOMER,
    current_user: models.User = Depends(deps.require_role(Role.ADMIN)),
) -> schemas.User:
    """
    ADMIN: Create new user.
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user with this username already exists in the system.",
            locale=current_user.language,
        )
    user = crud.user.create(db, obj_in=user_in, role=role)
    background_tasks.add_task(send_new_account_email, email=user_in.email)
    return user


@router.put("/me")
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_user),
) -> schemas.User:
    """
    Update current user.
    """
    user = crud.user.update(db, db_obj=current_user, obj_in=user_in)
    return user


@router.get("/me")
def read_user_me(
    current_user: models.User = Depends(deps.get_current_user),
) -> schemas.User:
    """
    Read current user.
    """
    return current_user


@router.delete("/me/archive")
def archive_user_me(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> schemas.User:
    """
    Archive the current user. Only admin users can unarchive users.
    """
    user = crud.user.archive(db, obj=current_user)
    return user


@router.get("/{user_id}")
def read_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: UUID4,
    current_user: models.User = Depends(deps.require_role(Role.ADMIN)),
    ) -> schemas.User:
    """
    ADMIN: Read a specific user by id.
    """
    user = crud.user.get(db, id=user_id, with_archived=True)
    if user is None:
        raise
    if user == current_user:
        return user
    if not current_user.is_admin:
        raise HTTPNotEnoughPermissions(current_user.language)
    return user


@router.put("/{user_id}")
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: UUID4,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.require_role(Role.ADMIN)),
) -> schemas.User:
    """
    ADMIN: Update a user.
    """
    user = crud.user.get(db, id=user_id, with_archived=True)
    if user is None:
        raise HTTPUserNotFound(current_user.language)
    user = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user


@router.delete("/{user_id}/archive")
def archive_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: UUID4,
    current_user: models.User = Depends(deps.require_role(Role.ADMIN)),
) -> schemas.User:
    """
    ADMIN: Archive a user.
    """
    user = crud.user.get(db, id=user_id)
    if user is None:
        raise HTTPUserNotFound(current_user.language)
    user = crud.user.archive(db, user)
    return user


@router.put("/{user_id}/unarchive")
def unarchive_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: UUID4,
    current_user: models.User = Depends(deps.require_role(Role.ADMIN)),
) -> schemas.User:
    """
    ADMIN: Unarchive a user.
    """
    user = crud.user.get(db, id=user_id, with_archived=True)
    if user is None:
        raise HTTPUserNotFound(current_user.language)
    user = crud.user.unarchive(db, user)
    return user


@router.delete("/{user_id}")
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: UUID4,
    current_user: models.User = Depends(deps.require_role(Role.ADMIN)),
) -> schemas.User:
    """
    ADMIN: Permanently delete a user.
    """
    user = crud.user.get(db, id=user_id)
    if user is None:
        raise HTTPUserNotFound(current_user.language)
    user = crud.user.remove(db, id=user_id)
    return user
