from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base
from app.core.utils import current_time

if TYPE_CHECKING:
    from app.api.citizens.models import Citizen


class AccountClusterMember(Base):
    """Represents membership of a citizen in an account cluster."""

    __tablename__ = 'account_cluster_members'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_id = Column(Integer, nullable=False, index=True)
    citizen_id = Column(Integer, ForeignKey('humans.id'), nullable=False, unique=True)
    created_at = Column(DateTime, default=current_time)

    # Relationships
    citizen: Mapped['Citizen'] = relationship('Citizen')


class ClusterJoinRequest(Base):
    """Represents a pending request to join accounts into a cluster."""

    __tablename__ = 'cluster_join_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    initiator_citizen_id = Column(
        Integer, ForeignKey('humans.id'), nullable=False, index=True
    )
    target_citizen_id = Column(
        Integer, ForeignKey('humans.id'), nullable=False, index=True
    )
    verification_code = Column(String, nullable=False, unique=True, index=True)
    code_expiration = Column(DateTime, nullable=False)
    # pending, verified, expired
    status = Column(String, nullable=False, default='pending')
    created_at = Column(DateTime, default=current_time)

    # Relationships
    initiator: Mapped['Citizen'] = relationship(
        'Citizen', foreign_keys=[initiator_citizen_id]
    )
    target: Mapped['Citizen'] = relationship(
        'Citizen', foreign_keys=[target_citizen_id]
    )
