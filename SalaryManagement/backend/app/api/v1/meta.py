"""Metadata endpoints for frontend filter dropdowns."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.employee import MetaFiltersResponse
from app.services.employee_service import get_employee_filters

router = APIRouter(
    prefix="/meta",
    tags=["metadata"],
)


@router.get(
    "/filters",
    response_model=MetaFiltersResponse,
)
def get_filters(
    session: Annotated[Session, Depends(get_db)],
) -> dict[str, list[str]]:
    """Return distinct countries, departments and job titles."""

    return get_employee_filters(session)
