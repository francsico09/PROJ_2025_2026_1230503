import uuid
from dataclasses import field
from typing import Optional
from pydantic.dataclasses import dataclass


@dataclass
class NormalizedProfile:
    researcher_id: uuid.UUID
    biography: Optional[str] = None
    keywords: list[str] = field(default_factory=list)
    orcid_id: Optional[str] = None
    scholar_id: Optional[str] = None
    wos_id: Optional[str] = None
    scopus_id: Optional[str] = None