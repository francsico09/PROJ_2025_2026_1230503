import uuid

from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from src.database.models.user_orm import UserORM
from src.modules.user.model.role.user_role import UserRole
from src.modules.user.model.user_model import User
from src.modules.user.repository.user_repository import UserRepository

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.researcher_profile_orm import ResearcherProfileORM

"""
    Implementation of the abstract methods from the GeneralRepository
    and specific entity repository interfaces
"""
class PostgresUserRepository(UserRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    """
    Function to fetch users by name. If there are no users with the provided name,
    the list is returned empty.
    
    :param name str: name of the user
    
    :return list[User]:
    """
    async def get_by_name(
            self,
            name: str
    ) -> list[User]:
        result = await self._session.execute(
            select(UserORM)
            .options(
                selectinload(UserORM.researcher_profile)
                .selectinload(ResearcherProfileORM.metrics)
            )
            .where(
                UserORM.name == name
            )
        )

        return [obj.to_domain() for obj in result.scalars().all()]

    """
    Function to fetch users by email. If there are no users with the provided email,
    the list is returned empty.
    
    :param email str: email of the user

    :return list[User]:
    """
    async def get_by_email(
            self,
            email: str
    ) -> User:
        result = await self._session.execute(
            select(UserORM)
            .options(
                selectinload(UserORM.researcher_profile)
                .selectinload(ResearcherProfileORM.metrics)
            )
            .where(
                UserORM.email == email
            )
        )

        obj = result.scalar_one_or_none()
        return obj.to_domain() if obj else None

    """
    Function to fetch users by role. If there are no users with the provided role,
    the list is returned empty.
    
    :param role Role: user role to filter

    :return list[User]:
    """
    async def get_by_role(
            self,
            role: UserRole
    ) -> list[User]:
        result = await self._session.execute(
            select(UserORM)
            .options(
                selectinload(UserORM.researcher_profile)
                .selectinload(ResearcherProfileORM.metrics)
            )
            .where(
                UserORM.role == role
            )
        )

        return [obj.to_domain() for obj in result.scalars().all()]

    """
    Asynchronous function to fetch all the users. If there are no users, the list is returned empty.

    :return list[User]:
    """
    async def get_all(
            self
    ) -> list[User]:
        result = await self._session.execute(
            select(UserORM)
            .options(
                selectinload(UserORM.researcher_profile)
                .selectinload(ResearcherProfileORM.metrics)
            )
        )
        return [obj.to_domain() for obj in result.scalars().all()]

    """
    Asynchronous function to fetch users by id. If there are no users with the given id, 
    the return is None.

    :param user_id UUID: internal system id of the user to be fetched

    :return Optional[User]:
    """
    async def get_by_id(
            self,
            user_id: uuid.UUID
    ) -> Optional[User]:
        result = await self._session.execute(
            select(UserORM)
            .options(
                selectinload(UserORM.researcher_profile)
                .selectinload(ResearcherProfileORM.metrics)
            )
            .where(
                UserORM.id == user_id
            )
        )

        orm = result.scalar_one_or_none()
        return orm.to_domain() if orm else None

    """
    Asynchronous function to save the changes made. Returns the saved metric.

    :param entity ResearcherMetric: Metric to be saved

    :return ResearcherMetric:
    """
    async def save(
            self,
            entity: User
    ) -> User:
        orm = UserORM.from_domain(entity)

        merged = await self._session.merge(orm)

        try:
            await self._session.flush()
        except Exception as e:
            raise e

        return merged.to_domain()

    """
    Asynchronous function to delete a user by id.

    :param user_id UUID: internal system id of the metric to be deleted
    """
    async def delete(
            self,
            user_id: uuid.UUID
    ) -> None:
        await self._session.execute(
            delete(UserORM).where(UserORM.id == user_id)
        )

        await self._session.flush()
