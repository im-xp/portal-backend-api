import csv
import io

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.api.citizens.models import Citizen

from app.api.applications import models, schemas
from app.api.applications.crud import application as application_crud
from app.api.attendees import schemas as attendees_schemas
from app.api.common.schemas import PaginatedResponse, PaginationMetadata
from app.core.config import settings
from app.core.database import get_db
from app.core.logger import logger
from app.core.security import TokenData, get_current_user

router = APIRouter()


@router.post(
    '/',
    response_model=schemas.Application,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    application: schemas.ApplicationCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info('Creating application: %s', application)
    return application_crud.create(db=db, obj=application, user=current_user)


@router.get('/', response_model=list[schemas.Application])
def get_applications(
    current_user: TokenData = Depends(get_current_user),
    filters: schemas.ApplicationFilter = Depends(),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return application_crud.find(
        db=db,
        skip=skip,
        limit=limit,
        filters=filters,
        user=current_user,
    )


@router.get('/residencies', response_model=list[schemas.Residency])
def get_residencies(current_user: TokenData = Depends(get_current_user)):
    return list(schemas.Residency)


@router.get(
    '/attendees_directory/{popup_city_id}',
    response_model=PaginatedResponse[schemas.AttendeesDirectory],
)
def get_attendees_directory(
    popup_city_id: int,
    filters: schemas.AttendeesDirectoryFilter = Depends(),
    skip: int = 0,
    limit: int = 100,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info('Getting attendees directory: %s', filters)
    attendees, total = application_crud.get_attendees_directory(
        db=db,
        popup_city_id=popup_city_id,
        filters=filters,
        skip=skip,
        limit=limit,
        user=current_user,
    )
    return PaginatedResponse(
        items=attendees,
        pagination=PaginationMetadata(
            skip=skip,
            limit=limit,
            total=total,
        ),
    )


@router.get('/attendees_directory/{popup_city_id}/csv')
def get_attendees_directory_csv(
    popup_city_id: int,
    filters: schemas.AttendeesDirectoryFilter = Depends(),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info('Getting attendees directory: %s', filters)
    csv_content = application_crud.get_attendees_directory_csv(
        db=db,
        popup_city_id=popup_city_id,
        filters=filters,
        user=current_user,
    )
    return Response(
        content=csv_content,
        media_type='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename="attendees_directory.csv"'
        },
    )


@router.get('/world-addresses/{popup_city_id}/csv')
def get_world_addresses_csv(
    popup_city_id: int,
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
):
    """Get all citizens with world addresses from applications in a popup city as CSV

    Authentication: API key required via X-API-Key header
    """
    # Validate API key
    if x_api_key != settings.API_KEY_WORLD_ADDRESSES:
        raise HTTPException(status_code=401, detail='Invalid API key')

    logger.info(
        'Getting citizens with world addresses as CSV for popup city: %s', popup_city_id
    )
    applications_with_world_addresses = (
        db.query(Citizen.world_address)
        .join(models.Application, models.Application.citizen_id == Citizen.id)
        .filter(
            models.Application.popup_city_id == popup_city_id,
            Citizen.world_address.isnot(None),
            Citizen.world_address != '',
        )
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['World Address'])

    # Write data rows - only world addresses
    for (world_address,) in applications_with_world_addresses:
        writer.writerow([world_address])

    csv_content = output.getvalue()

    return Response(
        content=csv_content,
        media_type='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename="world_addresses_popup_{popup_city_id}.csv"'
        },
    )


@router.get('/{application_id}', response_model=schemas.Application)
def get_application(
    application_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return application_crud.get(db=db, id=application_id, user=current_user)


@router.put('/{application_id}', response_model=schemas.Application)
def update_application(
    application_id: int,
    application: schemas.ApplicationUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info('Updating application: %s: %s', application_id, application)
    return application_crud.update(
        db=db,
        id=application_id,
        obj=application,
        user=current_user,
    )


@router.post('/{application_id}/attendees', response_model=schemas.Application)
def create_attendee(
    application_id: int,
    attendee: attendees_schemas.AttendeeCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info('Creating attendee: %s', attendee)
    return application_crud.create_attendee(
        db=db,
        application_id=application_id,
        attendee=attendee,
        user=current_user,
    )


@router.put(
    '/{application_id}/attendees/{attendee_id}',
    response_model=schemas.Application,
)
def update_attendee(
    application_id: int,
    attendee_id: int,
    attendee: attendees_schemas.AttendeeUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info('Updating attendee: %s: %s', attendee_id, attendee)
    return application_crud.update_attendee(
        db=db,
        application_id=application_id,
        attendee_id=attendee_id,
        attendee=attendee,
        user=current_user,
    )


@router.delete(
    '/{application_id}/attendees/{attendee_id}',
    response_model=schemas.Application,
)
def delete_attendee(
    application_id: int,
    attendee_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info('Deleting attendee: %s: %s', application_id, attendee_id)
    return application_crud.delete_attendee(
        db=db,
        application_id=application_id,
        attendee_id=attendee_id,
        user=current_user,
    )
