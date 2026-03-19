from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class CouponCode(BaseModel):
    id: int
    code: str
    popup_city_id: int
    discount_value: float
    applies_to: str = 'pass'

    model_config = ConfigDict(
        from_attributes=True,
    )


class CouponCodeCreate(BaseModel):
    code: str
    popup_city_id: int
    discount_value: int
    max_uses: Optional[int] = None
    is_active: bool = True
    applies_to: str = 'pass'

    @field_validator('discount_value')
    def validate_discount_value(cls, v: int) -> int:
        if v < 0 or v > 100 or v % 10 != 0:
            raise ValueError('discount_value must be 0, 10, 20, ..., 90, or 100')
        return v

    @field_validator('applies_to')
    def validate_applies_to(cls, v: str) -> str:
        if v not in ('pass', 'lodging', 'all'):
            raise ValueError("applies_to must be 'pass', 'lodging', or 'all'")
        return v
