import uuid

from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.repositories.general_repository import T
from src.database.models.researcher_profile_orm import ResearcherProfileORM

from src.core.domain.researcher_profile.researcher_profile_model.reasearcher_profile_model import \
    ResearcherProfile
from src.modules.researcher_profile.repository.researcher_profile_repository import ResearcherProfileRepository
from src.database.models.user_orm import UserORM
from src.core.repositories.postgres_base_repository import PostgresBaseRepository
from src.core.domain.pagination.schema.pagination_schema import PaginationParams, PaginatedResponse


class PostgresResearcherProfileRepository(PostgresBaseRepository, ResearcherProfileRepository):
    """
    Implementation of the abstract methods from the GeneralRepository
    and specific entity repository interfaces
    """
    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch(self, params: PaginationParams) -> PaginatedResponse:
        """
        Implementations of the fetch method. Returns a paginated and filtered
        result given certain parameters.
        Uses the _fetch_paginated method from the PostgresBaseRepository to
        avoid code repetition.

        :param params: PaginationParams with ordering and filtering information

        :return: PaginatedResponse
        """
        return await self._fetch_paginated(
            model=ResearcherProfileORM,
            params=params,
            search_columns=[
                ResearcherProfileORM.scholar_id,
                ResearcherProfileORM.orcid,
                ResearcherProfileORM.wos_id,
                ResearcherProfileORM.scopus_id,
                # For joins
                UserORM.name,
                UserORM.email,
            ],
            joins=[UserORM],
            load_options=[
                selectinload(ResearcherProfileORM.metrics)
            ],
        )

    async def get_by_user_id(
            self,
            user_id: uuid.UUID
    ) -> Optional[ResearcherProfile]:
        """
        Asynchronous function to fetch ResearcherProfiles by user_id.
        If there are no ResearcherProfiles with the provided user_id,
        return None.

        :param user_id: scholar id of the researcher

        :return profile: Optional[ResearcherProfile]
        """

        stmt = (
            select(ResearcherProfileORM)
            .join(UserORM, UserORM.researcher_profile_id == ResearcherProfileORM.id)
            .where(UserORM.id == user_id)
            .options(selectinload(ResearcherProfileORM.metrics))
        )

        result = await self._session.execute(stmt)
        obj = result.scalar_one_or_none()

        return obj.to_domain() if obj else None

    async def get_by_scholar_id(
            self,
            scholar_id: str
    ) -> Optional[ResearcherProfile]:
        """
        Asynchronous function to fetch ResearcherProfiles by scholar_id. If there are no ResearcherProfiles with
        the provided scholar_id, return None.

        :param scholar_id: scholar id of the researcher

        :return profile: Optional[ResearcherProfile]
        """

        result = await self._session.execute(
            select(ResearcherProfileORM)
            .options(selectinload(ResearcherProfileORM.metrics))
            .where(
                ResearcherProfileORM.scholar_id == scholar_id
            )
        )

        obj = result.scalar_one_or_none()

        return obj.to_domain() if obj else None

    async def get_by_orcid(
            self,
            orcid: str
    ) -> Optional[ResearcherProfile]:
        """
        Asynchronous function to fetch researcher profiles by orcid. If there are no researcher profiles with
        the provided orcid, return None.

        :param orcid: orcid of the researcher

        :return: Optional[ResearcherProfile]
        """

        result = await self._session.execute(
            select(ResearcherProfileORM)
            .options(selectinload(ResearcherProfileORM.metrics))
            .where(
                ResearcherProfileORM.orcid == orcid
            )
        )

        obj = result.scalar_one_or_none()
        return obj.to_domain() if obj else None


    async def get_by_wos_id(
            self,
            wos_id: str
    ) -> Optional[ResearcherProfile]:
        """
        Asynchronous function to fetch ResearcherProfiles by wos_id. If there are no ResearcherProfiles with
        the provided wos_id, return None.

        :param wos_id: wos id of the researcher

        :return profile ResearcherProfile:
        """

        result = await self._session.execute(
            select(ResearcherProfileORM)
            .options(selectinload(ResearcherProfileORM.metrics))
            .where(
                ResearcherProfileORM.wos_id == wos_id
            )
        )

        obj = result.scalar_one_or_none()

        return obj.to_domain() if obj else None


    async def get_by_scopus_id(
            self,
            scopus_id: str
    ) -> Optional[ResearcherProfile]:
        """
        Asynchronous function to fetch ResearcherProfiles by scopus_id. If there are no ResearcherProfiles with
        the provided scopus_id, return None.

        :param scopus_id: scopus id of the researcher

        :return profile ResearcherProfile:
        """

        result = await self._session.execute(
            select(ResearcherProfileORM)
            .options(selectinload(ResearcherProfileORM.metrics))
            .where(
                ResearcherProfileORM.scopus_id == scopus_id
            )
        )

        obj = result.scalar_one_or_none()

        return obj.to_domain() if obj else None


    async def get_all(
            self
    ) -> list[ResearcherProfile]:
        """
        Asynchronous function to fetch all researcher profiles. If there are no researcher profiles,
        the list is returned empty.

        :return list[ResearcherProfile]:
        """

        result = await self._session.execute(
            select(ResearcherProfileORM)
            .options(selectinload(ResearcherProfileORM.metrics))
        )

        return [obj.to_domain() for obj in result.scalars().all()]


    async def get_by_id(
            self,
            profile_id: uuid.UUID
    ) -> Optional[ResearcherProfile]:
        """
        Asynchronous function to fetch a researcher profile by id. If there are no researcher profiles with
        the provided id, return None.

        :param profile_id: internal system id of the researcher profile

        :return profile Optional[ResearcherProfile]:
        """

        result = await self._session.execute(
            select(ResearcherProfileORM)
            .options(selectinload(ResearcherProfileORM.metrics))
            .where(
                ResearcherProfileORM.id == profile_id
            )
        )

        obj = result.scalar_one_or_none()
        return obj.to_domain() if obj else None


    async def save(
            self,
            entity: ResearcherProfile
    ) -> T:
        """
        Asynchronous function to save the changes made. Returns the saved researcher profile.

        :param entity: profile to be saved

        :return: ResearcherProfile
        """

        orm = ResearcherProfileORM.from_domain(entity)
        merged = await self._session.merge(orm)

        try:
            await self._session.flush()
        except Exception as e:
            await self._session.rollback()
            raise e

        return merged.to_domain()


    async def delete(
            self,
            profile_id: uuid.UUID
    ) -> None:
        """
        Asynchronous function to delete a researcher profile by id.

        :param profile_id: internal system id of the researcher profile to be deleted
        """

        await self._session.execute(
            delete(ResearcherProfileORM)
            .where(ResearcherProfileORM.id == profile_id)
        )

        await self._session.flush()
