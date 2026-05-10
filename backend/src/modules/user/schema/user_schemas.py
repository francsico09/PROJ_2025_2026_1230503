import uuid
from typing import Optional

from pydantic import BaseModel

from src.modules.researcher_profile.model.reasearcher_profile_model import ResearcherProfile
from src.modules.researcher_profile.schema.researcher_profile_schemas import ResearcherProfileResponse
from src.modules.user.model.role.user_role import UserRole


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

