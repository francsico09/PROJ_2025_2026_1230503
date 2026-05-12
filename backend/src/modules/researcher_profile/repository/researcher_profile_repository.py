from abc import abstractmethod, ABC

from src.core.repositories.general_repository import GeneralRepository
from src.core.domain.researcher_profile.researcher_profile_model.reasearcher_profile_model import \
    ResearcherProfile

class ResearcherProfileRepository(GeneralRepository[ResearcherProfile]):
    @abstractmethod
    def get_by_scholar_id(self, scholar_id: str) -> ResearcherProfile: pass

    @abstractmethod
    def get_by_orcid(self, orcid: str) -> ResearcherProfile: pass

    @abstractmethod
    def get_by_wos_id(self, wos_id: str) -> ResearcherProfile: pass

    @abstractmethod
    def get_by_scopus_id(self, scopus_id: str) -> ResearcherProfile: pass
