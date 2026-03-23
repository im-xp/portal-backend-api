from typing import Optional

from pydantic import BaseModel
from sqlalchemy.orm import Query, Session

from app.api.base_crud import CRUDBase
from app.api.popup_city.models import PopUpCity
from app.api.product_segments import models, schemas


class CRUDProductSegment(CRUDBase[models.ProductSegment, BaseModel, BaseModel]):
    def _apply_filters(
        self, query: Query, filters: Optional[BaseModel] = None
    ) -> Query:
        if not filters:
            return query

        if isinstance(filters, schemas.ProductSegmentFilter):
            if filters.popup_city_slug:
                query = query.join(
                    PopUpCity, PopUpCity.id == self.model.popup_city_id
                ).filter(PopUpCity.slug == filters.popup_city_slug)

        return query

    def get_by_slug_and_popup(
        self, db: Session, slug: str, popup_city_id: int
    ) -> Optional[models.ProductSegment]:
        return (
            db.query(self.model)
            .filter(
                self.model.slug == slug,
                self.model.popup_city_id == popup_city_id,
            )
            .first()
        )


product_segment = CRUDProductSegment(models.ProductSegment)
