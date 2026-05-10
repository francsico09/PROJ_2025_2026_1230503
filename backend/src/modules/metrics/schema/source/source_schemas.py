from enum import Enum

from pydantic import BaseModel


class SourceNameModel(str, Enum):
    scholar = 'scholar'
    orcid = 'orcid'
    wos = 'web_of_science'
    scopus = 'scopus'

    model_config = {"from_attributes": True}

class SourceModel(BaseModel):
    name: SourceNameModel
    url: str

    model_config = {"from_attributes": True}

