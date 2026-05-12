import uuid
from typing import Optional

from pydantic import BaseModel

from src.core.domain.researcher_profile.researcher_profile_model.reasearcher_profile_model import \
    ResearcherProfile
from src.core.domain.researcher_profile.researcher_profile_schema.researcher_profile_schemas import \
    ResearcherProfileResponse
from src.core.domain.user.user_model.user_role import UserRole


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    active: bool
    researcherProfile: Optional[ResearcherProfileResponse] = None
    role: UserRole

    model_config = {"from_attributes": True}

class UserCreate(BaseModel):
    name: str
    email: str
    researcherProfile: Optional[ResearcherProfile] = None
    role: UserRole

    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    name: Optional[str]
    email: Optional[str]
    active: Optional[bool]
    role: Optional[UserRole]

    model_config = {"from_attributes": True}

