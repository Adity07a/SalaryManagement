"""Business services for employee management."""

from datetime import date
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictError,
    DomainValidationError,
    NotFoundError,
)
from app.models import Employee, Salary
from app.repositories.employee_repository import (
    add_employee as repository_add_employee,
)
from app.repositories.employee_repository import (
    add_salary_record,
    currency_exists,
    delete_employee_and_salaries,
    get_employee_by_email,
    get_employee_by_id,
    get_employee_directory_item,
    get_salary_by_effective_date,
    get_salary_response_data,
)
from app.repositories.employee_repository import (
    get_employee_detail as repository_get_employee_detail,
)
from app.repositories.employee_repository import (
    get_employee_filters as repository_get_employee_filters,
)
from app.repositories.employee_repository import (
    list_employees as repository_list_employees,
)
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.schemas.salary import SalaryCreate


def list_employees(
    session: Session,
    *,
    page: int,
    page_size: int,
    search: str | None,
    country: str | None,
    department: str | None,
    job_title: str | None,
    sort_by: str,
    sort_order: str,
) -> dict[str, Any]:
    """Return a paginated employee directory response."""

    items, total = repository_list_employees(
        session,
        page=page,
        page_size=page_size,
        search=search,
        country=country,
        department=department,
        job_title=job_title,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_employee_filters(
    session: Session,
) -> dict[str, list[str]]:
    """Return employee filter metadata."""

    return repository_get_employee_filters(session)


def _validate_hire_date(hire_date: date) -> None:
    """Prevent employees from having future hire dates."""

    if hire_date > date.today():
        raise DomainValidationError(
            "Hire date cannot be in the future.",
            {
                "field": "hire_date",
                "value": hire_date.isoformat(),
            },
        )


def _validate_salary_currency(
    session: Session,
    currency: str,
) -> None:
    """Ensure salary currency has a configured exchange rate."""

    if not currency_exists(session, currency):
        raise DomainValidationError(
            f"Currency '{currency}' is not supported.",
            {
                "field": "currency",
                "value": currency,
            },
        )


def _handle_integrity_error(
    session: Session,
) -> None:
    """Rollback and translate database conflicts into API errors."""

    session.rollback()

    raise ConflictError(
        "Employee could not be saved because a conflicting record exists."
    )


def _get_employee_response(
    session: Session,
    employee_id: int,
) -> dict[str, Any]:
    """Fetch the committed employee representation."""

    result = get_employee_directory_item(
        session,
        employee_id,
    )

    if result is None:
        raise NotFoundError("Employee", employee_id)

    return result


def create_employee(
    session: Session,
    payload: EmployeeCreate,
) -> dict[str, Any]:
    """Create an employee and their initial salary atomically."""

    employee_data = payload.model_dump(exclude={"initial_salary"})

    employee_data["email"] = str(payload.email).lower()

    _validate_hire_date(employee_data["hire_date"])

    salary_data = payload.initial_salary

    _validate_salary_currency(
        session,
        salary_data.currency,
    )

    existing_employee = get_employee_by_email(
        session,
        employee_data["email"],
    )

    if existing_employee is not None:
        raise ConflictError(
            "An employee with this email already exists.",
            {
                "field": "email",
                "value": employee_data["email"],
            },
        )

    employee = Employee(**employee_data)

    initial_salary = Salary(
        amount=salary_data.amount,
        currency=salary_data.currency,
        effective_from=salary_data.effective_from,
    )

    try:
        employee_id = repository_add_employee(
            session,
            employee,
            initial_salary,
        )

        session.commit()

    except IntegrityError:
        _handle_integrity_error(session)

    return _get_employee_response(
        session,
        employee_id,
    )


def update_employee(
    session: Session,
    employee_id: int,
    payload: EmployeeUpdate,
) -> dict[str, Any]:
    """Update employee information without modifying salary history."""

    employee = get_employee_by_id(
        session,
        employee_id,
    )

    if employee is None:
        raise NotFoundError("Employee", employee_id)

    employee_data = payload.model_dump()

    employee_data["email"] = str(payload.email).lower()

    _validate_hire_date(employee_data["hire_date"])

    existing_employee = get_employee_by_email(
        session,
        employee_data["email"],
        exclude_employee_id=employee_id,
    )

    if existing_employee is not None:
        raise ConflictError(
            "Another employee already uses this email.",
            {
                "field": "email",
                "value": employee_data["email"],
            },
        )

    # Salary data is intentionally not part of this operation.
    for field, value in employee_data.items():
        setattr(employee, field, value)

    try:
        session.commit()

    except IntegrityError:
        _handle_integrity_error(session)

    return _get_employee_response(
        session,
        employee_id,
    )


def delete_employee(
    session: Session,
    employee_id: int,
) -> None:
    """Physically delete an employee and dependent salary records."""

    employee = get_employee_by_id(
        session,
        employee_id,
    )

    if employee is None:
        raise NotFoundError("Employee", employee_id)

    try:
        delete_employee_and_salaries(
            session,
            employee,
        )

        session.commit()

    except IntegrityError:
        session.rollback()
        raise


def get_employee_detail(
    session: Session,
    employee_id: int,
) -> dict[str, Any]:
    """Return employee profile with complete salary history."""

    employee = repository_get_employee_detail(
        session,
        employee_id,
    )

    if employee is None:
        raise NotFoundError(
            "Employee",
            employee_id,
        )

    return employee


def add_employee_salary(
    session: Session,
    employee_id: int,
    payload: SalaryCreate,
) -> dict[str, Any]:
    """Append a salary record without modifying salary history."""

    employee = get_employee_by_id(
        session,
        employee_id,
    )

    if employee is None:
        raise NotFoundError(
            "Employee",
            employee_id,
        )

    # Salary must not become effective before employment begins.
    if payload.effective_from < employee.hire_date:
        raise DomainValidationError(
            "Salary effective date cannot be before employee hire date.",
            {
                "field": "effective_from",
                "hire_date": employee.hire_date.isoformat(),
                "effective_from": payload.effective_from.isoformat(),
            },
        )

    _validate_salary_currency(
        session,
        payload.currency,
    )

    # Prevent duplicate salary records for the same effective date.
    existing_salary = get_salary_by_effective_date(
        session,
        employee_id,
        payload.effective_from,
    )

    if existing_salary is not None:
        raise ConflictError(
            "A salary record already exists for this effective date.",
            {
                "employee_id": employee_id,
                "effective_from": payload.effective_from.isoformat(),
            },
        )

    salary = Salary(
        employee_id=employee_id,
        amount=payload.amount,
        currency=payload.currency,
        effective_from=payload.effective_from,
    )

    try:
        salary_id = add_salary_record(
            session,
            salary,
        )

        session.commit()

    except IntegrityError as err:
        session.rollback()

        raise ConflictError(
            "A salary record already exists for this effective date.",
            {
                "employee_id": employee_id,
                "effective_from": payload.effective_from.isoformat(),
            },
        ) from err

    result = get_salary_response_data(
        session,
        salary_id,
    )

    if result is None:
        raise RuntimeError("Saved salary record could not be retrieved.")

    return result
