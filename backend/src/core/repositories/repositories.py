from src.core.session import AsyncSessionFactory
from src.modules.metrics.adapters.postgres_researcher_metric import PostgresResearcherMetricRepository
from src.modules.researcher_profile.adapters.postgres_researcher_profile import PostgresResearcherProfileRepository
from src.modules.user.adapters.postgres_user import PostgresUserRepository
from src.modules.extraction.adapters.postgres_extraction_run import PostgresExtractionRunRepository

from sqlalchemy.ext.asyncio import AsyncSession

"""
    This is the application of the Unit of Work design pattern on
    the repository entities.
    
    This class centralizes the application session for all repositories,
    making synchronization easier. This is used in services, so that if
    access to more than one repository is needed, the access is easier.
    
    Also, this implementations allows for only one commit action even
    with more then one repository working and, in the case of a failure,
    everything can be rolled back to the previous state in one action.
"""
class Repositories:
    def __init__(self):
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> "Repositories":
        self._session = AsyncSessionFactory()
        self.users = PostgresUserRepository(self._session)
        self.profiles = PostgresResearcherProfileRepository(self._session)
        self.metrics = PostgresResearcherMetricRepository(self._session)
        self.extraction_runs = PostgresExtractionRunRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            await self._session.rollback()
        else:
            await self._session.commit()
        await self._session.close()

    """
    Asynchronous function to commit the changes made to the repositories.
    """
    async def commit(self) -> None:
        await self._session.commit()

    """
    Asynchronous function to roll back the changes made to the repositories.
    """
    async def rollback(self) -> None:
        await self._session.rollback()

