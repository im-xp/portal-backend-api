from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base
from app.core.utils import current_time

if TYPE_CHECKING:
    from app.api.citizens.models import Citizen


class Achievement(Base):
    __tablename__ = 'achievements'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    sender_id = Column(Integer, ForeignKey('humans.id'), index=True, nullable=False)
    receiver_id = Column(Integer, ForeignKey('humans.id'), index=True, nullable=False)
    achievement_type = Column(String, nullable=False)
    sent_at = Column(DateTime, default=current_time, nullable=False)
    message = Column(String, nullable=True)

    # Relationships to Citizen model
    sender: Mapped['Citizen'] = relationship('Citizen', foreign_keys=[sender_id])
    receiver: Mapped['Citizen'] = relationship('Citizen', foreign_keys=[receiver_id])
