"""Database queries for employee directory operations."""

from datetime import date
from typing import Any

from sqlalchemy import Numeric, Select, cast, delete, func, or_, select
from sqlalchemy.orm import Session

from app.models import Employee, ExchangeRate, Salary


def _escape_like_value(value: str) -> str:
    """Treat LIKE wildcard characters in user input literally."""

    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _current_salary_subquery() -> Any:
    """Select the latest salary record for every employee.

    When effective dates are equal, the higher salary ID wins.
    Conversion into USD happens in SQL using the exchange-rate table.
    """

    return (
        select(
            Salary.employee_id.label("employee_id"),
            Salary.id.label("salary_id"),
            Salary.amount.label("amount"),
            Salary.currency.label("currency"),
            Salary.effective_from.label("effective_from"),
            Salary.created_at.label("created_at"),
            cast(
                Salary.amount * ExchangeRate.rate_to_base,
                Numeric(24, 2),
            ).label("amount_usd"),
            func.row_number()
            .over(
                partition_by=Salary.employee_id,
                order_by=(
                    Salary.effective_from.desc(),
                    Salary.id.desc(),
                ),
            )
            .label("row_number"),
        )
        .join(
            ExchangeRate,
            ExchangeRate.currency == Salary.currency,
        )
        .subquery("ranked_current_salaries")
    )


