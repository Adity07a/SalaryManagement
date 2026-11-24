"""Unit tests for employee and salary request validation."""

from decimal import Decimal

import pytest
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.schemas.salary import SalaryCreate
from pydantic import ValidationError


def valid_employee_payload() -> dict:
    return {
        "full_name": "Alice Smith",
        "email": "alice@example.com",
        "job_title": "Software Engineer",
        "department": "Engineering",
        "country": "US",
        "employment_type": "full_time",
        "hire_date": "2024-01-15",
    }


def valid_salary_payload() -> dict:
    return {
        "amount": "75000.00",
        "currency": "USD",
        "effective_from": "2025-01-01",
    }


def test_employee_create_normalizes_text_fields() -> None:
    payload = valid_employee_payload()
    payload["full_name"] = "  Alice   Smith  "
    payload["email"] = " ALICE@EXAMPLE.COM "
    payload["country"] = "us"

    employee = EmployeeUpdate.model_validate(payload)

    assert employee.full_name == "Alice Smith"
    assert employee.email == "alice@example.com"
    assert employee.country == "US"


def test_employee_create_rejects_invalid_email() -> None:
    payload = valid_employee_payload()
    payload["email"] = "not-an-email"

    with pytest.raises(ValidationError):
        EmployeeUpdate.model_validate(payload)


def test_employee_create_rejects_invalid_country_code() -> None:
    payload = valid_employee_payload()
    payload["country"] = "ZZ"

    with pytest.raises(ValidationError):
        EmployeeUpdate.model_validate(payload)


def test_employee_create_rejects_blank_required_text() -> None:
    payload = valid_employee_payload()
    payload["full_name"] = "   "

    with pytest.raises(ValidationError):
        EmployeeUpdate.model_validate(payload)


def test_salary_create_normalizes_currency() -> None:
    payload = valid_salary_payload()
    payload["currency"] = " inr "

    salary = SalaryCreate.model_validate(payload)

    assert salary.currency == "INR"
    assert salary.amount == Decimal("75000.00")


@pytest.mark.parametrize(
    "amount",
    ["0", "-100.00"],
)
def test_salary_create_rejects_non_positive_amount(amount: str) -> None:
    payload = valid_salary_payload()
    payload["amount"] = amount

    with pytest.raises(ValidationError):
        SalaryCreate.model_validate(payload)


@pytest.mark.parametrize(
    "amount",
    ["100.001", "1234567890123.00"],
)
def test_salary_create_rejects_invalid_decimal_precision(
    amount: str,
) -> None:
    payload = valid_salary_payload()
    payload["amount"] = amount

    with pytest.raises(ValidationError):
        SalaryCreate.model_validate(payload)


@pytest.mark.parametrize(
    "currency",
    ["US", "US1", "123", "USDD"],
)
def test_salary_create_rejects_invalid_currency(currency: str) -> None:
    payload = valid_salary_payload()
    payload["currency"] = currency

    with pytest.raises(ValidationError):
        SalaryCreate.model_validate(payload)


def test_employee_create_requires_initial_salary() -> None:
    payload = valid_employee_payload()

    with pytest.raises(ValidationError):
        EmployeeCreate.model_validate(payload)


def test_employee_create_accepts_valid_initial_salary() -> None:
    payload = valid_employee_payload()
    payload["initial_salary"] = valid_salary_payload()

    employee = EmployeeCreate.model_validate(payload)

    assert employee.initial_salary.amount == Decimal("75000.00")
    assert employee.initial_salary.currency == "USD"
