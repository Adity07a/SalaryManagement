"""Employee management API endpoints."""

from typing import Annotated, Literal

from fastapi import (
    APIRouter,
    Depends,
    Path,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeDetailResponse,
    EmployeeListItem,
    EmployeeUpdate,
)
from app.schemas.salary import SalaryCreate, SalaryResponse
from app.services.employee_service import (
    add_employee_salary as service_add_employee_salary,
)
from app.services.employee_service import (
    create_employee as service_create_employee,
)
from app.services.employee_service import (
    delete_employee as service_delete_employee,
)
from app.services.employee_service import (
    get_employee_detail as service_get_employee_detail,
)
from app.services.employee_service import (
    list_employees as service_list_employees,
)
from app.services.employee_service import (
    update_employee as service_update_employee,
)

router = APIRouter(
    prefix="/employees",
    tags=["employees"],
)

SortColumn = Literal[
    "full_name",
    "email",
    "job_title",
    "department",
    "country",
    "employment_type",
    "hire_date",
    "created_at",
    "updated_at",
    "current_salary",
]

SortOrder = Literal["asc", "desc"]


@router.get(
    "",
    response_model=PaginatedResponse[EmployeeListItem],
)
def get_employees(
    session: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    search: Annotated[str | None, Query(max_length=100)] = None,
    country: Annotated[
        str | None,
        Query(
            min_length=2,
            max_length=2,
            pattern=r"^[A-Za-z]{2}$",
        ),
    ] = None,
    department: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
    job_title: Annotated[
        str | None,
        Query(min_length=1, max_length=120),
    ] = None,
    sort_by: SortColumn = "full_name",
    sort_order: SortOrder = "asc",
) -> dict[str, object]:
    """Search, filter, sort and paginate employees."""

    return service_list_employees(
        session,
        page=page,
        page_size=page_size,
        search=search,
        country=country.upper() if country else None,
        department=department,
        job_title=job_title,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post(
    "",
    response_model=EmployeeListItem,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    payload: EmployeeCreate,
    session: Annotated[Session, Depends(get_db)],
) -> dict:
    """Create an employee together with their initial salary."""

    return service_create_employee(
        session,
        payload,
    )


@router.put(
    "/{employee_id}",
    response_model=EmployeeListItem,
)
def update_employee(
    employee_id: Annotated[int, Path(gt=0)],
    payload: EmployeeUpdate,
    session: Annotated[Session, Depends(get_db)],
) -> dict:
    """Update employee profile information."""

    return service_update_employee(
        session,
        employee_id,
        payload,
    )


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_employee(
    employee_id: Annotated[int, Path(gt=0)],
    session: Annotated[Session, Depends(get_db)],
) -> Response:
    """Delete an employee and their associated salary records."""

    service_delete_employee(
        session,
        employee_id,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{employee_id}",
    response_model=EmployeeDetailResponse,
)
def get_employee_detail(
    employee_id: Annotated[int, Path(gt=0)],
    session: Annotated[Session, Depends(get_db)],
) -> dict:
    """Retrieve employee profile and complete salary history."""

    return service_get_employee_detail(
        session,
        employee_id,
    )


@router.post(
    "/{employee_id}/salary",
    response_model=SalaryResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_employee_salary(
    employee_id: Annotated[int, Path(gt=0)],
    payload: SalaryCreate,
    session: Annotated[Session, Depends(get_db)],
) -> dict:
    """Add a new salary history record."""

    return service_add_employee_salary(
        session,
        employee_id,
        payload,
    )
