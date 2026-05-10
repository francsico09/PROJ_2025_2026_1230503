from dataclasses import dataclass
from enum import Enum

class SourceName(str, Enum):
    scholar = 'scholar'
    orcid = 'orcid'
    wos = 'web_of_science'
    scopus = 'scopus'

@dataclass
class Source:
    name: SourceName
    url: str
