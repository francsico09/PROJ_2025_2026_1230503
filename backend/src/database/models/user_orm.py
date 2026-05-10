import uuid

from sqlalchemy import Boolean, Column, String, ForeignKey
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from src.database.base.base import Base

from src.database.models.researcher_profile_orm import ResearcherProfileORM


class UserORM(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    email = Column(String, unique=True)
    active = Column(Boolean)

    role = Column(String)

    researcher_profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("researcher_profiles.id", ondelete="CASCADE"),
        nullable=True
    )
    researcher_profile = relationship(
        "ResearcherProfileORM",
       cascade="all, delete-orphan",
        single_parent=True,
        lazy="joined"
    )

    def to_domain(self):
        from src.modules.user.model.user_model import User
        from src.modules.user.model.role.user_role import UserRole

        return User(
            id=self.id,
            name=self.name,
            email=self.email,
            active=self.active,
            role=UserRole[self.role],
            researcherProfile=self.researcher_profile.to_domain()
            if self.researcher_profile else None
        )

    @staticmethod
    def from_domain(entity):

        if isinstance(entity, UserORM):
            return entity

        orm = UserORM(
            id=entity.id,
            name=entity.name,
            email=entity.email,
            active=entity.active,
            role=entity.role.value,
        )
        if entity.researcherProfile:
            orm.researcher_profile = ResearcherProfileORM.from_domain(entity.researcherProfile)
        return orm