def _employee_filters(
    statement: Select[Any],
    *,
    search: str | None,
    country: str | None,
    department: str | None,
    job_title: str | None,
) -> Select[Any]:
    """Apply employee search and filtering conditions."""

    if search:
        pattern = f"%{_escape_like_value(search.strip())}%"

        statement = statement.where(
            or_(
                Employee.full_name.ilike(
                    pattern,
                    escape="\\",
                ),
                Employee.email.ilike(
                    pattern,
                    escape="\\",
                ),
            )
        )

    if country:
        statement = statement.where(Employee.country == country.upper())

    if department:
        statement = statement.where(Employee.department == department)

    if job_title:
        statement = statement.where(Employee.job_title == job_title)

    return statement


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
) -> tuple[list[dict[str, Any]], int]:
    """Fetch employees using database-side filtering and pagination."""

    filters = {
        "search": search,
        "country": country,
        "department": department,
        "job_title": job_title,
    }

    # Count matching employees separately from the paginated query.
    count_statement = _employee_filters(
        select(func.count(Employee.id)),
        **filters,
    )

    total = int(session.scalar(count_statement) or 0)

    current_salary = _current_salary_subquery()

    # LEFT JOIN ensures employees without salary history
    # can still appear in the employee directory.
    statement = select(
        Employee,
        current_salary.c.salary_id,
        current_salary.c.amount,
        current_salary.c.currency,
        current_salary.c.effective_from,
        current_salary.c.amount_usd,
        current_salary.c.created_at,
    ).outerjoin(
        current_salary,
        (current_salary.c.employee_id == Employee.id)
        & (current_salary.c.row_number == 1),
    )

    statement = _employee_filters(
        statement,
        **filters,
    )

    # Explicit whitelist prevents arbitrary column selection.
    sortable_columns = {
        "full_name": Employee.full_name,
        "email": Employee.email,
        "job_title": Employee.job_title,
        "department": Employee.department,
        "country": Employee.country,
        "employment_type": Employee.employment_type,
        "hire_date": Employee.hire_date,
        "created_at": Employee.created_at,
        "updated_at": Employee.updated_at,
        "current_salary": current_salary.c.amount_usd,
    }

    sort_column = sortable_columns[sort_by]

    if sort_order == "desc":
        ordering = sort_column.desc().nulls_last()
    else:
        ordering = sort_column.asc().nulls_last()

    # Employee ID provides deterministic ordering when values tie.
    statement = (
        statement.order_by(
            ordering,
            Employee.id.asc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    rows = session.execute(statement).all()

    items: list[dict[str, Any]] = []

    for row in rows:
        employee = row[0]

        (
            salary_id,
            amount,
            currency,
            effective_from,
            amount_usd,
            salary_created_at,
        ) = row[1:]

        current_salary_data = None

        if salary_id is not None:
            current_salary_data = {
                "id": salary_id,
                "amount": amount,
                "currency": currency,
                "effective_from": effective_from,
                "amount_usd": amount_usd,
                "created_at": salary_created_at,
            }

        items.append(
            {
                "id": employee.id,
                "full_name": employee.full_name,
                "email": employee.email,
                "job_title": employee.job_title,
                "department": employee.department,
                "country": employee.country,
                "employment_type": employee.employment_type,
                "hire_date": employee.hire_date,
                "created_at": employee.created_at,
                "updated_at": employee.updated_at,
                "current_salary": current_salary_data,
            }
        )

    return items, total


def get_employee_filters(
    session: Session,
) -> dict[str, list[str]]:
    """Return sorted distinct values for employee filters."""

    countries = session.scalars(
        select(Employee.country).distinct().order_by(Employee.country)
    ).all()

    departments = session.scalars(
        select(Employee.department).distinct().order_by(Employee.department)
    ).all()

    job_titles = session.scalars(
        select(Employee.job_title).distinct().order_by(Employee.job_title)
    ).all()

    return {
        "countries": list(countries),
        "departments": list(departments),
        "job_titles": list(job_titles),
    }


def get_employee_by_id(
    session: Session,
    employee_id: int,
) -> Employee | None:
    """Retrieve an employee by primary key."""

    return session.get(Employee, employee_id)


def get_employee_by_email(
    session: Session,
    email: str,
    *,
    exclude_employee_id: int | None = None,
) -> Employee | None:
    """Find an employee using their unique email address."""

    statement = select(Employee).where(Employee.email == email)

    if exclude_employee_id is not None:
        statement = statement.where(Employee.id != exclude_employee_id)

    return session.scalar(statement)


def currency_exists(
    session: Session,
    currency: str,
) -> bool:
    """Check whether a currency is configured in the database."""

    return session.get(ExchangeRate, currency) is not None


def add_employee(
    session: Session,
    employee: Employee,
    initial_salary: Salary,
) -> int:
    """Insert an employee and their initial salary in one transaction."""

    session.add(employee)
    session.flush()

    initial_salary.employee_id = employee.id

    session.add(initial_salary)
    session.flush()

    return employee.id


def delete_employee_and_salaries(
    session: Session,
    employee: Employee,
) -> None:
    """Delete the employee and their dependent salary records.

    The caller is responsible for committing the transaction.
    """

    session.execute(delete(Salary).where(Salary.employee_id == employee.id))

    session.delete(employee)
    session.flush()


def get_employee_directory_item(
    session: Session,
    employee_id: int,
) -> dict[str, Any] | None:
    """Fetch one employee using the same current-salary logic as the list API."""

    current_salary = _current_salary_subquery()

    statement = (
        select(
            Employee,
            current_salary.c.salary_id,
            current_salary.c.amount,
            current_salary.c.currency,
            current_salary.c.effective_from,
            current_salary.c.amount_usd,
            current_salary.c.created_at,
        )
        .outerjoin(
            current_salary,
            (current_salary.c.employee_id == Employee.id)
            & (current_salary.c.row_number == 1),
        )
        .where(Employee.id == employee_id)
    )

    row = session.execute(statement).first()

    if row is None:
        return None

    employee = row[0]

    (
        salary_id,
        amount,
        currency,
        effective_from,
        amount_usd,
        salary_created_at,
    ) = row[1:]

    salary_data = None

    if salary_id is not None:
        salary_data = {
            "id": salary_id,
            "amount": amount,
            "currency": currency,
            "effective_from": effective_from,
            "amount_usd": amount_usd,
            "created_at": salary_created_at,
        }

    return {
        "id": employee.id,
        "full_name": employee.full_name,
        "email": employee.email,
        "job_title": employee.job_title,
        "department": employee.department,
        "country": employee.country,
        "employment_type": employee.employment_type,
        "hire_date": employee.hire_date,
        "created_at": employee.created_at,
        "updated_at": employee.updated_at,
        "current_salary": salary_data,
    }


def get_employee_salary_history(
    session: Session,
    employee_id: int,
) -> list[dict[str, Any]]:
    """Fetch salary history ordered by newest effective date first."""

    statement = (
        select(
            Salary.id,
            Salary.employee_id,
            Salary.amount,
            Salary.currency,
            Salary.effective_from,
            cast(
                Salary.amount * ExchangeRate.rate_to_base,
                Numeric(24, 2),
            ).label("amount_usd"),
            Salary.created_at,
        )
        .join(
            ExchangeRate,
            ExchangeRate.currency == Salary.currency,
        )
        .where(Salary.employee_id == employee_id)
        .order_by(
            Salary.effective_from.desc(),
            Salary.id.desc(),
        )
    )

    rows = session.execute(statement).all()

    return [
        {
            "id": row.id,
            "employee_id": row.employee_id,
            "amount": row.amount,
            "currency": row.currency,
            "effective_from": row.effective_from,
            "amount_usd": row.amount_usd,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def get_employee_detail(
    session: Session,
    employee_id: int,
) -> dict[str, Any] | None:
    """Retrieve employee profile and complete salary history."""

    employee_data = get_employee_directory_item(
        session,
        employee_id,
    )

    if employee_data is None:
        return None

    employee_data["salary_history"] = get_employee_salary_history(
        session,
        employee_id,
    )

    return employee_data


def get_salary_by_effective_date(
    session: Session,
    employee_id: int,
    effective_from: date,
) -> Salary | None:
    """Find a salary record for an employee and effective date."""

    statement = select(Salary).where(
        Salary.employee_id == employee_id,
        Salary.effective_from == effective_from,
    )

    return session.scalar(statement)


def add_salary_record(
    session: Session,
    salary: Salary,
) -> int:
    """Persist an additional salary history record."""

    session.add(salary)

    session.flush()

    return salary.id


def get_salary_response_data(
    session: Session,
    salary_id: int,
) -> dict[str, Any] | None:
    """Retrieve a saved salary record and its USD equivalent."""

    statement = (
        select(
            Salary.id,
            Salary.employee_id,
            Salary.amount,
            Salary.currency,
            Salary.effective_from,
            cast(
                Salary.amount * ExchangeRate.rate_to_base,
                Numeric(24, 2),
            ).label("amount_usd"),
            Salary.created_at,
        )
        .join(
            ExchangeRate,
            ExchangeRate.currency == Salary.currency,
        )
        .where(Salary.id == salary_id)
    )

    row = session.execute(statement).first()

    if row is None:
        return None

    return {
        "id": row.id,
        "employee_id": row.employee_id,
        "amount": row.amount,
        "currency": row.currency,
        "effective_from": row.effective_from,
        "amount_usd": row.amount_usd,
        "created_at": row.created_at,
    }
