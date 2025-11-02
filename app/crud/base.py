from datetime import UTC, datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from pydantic.types import UUID4
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql.expression import false

from app.db.base_class import Base
from app.models.archivable import Archivable

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


def apply_changes(db: Session, db_item: ModelType) -> None:
    db.add(db_item)
    db.commit()
    db.refresh(db_item)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def filter_archivable(self, query: Query, with_archived: bool = False):
        if issubclass(self.model, Archivable) and not with_archived:
            query = query.filter(self.model.archived == false())
        return query

    def get(
        self, db: Session, id: UUID4, with_archived: bool = False
    ) -> Optional[ModelType]:
        query: Query = db.query(self.model).filter(self.model.id == id)
        query = self.filter_archivable(query, with_archived)
        return query.first()

    def get_all(self, db: Session, with_archived: bool = False) -> List[ModelType]:
        query = db.query(self.model)
        query = self.filter_archivable(query, with_archived)
        return query.all()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        with_archived: bool = False,
    ) -> List[ModelType]:
        query = db.query(self.model)
        query = self.filter_archivable(query, with_archived)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        apply_changes(db, db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        apply_changes(db, db_obj)
        return db_obj

    def remove(self, db: Session, obj: ModelType) -> ModelType:
        db.delete(obj)
        db.commit()
        return obj

    def archive(self, db: Session, obj: ModelType) -> ModelType:
        if issubclass(self.model, Archivable):
            obj.archived_at = datetime.now(UTC)
            apply_changes(db, obj)
        return obj

    def unarchive(self, db: Session, obj: ModelType) -> ModelType:
        if issubclass(self.model, Archivable):
            obj.archived_at = None
            apply_changes(db, obj)
        return obj
