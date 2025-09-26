from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.core.database import Base
from app.core.utils import current_time


class AuthorizedThirdPartyApp(Base):
    __tablename__ = 'authorized_third_party_apps'

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        unique=True,
        index=True,
    )
    name = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=current_time)
    updated_at = Column(DateTime, default=current_time, onupdate=current_time)
