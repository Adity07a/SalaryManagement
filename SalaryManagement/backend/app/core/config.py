
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root: acme-salary-management/
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """
    Central application configuration.

    Values are loaded from environment variables first,
    followed by the project's root .env file.
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ACME Salary Management API"

    debug: bool = False

    database_url: str = (
        "postgresql+psycopg://acme:local_dev_password"
        "@localhost:5432/acme_salary"
    )


settings = Settings()
