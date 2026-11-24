"""Employee request and response schemas."""

from datetime import date, datetime
from decimal import Decimal

import pycountry
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)

from app.schemas.salary import InitialSalaryCreate, SalaryResponse

# =====================================================
# EMPLOYEE REQUEST SCHEMAS
# =====================================================


class EmployeeFields(BaseModel):
    """Shared employee fields for creation and updates."""

    full_name: str = Field(min_length=2, max_length=150)

    email: EmailStr

    job_title: str = Field(min_length=2, max_length=120)

    department: str = Field(min_length=2, max_length=100)

    country: str = Field(min_length=2, max_length=2)

    employment_type: str = Field(min_length=1, max_length=30)

    hire_date: date

    @field_validator(
        "full_name",
        "job_title",
        "department",
        "employment_type",
    )
    @classmethod
    def normalize_text(cls, value: str) -> str:
        """Normalize whitespace in text fields."""

        normalized = " ".join(value.split())

        if not normalized:
            raise ValueError("This field cannot be empty.")

        return normalized

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        """Validate ISO-3166 alpha-2 country codes."""

        country = value.strip().upper()

        if pycountry.countries.get(alpha_2=country) is None:
            raise ValueError("Country must be a valid ISO-3166 alpha-2 code.")

        return country

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        """Normalize email addresses."""

        return str(value).strip().lower()


class EmployeeCreate(EmployeeFields):
    """Employee creation request with initial salary."""

    initial_salary: InitialSalaryCreate


class EmployeeUpdate(EmployeeFields):
    """Employee profile update request.

    Salary changes must use the dedicated salary endpoint.
    """


# =====================================================
# EMPLOYEE RESPONSE SCHEMAS
# =====================================================


class CurrentSalaryResponse(BaseModel):
    """Current salary in local currency and USD."""

    id: int

    amount: Decimal

    currency: str

    effective_from: date

    amount_usd: Decimal

    created_at: datetime


class EmployeeListItem(BaseModel):
    """Employee record returned by the employee API."""

    id: int

    full_name: str

    email: str

    job_title: str

    department: str

    country: str

    employment_type: str

    hire_date: date

    created_at: datetime

    updated_at: datetime

    current_salary: CurrentSalaryResponse | None = None


class MetaFiltersResponse(BaseModel):
    """Distinct values for employee filter dropdowns."""

    countries: list[str]

    departments: list[str]

    job_titles: list[str]


class EmployeeDetailResponse(EmployeeListItem):
    """Employee profile with complete salary history."""

    salary_history: list[SalaryResponse] = Field(default_factory=list)
