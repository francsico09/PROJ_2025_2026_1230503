import uuid
from typing import Optional

from pydantic.dataclasses import dataclass

from src.core.domain.researcher_profile.researcher_profile_model.reasearcher_profile_model import \
    ResearcherProfile
from src.core.domain.user.user_model.user_role import UserRole
from src.core.domain.user.user_schema.user_schemas import UserUpdate


@dataclass
class User:
    id: uuid.UUID
    name: str
    email: str
    active: bool
    role: UserRole
    researcherProfile: Optional[ResearcherProfile]

    def update(self, user_data: UserUpdate):
        if user_data.name:
            self.name = user_data.name

        if user_data.email:
            self.email = user_data.email

        if user_data.active:
            self.active = user_data.active

        if user_data.role:
            self.role = user_data.role


