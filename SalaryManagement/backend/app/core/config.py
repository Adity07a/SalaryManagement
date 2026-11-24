from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> repository's SalaryManagement directory.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Application settings loaded from environment variables or the root .env file."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "ACME Salary Management API"
    debug: bool = False
    # repr=False prevents accidental disclosure when settings are logged or inspected.
    database_url: str = Field(
        default=(
            "postgresql+psycopg://salary_management_user:local_dev_password"
            "@localhost:5432/salary_management_db"
        ),
        repr=False,
    )


settings = Settings()
