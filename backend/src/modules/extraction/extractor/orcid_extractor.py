import logging
from typing import Optional
import requests
from src.modules.normalization.models.result.normalization_result import RawOrcidProfile

from src.core.settings.settings import settings

logger = logging.getLogger(__name__)


class OrcidExtractor:

    BASE_URL = settings.ORCID_BASE_URL

    def extract_by_id(self, orcid_id: str) -> Optional[RawOrcidProfile]:
        return self._fetch_profile(orcid_id)

    def extract_by_name(self, name: str) -> Optional[RawOrcidProfile]:
        try:
            parts = name.strip().split()
            if not parts:
                return None
            query = f"family-name:{parts[-1]} AND given-names:{parts[0]}"
            data = self._search(query)
            records = data.get("result", [])
            if not records:
                return None
            orcid_id = records[0]["orcid-identifier"]["path"]
            return self._fetch_profile(orcid_id)
        except Exception as e:
            logger.error(f"[ORCID] Error searching by name '{name}': {e}")
            return None

    def extract_by_email(self, email: str) -> Optional[RawOrcidProfile]:
        try:
            data = self._search(f"email:{email}")
            records = data.get("result", [])
            if not records:
                return None
            orcid_id = records[0]["orcid-identifier"]["path"]
            return self._fetch_profile(orcid_id)
        except Exception as e:
            logger.error(f"[ORCID] Error searching by email '{email}': {e}")
            return None

    def _search(self, query: str) -> dict:
        response = requests.get(
            f"{self.BASE_URL}/search/",
            params={"q": query},
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        return response.json()

    def _fetch_profile(self, orcid_id: str) -> Optional[RawOrcidProfile]:
        try:
            response = requests.get(
                f"{self.BASE_URL}/{orcid_id}/record",
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            record = response.json()

            person = record.get("person", {})
            name_data = person.get("name", {})
            emails = person.get("emails", {}).get("email", [])
            keywords = person.get("keywords", {}).get("keyword", [])
            bio = person.get("biography", {})

            external_ids = person.get("external-identifiers", {}).get("external-identifier", [])
            scholar_id = self._extract_external_id(external_ids, "Google Scholar")
            wos_id     = self._extract_external_id(external_ids, "ResearcherID")
            scopus_id  = self._extract_external_id(external_ids, "Scopus Author ID")

            return RawOrcidProfile(
                orcid_id=orcid_id,
                given_name=name_data.get("given-names", {}).get("value", ""),
                family_name=name_data.get("family-name", {}).get("value", ""),
                email=emails[0].get("email") if emails else None,
                biography=bio.get("content") if bio else None,
                keywords=[kw.get("content", "") for kw in keywords],
                scholar_id=scholar_id,
                wos_id=wos_id,
                scopus_id=scopus_id,
            )

        except Exception as e:
            logger.error(f"[ORCID] Error fetching profile '{orcid_id}': {e}")
            return None

    @staticmethod
    def _extract_external_id(external_ids: list, id_type: str) -> Optional[str]:
        for ext in external_ids:
            if ext.get("external-id-type", "").lower() == id_type.lower():
                return ext.get("external-id-value")
        return None