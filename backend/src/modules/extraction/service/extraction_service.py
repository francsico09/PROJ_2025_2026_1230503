import logging
import uuid

from datetime import datetime
from uuid import UUID

from src.core.repositories.repositories import Repositories
from src.modules.extraction.extractor.orcid_extractor import OrcidExtractor
from src.modules.extraction.extractor.scholar_extractor import ScholarExtractor
from src.modules.extraction.extractor.wos_extractor import WosExtractor
from src.modules.extraction.extractor.scopus_extractor import ScopusExtractor
from src.core.domain.extraction_run.extraction_run_model.extraction_run_model import ExtractionRun, \
    ExtractionTrigger, ExtractionStatus
from src.core.domain.researcher_metric.researcher_metric_model.source_model import SourceName
from src.modules.normalization.models.result.normalization_result import RawExtractionResult

logger = logging.getLogger(__name__)


class ExtractionService:

    def __init__(
            self,
            repos: Repositories,
            scholar_extractor: ScholarExtractor,
            orcid_extractor: OrcidExtractor,
            wos_extractor: WosExtractor,
            scopus_extractor: ScopusExtractor
    ) -> None:
        self._repos = repos
        self._scholar = scholar_extractor
        self._orcid = orcid_extractor
        self._wos = wos_extractor
        self._scopus = scopus_extractor

    async def extract_for_user(self, user_id: UUID) -> RawExtractionResult:
        async with self._repos as repos:
            user = await repos.users.get_by_id(user_id)
            profile = await repos.profiles.get_by_user_id(user_id)

        if not user:
            raise ValueError(f"User {user_id} not found")

        if not profile:
            raise ValueError(f"Profile no found for user: {user_id}")

        result = RawExtractionResult(user_id=str(user_id),
                                     run=ExtractionRun(
                                         id=uuid.uuid4(),
                                         researcher_id=profile.id,
                                         triggered_at=datetime.now(),
                                         triggered_by=ExtractionTrigger.manual,
                                         status=ExtractionStatus.pending,
                                         sources_attempted=[],
                                         sources_succeeded=[],
                                     ))

        # --- Scholar ---
        result.run.sources_attempted.append(SourceName.scholar)

        scholar_identifier = profile.scholar_id if profile else None
        scholar_query = scholar_identifier or user.name
        scholar_data = self._scholar.extract(scholar_query)

        if scholar_data:
            result.run.sources_succeeded.append(SourceName.scholar)
            result.scholar = scholar_data
        else:
            search_type = "ID" if scholar_identifier else "name"
            result.errors.append(f"Scholar: no results for {search_type} '{scholar_query}'")

        # --- WoS ---
        result.run.sources_attempted.append(SourceName.wos)

        wos_id = profile.wos_id if profile else None

        if wos_id:
            wos_data = self._wos.extract(user.name, profile.keywords)
            if wos_data:
                result.run.sources_succeeded.append(SourceName.wos)
                result.wos = wos_data
            else:
                result.errors.append(f"WoS: no results for ID '{wos_id}'")
        else:
            logger.info(f"[Extraction] No WoS ID for user {user_id}, skipping.")

        # --- Scopus ---
        result.run.sources_attempted.append(SourceName.scopus)

        scopus_identifier = profile.scopus_id if profile.scopus_id else user.name

        if scopus_identifier:
            scopus_data = self._scopus.extract(scopus_identifier)
            if scopus_data:
                result.run.sources_succeeded.append(SourceName.scopus)
                result.scopus = scopus_data
            else:
                search_type = "ID" if profile.scopus_id else "name"
                result.errors.append(f"Scopus: no results for {search_type} '{scopus_identifier}'")
        else:
            logger.info(f"[Extraction] No Scopus identifier for user {user_id}, skipping.")

        # --- ORCID ---
        result.run.sources_attempted.append(SourceName.orcid)

        orcid_id = profile.orcid if profile else None

        if orcid_id:
            orcid_data = self._orcid.extract_by_id(orcid_id)
            if orcid_data:
                result.run.sources_succeeded.append(SourceName.orcid)
                result.orcid = orcid_data
            else:
                result.errors.append(f"ORCID: no results for ID '{orcid_id}'")
        else:
            logger.info(f"[Extraction] No ORCID for user {user_id}, skipping.")

        result.run.status = ExtractionStatus.completed if not result.errors else ExtractionStatus.partial

        return result

    async def extract_for_all_users(self) -> list[RawExtractionResult]:
        async with self._repos as repos:
            users = await repos.users.get_all()

        results = []
        for user in users:
            if not user.active:
                continue
            try:
                result = await self.extract_for_user(user.id)
                results.append(result)
            except Exception as e:
                logger.error(f"[Extraction] Error for user {user.id}: {e}")
                results.append(RawExtractionResult(
                    user_id=str(user.id),
                    errors=[f"fatal error: {str(e)}"],
                ))

        return results