from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AuthorizedThirdPartyAppBase(BaseModel):
    name: str
    active: bool = True

    model_config = ConfigDict(str_strip_whitespace=True)


class AuthorizedThirdPartyAppCreate(AuthorizedThirdPartyAppBase):
    name: str
    api_key: Optional[str] = None  # Optional since it will be auto-generated
    active: bool = True


class AuthorizedThirdPartyAppUpdate(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None

    model_config = ConfigDict(str_strip_whitespace=True)


class AuthorizedThirdPartyApp(AuthorizedThirdPartyAppBase):
    id: int
    api_key: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AuthorizedThirdPartyAppFilter(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    active: Optional[bool] = None
    api_key: Optional[str] = None

    model_config = ConfigDict(str_strip_whitespace=True)
