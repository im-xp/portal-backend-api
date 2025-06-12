from typing import Optional

from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.api.world_builders import models, schemas
from app.core.security import TokenData


class CRUDWorldBuilder(
    CRUDBase[
        models.WorldBuilder, schemas.WorldBuilderCreate, schemas.WorldBuilderUpdate
    ]
):
    def create(
        self,
        db: Session,
        obj: schemas.WorldBuilderCreate,
        user: Optional[TokenData] = None,
    ) -> models.WorldBuilder:
        return super().create(db, obj, user)


world_builder = CRUDWorldBuilder(models.WorldBuilder)
