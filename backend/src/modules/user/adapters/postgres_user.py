import uuid

from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.user_orm import UserORM
from src.modules.user.repository.user_repository import UserRepository
from src.database.models.researcher_profile_orm import ResearcherProfileORM
from src.core.domain.pagination.schema.pagination_schema import PaginatedResponse, PaginationParams
from src.core.repositories.postgres_base_repository import PostgresBaseRepository
from src.core.domain.user.user_model.user_model import User


class PostgresUserRepository(PostgresBaseRepository, UserRepository):
    """
    Implementation of the abstract methods from the GeneralRepository
    and specific entity repository interfaces
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch(
            self,
            params: PaginationParams,
            exclude_names: list[str] = None
    ) -> PaginatedResponse:
        """
        Implementations of the fetch method. Returns a paginated and filtered
        result given certain parameters.
        Uses the _fetch_paginated method from the PostgresBaseRepository to
        avoid code repetition.

        :param params: PaginationParams with ordering and filtering information

        :return: PaginatedResponse
        """
        extra_filters = []

        if exclude_names:
            extra_filters.append(UserORM.name.notin_(exclude_names))

        return await self._fetch_paginated(
            model=UserORM,
            params=params,
            search_columns=[
                UserORM.name,
                UserORM.email
            ],
            load_options=[
                selectinload(UserORM.researcher_profile)
                .selectinload(ResearcherProfileORM.metrics)
            ],
            extra_filters=extra_filters or None,
        )

    async def get_all(self) -> list[User]:
        result = await self._session.execute(
            select(UserORM)
            .options(
                selectinload(UserORM.researcher_profile)
                .selectinload(ResearcherProfileORM.metrics)
            )
        )

        return [obj.to_domain() for obj in result.scalars().all()]

    async def get_by_email(
            self,
            email: str
    ) -> Optional[User]:
        """
        Function to fetch users by email. If there are no users with the provided email,
        the list is returned empty.

        :param email: email of the user

        :return list[User]:
        """

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


    async def get_by_id(
            self,
            user_id: uuid.UUID
    ) -> Optional[User]:
        """
        Asynchronous function to fetch users by id. If there are no users with the given id,
        the return is None.

        :param user_id: internal system id of the user to be fetched

        :return Optional[User]:
        """

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


    async def save(
            self,
            entity: User
    ) -> User:
        """
        Asynchronous function to save the changes made. Returns the saved user.

        :param entity: User to be saved

        :return User:
        """

        orm = UserORM.from_domain(entity)

        merged = await self._session.merge(orm)

        try:
            await self._session.flush()

        except Exception as e:
            raise e

        return merged.to_domain()


    async def delete(
            self,
            user_id: uuid.UUID
    ) -> None:
        """
        Asynchronous function to delete a user by id.

        :param user_id: internal system id of the user to be deleted
        """

        await self._session.execute(
            delete(UserORM).where(UserORM.id == user_id)
        )

        await self._session.flush()