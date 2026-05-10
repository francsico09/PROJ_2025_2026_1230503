from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # LDAP
    LDAP_HOST: str
    LDAP_PORT: int = 389
    LDAP_BASE_DN: str
    LDAP_ADMIN_DN: str
    LDAP_ADMIN_PASSWORD: str
    LDAP_PEOPLE_OU: str

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    # ORCID
    ORCID_CLIENT_ID: str = ""
    ORCID_CLIENT_SECRET: str = ""
    ORCID_BASE_URL: str = "https://pub.orcid.org/v3.0"

    # Scholar
    SCHOLAR_BASE_URL: str = "https://scholar.google.com/citations"

    # Scopus
    SCOPUS_API_KEY: str = "088005813931e5ba2c9585dd7fe5b56d"
    SCOPUS_BASE_URL: str = "https://api.elsevier.com/content"
    SCOPUS_INST_TOKEN: Optional[str] = None

    # WoS
    WOS_API_KEY: str = "1a004c4e2973e946c0758a0107e87162e296081f"
    WOS_BASE_URL: str = "https://api.clarivate.com/apis/wos-starter/v1"

    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()