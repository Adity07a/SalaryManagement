"""Behavioral tests for employee directory APIs."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from app.models import Employee, ExchangeRate, Salary
from sqlalchemy import func, select
from sqlalchemy.orm import Session


@pytest.fixture
def sample_employees(db_session: Session) -> None:
    """Insert a small deterministic dataset."""

    db_session.add_all(
        [
            ExchangeRate(
                currency="USD",
                rate_to_base=Decimal("1.00000000"),
            ),
            ExchangeRate(
                currency="INR",
                rate_to_base=Decimal("0.01200000"),
            ),
            ExchangeRate(
                currency="GBP",
                rate_to_base=Decimal("1.27000000"),
            ),
        ]
    )

    db_session.flush()

    alice = Employee(
        full_name="Alice Smith",
        email="alice.smith@example.com",
        job_title="Senior Software Engineer",
        department="Engineering",
        country="US",
        employment_type="full_time",
        hire_date=date(2020, 1, 10),
    )

    bob = Employee(
        full_name="Bob Jones",
        email="bob.jones@example.com",
        job_title="Financial Analyst",
        department="Finance",
        country="IN",
        employment_type="full_time",
        hire_date=date(2021, 2, 15),
    )

    carol = Employee(
        full_name="Carol White",
        email="carol.white@example.com",
        job_title="Software Engineer II",
        department="Engineering",
        country="US",
        employment_type="contract",
        hire_date=date(2022, 3, 20),
    )

    david = Employee(
        full_name="David King",
        email="david.king@example.com",
        job_title="Account Executive",
        department="Sales",
        country="GB",
        employment_type="full_time",
        hire_date=date(2019, 4, 25),
    )

    db_session.add_all([alice, bob, carol, david])
    db_session.flush()

    db_session.add_all(
        [
            # Alice's previous salary.
            Salary(
                employee_id=alice.id,
                amount=Decimal("100000.00"),
                currency="USD",
                effective_from=date(2024, 1, 1),
            ),
            # Alice's latest salary.
            Salary(
                employee_id=alice.id,
                amount=Decimal("120000.00"),
                currency="USD",
                effective_from=date(2025, 1, 1),
            ),
            Salary(
                employee_id=bob.id,
                amount=Decimal("5000000.00"),
                currency="INR",
                effective_from=date(2025, 1, 1),
            ),
            Salary(
                employee_id=carol.id,
                amount=Decimal("90000.00"),
                currency="USD",
                effective_from=date(2025, 1, 1),
            ),
            Salary(
                employee_id=david.id,
                amount=Decimal("70000.00"),
                currency="GBP",
                effective_from=date(2025, 1, 1),
            ),
        ]
    )

    db_session.commit()


def test_employee_list_returns_paginated_items_and_current_salary(
    client,
    sample_employees,
) -> None:
    response = client.get("/api/v1/employees?page=1&page_size=10")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 4
    assert payload["page"] == 1
    assert payload["page_size"] == 10
    assert len(payload["items"]) == 4

    alice = next(
        item for item in payload["items"] if item["email"] == "alice.smith@example.com"
    )

    assert Decimal(alice["current_salary"]["amount"]) == Decimal("120000.00")

    assert alice["current_salary"]["currency"] == "USD"

    assert Decimal(alice["current_salary"]["amount_usd"]) == Decimal("120000.00")

    assert alice["current_salary"]["effective_from"] == "2025-01-01"


def test_employee_search_matches_name_or_email(
    client,
    sample_employees,
) -> None:
    name_response = client.get("/api/v1/employees?search=alice")

    email_response = client.get("/api/v1/employees?search=example.com")

    assert name_response.status_code == 200
    assert name_response.json()["total"] == 1
    assert name_response.json()["items"][0]["full_name"] == "Alice Smith"

    assert email_response.status_code == 200
    assert email_response.json()["total"] == 4


def test_employee_filters_can_be_combined(
    client,
    sample_employees,
) -> None:
    response = client.get(
        "/api/v1/employees",
        params={
            "country": "us",
            "department": "Engineering",
            "job_title": "Senior Software Engineer",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 1
    assert payload["items"][0]["email"] == "alice.smith@example.com"


def test_employee_pagination_is_stable_and_reports_total(
    client,
    sample_employees,
) -> None:
    response = client.get(
        "/api/v1/employees",
        params={
            "page": 2,
            "page_size": 2,
            "sort_by": "full_name",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["total"] == 4
    assert payload["page"] == 2
    assert payload["page_size"] == 2

    assert [item["full_name"] for item in payload["items"]] == [
        "Carol White",
        "David King",
    ]


def test_employee_sorting_supports_descending_order(
    client,
    sample_employees,
) -> None:
    response = client.get(
        "/api/v1/employees",
        params={
            "sort_by": "full_name",
            "sort_order": "desc",
        },
    )

    assert response.status_code == 200

    assert [item["full_name"] for item in response.json()["items"]] == [
        "David King",
        "Carol White",
        "Bob Jones",
        "Alice Smith",
    ]


def test_employee_list_rejects_invalid_pagination(
    client,
    sample_employees,
) -> None:
    response = client.get("/api/v1/employees?page=0")

    assert response.status_code == 422

    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    assert response.json()["error"]["message"] == "Request validation failed."


def test_employee_list_rejects_unknown_sort_column(
    client,
    sample_employees,
) -> None:
    response = client.get("/api/v1/employees?sort_by=salary_password")

    assert response.status_code == 422

    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_meta_filters_return_sorted_distinct_values(
    client,
    sample_employees,
) -> None:
    response = client.get("/api/v1/meta/filters")

    assert response.status_code == 200

    assert response.json() == {
        "countries": ["GB", "IN", "US"],
        "departments": [
            "Engineering",
            "Finance",
            "Sales",
        ],
        "job_titles": [
            "Account Executive",
            "Financial Analyst",
            "Senior Software Engineer",
            "Software Engineer II",
        ],
    }


def _valid_employee_payload(
    email: str = "new.employee@example.com",
) -> dict:
    """Build a valid employee creation request."""

    return {
        "full_name": "New Employee",
        "email": email,
        "job_title": "Software Engineer I",
        "department": "Engineering",
        "country": "US",
        "employment_type": "full_time",
        "hire_date": "2024-01-15",
        "initial_salary": {
            "amount": "75000.00",
            "currency": "USD",
            "effective_from": "2025-01-01",
        },
    }


def test_create_employee_with_initial_salary(
    client,
    sample_employees,
) -> None:
    response = client.post(
        "/api/v1/employees",
        json=_valid_employee_payload(),
    )

    assert response.status_code == 201

    employee = response.json()

    assert employee["full_name"] == "New Employee"
    assert employee["email"] == "new.employee@example.com"
    assert employee["country"] == "US"

    assert employee["current_salary"]["currency"] == "USD"
    assert employee["current_salary"]["amount"] == "75000.00"
    assert employee["current_salary"]["amount_usd"] == "75000.00"


def test_create_employee_rejects_duplicate_email(
    client,
    sample_employees,
) -> None:
    response = client.post(
        "/api/v1/employees",
        json=_valid_employee_payload("alice.smith@example.com"),
    )

    assert response.status_code == 409

    assert response.json()["error"]["code"] == "RESOURCE_CONFLICT"


def test_create_employee_rejects_unsupported_currency(
    client,
    sample_employees,
) -> None:
    payload = _valid_employee_payload()
    payload["initial_salary"]["currency"] = "EUR"

    response = client.post(
        "/api/v1/employees",
        json=payload,
    )

    assert response.status_code == 422

    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_employee_rejects_invalid_country(
    client,
    sample_employees,
) -> None:
    payload = _valid_employee_payload()
    payload["country"] = "ZZ"

    response = client.post(
        "/api/v1/employees",
        json=payload,
    )

    assert response.status_code == 422


def test_create_employee_rejects_future_hire_date(
    client,
    sample_employees,
) -> None:
    payload = _valid_employee_payload()

    payload["hire_date"] = (date.today() + timedelta(days=1)).isoformat()

    response = client.post(
        "/api/v1/employees",
        json=payload,
    )

    assert response.status_code == 422

    assert response.json()["error"]["details"]["field"] == "hire_date"


def test_create_employee_rejects_zero_salary(
    client,
    sample_employees,
) -> None:
    payload = _valid_employee_payload()
    payload["initial_salary"]["amount"] = "0.00"

    response = client.post(
        "/api/v1/employees",
        json=payload,
    )

    assert response.status_code == 422


def test_update_employee_changes_profile_without_changing_salary(
    client,
    sample_employees,
) -> None:
    list_response = client.get("/api/v1/employees?search=alice.smith@example.com")

    employee = list_response.json()["items"][0]

    original_salary = employee["current_salary"]

    employee_id = employee["id"]

    payload = {
        "full_name": "Alice Smith Updated",
        "email": "alice.updated@example.com",
        "job_title": "Engineering Manager",
        "department": "Engineering",
        "country": "US",
        "employment_type": "full_time",
        "hire_date": "2020-01-10",
    }

    response = client.put(
        f"/api/v1/employees/{employee_id}",
        json=payload,
    )

    assert response.status_code == 200

    updated = response.json()

    assert updated["full_name"] == "Alice Smith Updated"
    assert updated["email"] == "alice.updated@example.com"
    assert updated["job_title"] == "Engineering Manager"

    assert updated["current_salary"] == original_salary


def test_update_employee_returns_404_for_missing_employee(
    client,
) -> None:
    payload = {
        "full_name": "Unknown Employee",
        "email": "unknown@example.com",
        "job_title": "Developer",
        "department": "Engineering",
        "country": "US",
        "employment_type": "full_time",
        "hire_date": "2024-01-01",
    }

    response = client.put(
        "/api/v1/employees/999999",
        json=payload,
    )

    assert response.status_code == 404

    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_update_employee_rejects_duplicate_email(
    client,
    sample_employees,
) -> None:
    bob_response = client.get("/api/v1/employees?search=bob.jones")

    bob = bob_response.json()["items"][0]

    payload = {
        "full_name": "Bob Jones",
        "email": "alice.smith@example.com",
        "job_title": "Financial Analyst",
        "department": "Finance",
        "country": "IN",
        "employment_type": "full_time",
        "hire_date": "2021-02-15",
    }

    response = client.put(
        f"/api/v1/employees/{bob['id']}",
        json=payload,
    )

    assert response.status_code == 409


def test_delete_employee_removes_employee_and_salary_history(
    client,
    db_session,
    sample_employees,
) -> None:
    employee = db_session.scalar(
        select(Employee).where(Employee.email == "alice.smith@example.com")
    )

    assert employee is not None

    employee_id = employee.id

    response = client.delete(f"/api/v1/employees/{employee_id}")

    assert response.status_code == 204
    assert response.content == b""

    deleted_employee = db_session.get(
        Employee,
        employee_id,
    )

    assert deleted_employee is None

    remaining_salary_count = db_session.scalar(
        select(func.count(Salary.id)).where(Salary.employee_id == employee_id)
    )

    assert remaining_salary_count == 0


def test_delete_employee_returns_404_for_missing_employee(
    client,
) -> None:
    response = client.delete("/api/v1/employees/999999")

    assert response.status_code == 404

    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_employee_detail_returns_complete_salary_history(
    client,
    sample_employees,
) -> None:
    response = client.get("/api/v1/employees?search=alice.smith@example.com")

    employee_id = response.json()["items"][0]["id"]

    detail_response = client.get(f"/api/v1/employees/{employee_id}")

    assert detail_response.status_code == 200

    employee = detail_response.json()

    assert employee["full_name"] == "Alice Smith"

    assert len(employee["salary_history"]) == 2

    assert [salary["effective_from"] for salary in employee["salary_history"]] == [
        "2025-01-01",
        "2024-01-01",
    ]

    assert employee["current_salary"]["amount"] == "120000.00"


def test_employee_detail_returns_404_for_missing_employee(
    client,
) -> None:
    response = client.get("/api/v1/employees/999999")

    assert response.status_code == 404

    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_add_salary_appends_history_and_updates_current_salary(
    client,
    sample_employees,
) -> None:
    employee_response = client.get("/api/v1/employees?search=alice.smith@example.com")

    employee_id = employee_response.json()["items"][0]["id"]

    payload = {
        "amount": "12000000.00",
        "currency": "INR",
        "effective_from": "2026-01-01",
    }

    response = client.post(
        f"/api/v1/employees/{employee_id}/salary",
        json=payload,
    )

    assert response.status_code == 201

    salary = response.json()

    assert salary["amount"] == "12000000.00"
    assert salary["currency"] == "INR"
    assert salary["amount_usd"] == "144000.00"

    detail = client.get(f"/api/v1/employees/{employee_id}").json()

    assert len(detail["salary_history"]) == 3

    assert detail["salary_history"][0]["effective_from"] == "2026-01-01"

    assert detail["current_salary"]["amount"] == "12000000.00"
    assert detail["current_salary"]["currency"] == "INR"
    assert detail["current_salary"]["amount_usd"] == "144000.00"


def test_backdated_salary_is_appended_without_changing_current_salary(
    client,
    sample_employees,
) -> None:
    employee_response = client.get("/api/v1/employees?search=alice.smith@example.com")

    employee_id = employee_response.json()["items"][0]["id"]

    response = client.post(
        f"/api/v1/employees/{employee_id}/salary",
        json={
            "amount": "110000.00",
            "currency": "USD",
            "effective_from": "2024-06-01",
        },
    )

    assert response.status_code == 201

    detail = client.get(f"/api/v1/employees/{employee_id}").json()

    assert len(detail["salary_history"]) == 3

    assert detail["salary_history"][0]["effective_from"] == "2025-01-01"

    assert detail["current_salary"]["effective_from"] == "2025-01-01"
    assert detail["current_salary"]["amount"] == "120000.00"


def test_add_salary_rejects_duplicate_effective_date(
    client,
    sample_employees,
) -> None:
    employee_response = client.get("/api/v1/employees?search=alice.smith@example.com")

    employee_id = employee_response.json()["items"][0]["id"]

    response = client.post(
        f"/api/v1/employees/{employee_id}/salary",
        json={
            "amount": "130000.00",
            "currency": "USD",
            "effective_from": "2025-01-01",
        },
    )

    assert response.status_code == 409

    assert response.json()["error"]["code"] == "RESOURCE_CONFLICT"


def test_add_salary_rejects_date_before_employee_hire_date(
    client,
    sample_employees,
) -> None:
    employee_response = client.get("/api/v1/employees?search=bob.jones@example.com")

    employee_id = employee_response.json()["items"][0]["id"]

    response = client.post(
        f"/api/v1/employees/{employee_id}/salary",
        json={
            "amount": "8000000.00",
            "currency": "INR",
            "effective_from": "2019-01-01",
        },
    )

    assert response.status_code == 422

    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_add_salary_rejects_unsupported_currency(
    client,
    sample_employees,
) -> None:
    employee_response = client.get("/api/v1/employees?search=alice.smith@example.com")

    employee_id = employee_response.json()["items"][0]["id"]

    response = client.post(
        f"/api/v1/employees/{employee_id}/salary",
        json={
            "amount": "100000.00",
            "currency": "EUR",
            "effective_from": "2026-01-01",
        },
    )

    assert response.status_code == 422


def test_add_salary_returns_404_for_missing_employee(
    client,
) -> None:
    response = client.post(
        "/api/v1/employees/999999/salary",
        json={
            "amount": "100000.00",
            "currency": "USD",
            "effective_from": "2026-01-01",
        },
    )

    assert response.status_code == 404

    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_add_salary_rejects_zero_amount(
    client,
    sample_employees,
) -> None:
    employee_response = client.get("/api/v1/employees?search=alice.smith@example.com")

    employee_id = employee_response.json()["items"][0]["id"]

    response = client.post(
        f"/api/v1/employees/{employee_id}/salary",
        json={
            "amount": "0.00",
            "currency": "USD",
            "effective_from": "2026-01-01",
        },
    )

    assert response.status_code == 422
