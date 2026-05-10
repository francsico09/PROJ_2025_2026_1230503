import uuid

from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.repositories.general_repository import GeneralRepository, T

from src.modules.extraction.model.extraction_run_model import ExtractionRun

from src.database.models.extraction_run_orm import ExtractionRunORM

"""
Implementation of the abstract methods from the GeneralRepository
and specific entity repository interfaces
"""
class PostgresExtractionRunRepository(GeneralRepository[ExtractionRun]):
    def __init__(self, session: AsyncSession):
        self._session = session

    """
    Asynchronous function to fetch all researcher profiles. If there are no researcher profiles,
    the list is returned empty.

    :return list[ResearcherProfile]:
    """
    async def get_all(
            self
    ) -> list[ExtractionRun]:
        result = await self._session.execute(
            select(ExtractionRunORM)
            .options(selectinload(ExtractionRunORM.metrics))
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
            run_id: uuid.UUID
    ) -> Optional[ExtractionRun]:
        result = await self._session.execute(
            select(ExtractionRunORM)
            .options(selectinload(ExtractionRunORM.metrics))
            .where(
                ExtractionRunORM.id == run_id
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
            entity: ExtractionRun
    ) -> T:
        orm = ExtractionRunORM.from_domain(entity)
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
            run_id: uuid.UUID
    ) -> None:
        await self._session.execute(
            delete(ExtractionRunORM)
            .where(ExtractionRunORM.id == run_id)
        )

        await self._session.flush()
