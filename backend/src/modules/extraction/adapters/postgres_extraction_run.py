import uuid

from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.repositories.general_repository import GeneralRepository, T
from src.core.domain.extraction_run.extraction_run_model.extraction_run_model import ExtractionRun
from src.database.models.extraction_run_orm import ExtractionRunORM
from src.core.repositories.postgres_base_repository import PostgresBaseRepository

class PostgresExtractionRunRepository(PostgresBaseRepository, GeneralRepository[ExtractionRun]):
    """
    Implementation of the abstract methods from the GeneralRepository
    and specific entity repository interfaces
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    """
    Not implemented, as is not needed.
    """
    async def fetch(self, params): pass

    async def get_all(
            self
    ) -> list[ExtractionRun]:
        """
        Asynchronous function to fetch all researcher profiles. If there are no researcher profiles,
        the list is returned empty.

        :return list[ResearcherProfile]:
        """
        result = await self._session.execute(
            select(ExtractionRunORM)
            .options(selectinload(ExtractionRunORM.metrics))
        )

        return [obj.to_domain() for obj in result.scalars().all()]

    async def get_by_id(
            self,
            run_id: uuid.UUID
    ) -> Optional[ExtractionRun]:
        """
        Asynchronous function to fetch an extraction run by id.
        If there are no extraction run with the provided id, return None.

        :param run_id: internal system id of the extraction run

        :return profile: Optional[ExtractionRun]
        """
        result = await self._session.execute(
            select(ExtractionRunORM)
            .options(selectinload(ExtractionRunORM.metrics))
            .where(
                ExtractionRunORM.id == run_id
            )
        )

        obj = result.scalar_one_or_none()
        return obj.to_domain() if obj else None

    async def save(
            self,
            entity: ExtractionRun
    ) -> T:
        """
       Asynchronous function to save the changes made. Returns the saved extraction run.

       :param entity: extraction run to be saved

       :return: ExtractionRun
       """
        orm = ExtractionRunORM.from_domain(entity)
        merged = await self._session.merge(orm)

        try:
            await self._session.flush()
        except Exception as e:
            await self._session.rollback()
            raise e

        return merged.to_domain()

    async def delete(
            self,
            run_id: uuid.UUID
    ) -> None:
        """
        Asynchronous function to delete an extraction run by id.

        :param run_id: internal system id of the extraction run to be deleted
        """
        await self._session.execute(
            delete(ExtractionRunORM)
            .where(ExtractionRunORM.id == run_id)
        )

        await self._session.flush()
