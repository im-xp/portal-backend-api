from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.api.products.schemas import Product


class ProductSegmentFilter(BaseModel):
    popup_city_slug: Optional[str] = None


class ProductSegment(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    popup_city_id: int
    products: List[Product] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
    )
