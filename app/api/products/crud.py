from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.base_crud import CRUDBase
from app.api.product_segments.models import ProductSegmentProduct
from app.api.products import models, schemas
from app.core.security import TokenData


class CRUDProduct(
    CRUDBase[models.Product, schemas.ProductCreate, schemas.ProductUpdate]
):
    def find(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[BaseModel] = None,
        user: Optional[TokenData] = None,
        sort_by: str = 'created_at',
        sort_order: str = 'desc',
        product_segment_id: Optional[int] = None,
    ) -> List[models.Product]:
        query = db.query(self.model)
        query = self._apply_filters(query, filters)

        if product_segment_id is not None:
            query = query.join(
                ProductSegmentProduct,
                ProductSegmentProduct.product_id == self.model.id,
            ).filter(ProductSegmentProduct.product_segment_id == product_segment_id)

        if not hasattr(self.model, sort_by):
            from fastapi import HTTPException

            raise HTTPException(
                status_code=400, detail=f'Invalid sort field: {sort_by}'
            )

        order_by = getattr(self.model, sort_by)
        if sort_order == 'desc':
            order_by = order_by.desc()

        query = query.order_by(order_by)
        return query.offset(skip).limit(limit).all()


product = CRUDProduct(models.Product)
