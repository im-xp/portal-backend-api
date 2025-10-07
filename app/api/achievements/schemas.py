from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.api.citizens.schemas import Citizen


class AchievementBase(BaseModel):
    sender_id: int
    receiver_id: int
    achievement_type: str
    sent_at: datetime
    message: Optional[str] = None
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )


class AchievementCreate(BaseModel):
    receiver_id: int
    achievement_type: str
    message: Optional[str] = None


class Achievement(AchievementBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class AchievementFilter(BaseModel):
    id: Optional[int] = None
    id_in: Optional[List[int]] = None
    sender_id: Optional[int] = None
    receiver_id: Optional[int] = None
    achievement_type: Optional[str] = None
    message: Optional[str] = None


class AchievementWithCitizen(BaseModel):
    achievement: Achievement
    citizen: Citizen


class AchievementResponse(BaseModel):
    sent_achievements: List[AchievementWithCitizen]
    received_achievements: List[AchievementWithCitizen]
