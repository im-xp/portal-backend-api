from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.applications.models import Application
from app.api.products import schemas
from app.api.products.crud import product as product_crud
from app.core.database import get_db
from app.core.security import TokenData, get_current_user

router = APIRouter()


@router.get('/', response_model=list[schemas.Product])
def get_products(
    current_user: TokenData = Depends(get_current_user),
    filters: schemas.ProductFilter = Depends(),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    sort_by: str = Query(default='name', description='Field to sort by'),
    sort_order: str = Query(default='asc', pattern='^(asc|desc)$'),
    db: Session = Depends(get_db),
):
    product_segment_id = None
    if filters.popup_city_id:
        application = (
            db.query(Application)
            .filter(
                Application.citizen_id == current_user.citizen_id,
                Application.popup_city_id == filters.popup_city_id,
            )
            .first()
        )
        if application and application.product_segment_id:
            product_segment_id = application.product_segment_id

    return product_crud.find(
        db=db,
        skip=skip,
        limit=limit,
        filters=filters,
        user=current_user,
        sort_by=sort_by,
        sort_order=sort_order,
        product_segment_id=product_segment_id,
    )


@router.get('/{product_id}', response_model=schemas.Product)
def get_product(
    product_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return product_crud.get(db=db, id=product_id, user=current_user)
