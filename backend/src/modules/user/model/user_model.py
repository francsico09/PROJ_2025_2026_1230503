import uuid
from typing import Optional

from pydantic.dataclasses import dataclass
from pyparsing import empty

from src.modules.researcher_profile.model.reasearcher_profile_model import ResearcherProfile
from src.modules.user.model.role.user_role import UserRole
from src.modules.user.schema.user_schemas import UserUpdate


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


