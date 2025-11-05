from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class JoinRequestStatus(str, Enum):
    """Status of a cluster join request."""

    PENDING = 'pending'
    VERIFIED = 'verified'
    EXPIRED = 'expired'


class AccountClusterMemberBase(BaseModel):
    """Base schema for account cluster member."""

    cluster_id: int
    citizen_id: int


class AccountClusterMember(AccountClusterMemberBase):
    """Schema for account cluster member with full data."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClusterJoinRequestBase(BaseModel):
    """Base schema for cluster join request."""

    initiator_citizen_id: int
    target_citizen_id: int


class ClusterJoinRequestCreate(BaseModel):
    """Schema for creating a cluster join request."""

    target_email: EmailStr


class ClusterJoinRequest(ClusterJoinRequestBase):
    """Schema for cluster join request with full data."""

    id: int
    verification_code: str
    code_expiration: datetime
    status: JoinRequestStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClusterJoinRequestResponse(BaseModel):
    """Response after initiating a join request."""

    message: str
    request_id: int


class VerifyJoinRequest(BaseModel):
    """Schema for verifying a join request."""

    verification_code: str


class VerifyJoinResponse(BaseModel):
    """Response after verifying a join request."""

    message: str
    cluster_id: int


class ClusterInfo(BaseModel):
    """Information about a cluster."""

    cluster_id: int
    citizen_ids: List[int]
    member_count: int
    created_at: Optional[datetime] = None


class LeaveClusterResponse(BaseModel):
    """Response after leaving a cluster."""

    message: str
