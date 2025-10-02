from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base
from app.core.utils import current_time


class Achievement(Base):
    __tablename__ = 'achievements'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    sender_id = Column(Integer, ForeignKey('applications.id'), index=True, nullable=False)
    receiver_id = Column(Integer, ForeignKey('applications.id'), index=True, nullable=False)
    achievement_type = Column(String, nullable=False)
    sent_at = Column(DateTime, default=current_time, nullable=False)
    
    # Relationships to Application model
    sender: Mapped['Application'] = relationship(
        'Application', 
        foreign_keys=[sender_id]
    )
    receiver: Mapped['Application'] = relationship(
        'Application', 
        foreign_keys=[receiver_id]
    )
