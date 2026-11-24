"""SQLAlchemy model registry used by the application and Alembic."""

from app.models.base import Base
from app.models.employee import Employee
from app.models.exchange_rate import ExchangeRate
from app.models.salary import Salary

__all__ = [
    "Base",
    "Employee",
    "ExchangeRate",
    "Salary",
]
