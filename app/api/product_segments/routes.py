from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.api.product_segments import schemas
from app.api.product_segments.crud import product_segment as product_segment_crud
from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get('/', response_model=list[schemas.ProductSegment])
def get_product_segments(
    filters: schemas.ProductSegmentFilter = Depends(),
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
):
    if x_api_key != settings.APPLICATION_REVIEW_API_KEY:
        raise HTTPException(status_code=403, detail='Invalid API key')

    return product_segment_crud.find(
        db=db,
        filters=filters,
        limit=1000,
    )
