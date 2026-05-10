from abc import abstractmethod

from src.core.repositories.general_repository import GeneralRepository
from src.modules.researcher_profile.model.reasearcher_profile_model import ResearcherProfile

class ResearcherProfileRepository(GeneralRepository[ResearcherProfile]):
    @abstractmethod
    def get_by_scholar_id(self, id: str) -> ResearcherProfile: pass

    @abstractmethod
    def get_by_orcid(self, id: str) -> ResearcherProfile: pass
