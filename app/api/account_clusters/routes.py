from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.account_clusters import crud, schemas
from app.core.database import get_db
from app.core.security import TokenData, get_current_user

router = APIRouter()


@router.post(
    '/initiate',
    response_model=schemas.ClusterJoinRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def initiate_account_link(
    request: schemas.ClusterJoinRequestCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initiate a request to link another account.
    Sends a verification code to the target account's email.
    """
    return crud.initiate_link_request(
        db=db,
        initiator_id=current_user.citizen_id,
        target_email=request.target_email,
    )


@router.post(
    '/verify', response_model=schemas.VerifyJoinResponse, status_code=status.HTTP_200_OK
)
def verify_account_link(
    request: schemas.VerifyJoinRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify the code and complete the account linking.
    The verification code is sent to the target account's email.
    User must be logged into either the initiator or target account.
    """
    return crud.verify_and_complete_link(
        db=db,
        verification_code=request.verification_code,
        current_user_id=current_user.citizen_id,
    )


@router.get(
    '/my-cluster', response_model=schemas.ClusterInfo, status_code=status.HTTP_200_OK
)
def get_my_cluster(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get information about the cluster the current user belongs to.
    Returns None if the user is not in any cluster.
    """
    cluster_info = crud.get_cluster_info(db=db, citizen_id=current_user.citizen_id)

    if not cluster_info:
        return {
            'cluster_id': 0,
            'citizen_ids': [current_user.citizen_id],
            'member_count': 1,
            'created_at': None,
        }

    return cluster_info


@router.delete(
    '/leave',
    response_model=schemas.LeaveClusterResponse,
    status_code=status.HTTP_200_OK,
)
def leave_account_cluster(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove the current user from their account cluster.
    This is reversible - the user can re-link accounts later.
    """
    return crud.leave_cluster(db=db, citizen_id=current_user.citizen_id)
