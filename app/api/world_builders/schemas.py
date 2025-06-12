from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class WorldBuilderBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    personal_links: Optional[str] = None
    x_handle: Optional[str] = None
    project_description: Optional[str] = None
    project_stage: Optional[str] = None
    funding_status: Optional[str] = None
    team_description: Optional[str] = None
    tech_stack: Optional[str] = None
    edge_nexus_benefit: Optional[str] = None
    edge_nexus_cohort: Optional[str] = None
    financial_situation: Optional[str] = None
    financial_support_reason: Optional[str] = None
    extra_info: Optional[str] = None
    integration_potential: Optional[str] = None
    send_proposal: Optional[bool] = None
    accepted: Optional[str] = None
    notes: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WorldBuilderCreate(WorldBuilderBase):
    pass


class WorldBuilderUpdate(WorldBuilderBase):
    pass


class WorldBuilder(WorldBuilderBase):
    id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class WorldBuilderFilter(BaseModel):
    email: Optional[str] = None
