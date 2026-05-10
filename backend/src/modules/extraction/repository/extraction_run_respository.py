from abc import abstractmethod

from src.core.repositories.general_repository import GeneralRepository

from src.modules.extraction.model.extraction_run_model import ExtractionRun


class ResearcherProfileRepository(GeneralRepository[ExtractionRun]): pass
