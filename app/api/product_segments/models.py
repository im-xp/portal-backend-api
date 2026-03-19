from typing import TYPE_CHECKING, List

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base
from app.core.utils import current_time

if TYPE_CHECKING:
    from app.api.popup_city.models import PopUpCity
    from app.api.products.models import Product


class ProductSegmentProduct(Base):
    __tablename__ = 'product_segment_products'

    product_segment_id = Column(
        Integer, ForeignKey('product_segments.id'), primary_key=True
    )
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)


class ProductSegment(Base):
    __tablename__ = 'product_segments'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    popup_city_id = Column(Integer, ForeignKey('popups.id'), index=True, nullable=False)

    popup_city: Mapped['PopUpCity'] = relationship('PopUpCity', lazy='joined')
    products: Mapped[List['Product']] = relationship(
        'Product', secondary='product_segment_products', backref='product_segments'
    )

    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
