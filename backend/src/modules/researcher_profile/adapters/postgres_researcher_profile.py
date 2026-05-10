import uuid

from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.repositories.general_repository import T
from src.database.models.researcher_profile_orm import ResearcherProfileORM
from src.modules.researcher_profile.model.reasearcher_profile_model import ResearcherProfile
from src.modules.researcher_profile.repository.researcher_profile_repository import ResearcherProfileRepository

from src.database.models.user_orm import UserORM

"""
Implementation of the abstract methods from the GeneralRepository
and specific entity repository interfaces
"""
class PostgresResearcherProfileRepository(ResearcherProfileRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    """
    Asynchronous function to fetch ResearcherProfiles by scholar_id. If there are no ResearcherProfiles with
    the provided scholar_id, return None.
    
    :param scholar_id str: scholar id of the researcher
    
    :return profile ResearcherProfile: 
    """
    async def get_by_scholar_id(
            self,
            scholar_id: str
    ) -> Optional[ResearcherProfile]:
        result = await self._session.execute(
            select(ResearcherProfileORM)
            .options(selectinload(ResearcherProfileORM.metrics))
            .where(
                ResearcherProfileORM.scholar_id == scholar_id
            )
        )

        obj = result.scalar_one_or_none()
        return obj.to_domain() if obj else None

    """
    Asynchronous function to fetch ResearcherProfiles by scholar_id. If there are no ResearcherProfiles with
    the provided scholar_id, return None.
    
    :param scholar_id str: scholar id of the researcher
    
    :return profile ResearcherProfile: 
    """
    async def get_by_user_id(
            self,
            user_id: uuid.UUID
    ) -> Optional[ResearcherProfile]:
        stmt = (
            select(ResearcherProfileORM)
            .join(UserORM, UserORM.researcher_profile_id == ResearcherProfileORM.id)
            .where(UserORM.id == user_id)
            .options(selectinload(ResearcherProfileORM.metrics))
        )

        result = await self._session.execute(stmt)
        obj = result.scalar_one_or_none()

        return obj.to_domain() if obj else None

    """
    Asynchronous function to fetch researcher profiles by orcid. If there are no researcher profiles with
    the provided orcid, return None.
    
    :param orcid str: orcid of the researcher

    :return Optional[ResearcherProfile]:
    """
    async def get_by_orcid(
            self,
            orcid: str
    ) -> Optional[ResearcherProfile]:
        result = await self._session.execute(
            select(ResearcherProfileORM)
            .options(selectinload(ResearcherProfileORM.metrics))
            .where(
                ResearcherProfileORM.orcid == orcid
            )
        )

        obj = result.scalar_one_or_none()
        return obj.to_domain() if obj else None

    """
    Asynchronous function to fetch all researcher profiles. If there are no researcher profiles,
    the list is returned empty.

    :return list[ResearcherProfile]:
    """
    async def get_all(
            self
    ) -> list[ResearcherProfile]:
        result = await self._session.execute(
            select(ResearcherProfileORM)
            .options(selectinload(ResearcherProfileORM.metrics))
        )

        return [obj.to_domain() for obj in result.scalars().all()]

    """
    Asynchronous function to fetch a researcher profile by id. If there are no researcher profiles with
    the provided id, return None.

    :param profile_id UUID: internal system id of the researcher profile

    :return profile Optional[ResearcherProfile]:
    """
    async def get_by_id(
            self,
            profile_id: uuid.UUID
    ) -> Optional[ResearcherProfile]:
        result = await self._session.execute(
            select(ResearcherProfileORM)
            .options(selectinload(ResearcherProfileORM.metrics))
            .where(
                ResearcherProfileORM.id == profile_id
            )
        )

        obj = result.scalar_one_or_none()
        return obj.to_domain() if obj else None
    """
    Asynchronous function to save the changes made. Returns the saved researcher profile.

    :param entity ResearcherProfile: profile to be saved

    :return ResearcherProfile:
    """
    async def save(
            self,
            entity: ResearcherProfile
    ) -> T:
        orm = ResearcherProfileORM.from_domain(entity)
        merged = await self._session.merge(orm)

        try:
            await self._session.flush()
        except Exception as e:
            await self._session.rollback()
            raise e

        return merged.to_domain()

    """
    Asynchronous function to delete a researcher profile by id.

    :param profile_id UUID: internal system id of the researcher profile to be deleted
    """
    async def delete(
            self,
            profile_id: uuid.UUID
    ) -> None:
        await self._session.execute(
            delete(ResearcherProfileORM)
            .where(ResearcherProfileORM.id == profile_id)
        )

        await self._session.flush()
