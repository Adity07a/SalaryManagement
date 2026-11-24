from app.models import Employee, ExchangeRate, Salary
from sqlalchemy import Numeric


def test_employee_model_has_required_filter_indexes() -> None:
    index_names = {index.name for index in Employee.__table__.indexes}

    assert index_names == {
        "ix_employees_country",
        "ix_employees_department",
        "ix_employees_job_title",
    }
    assert any(
        constraint.name == "uq_employees_email"
        for constraint in Employee.__table__.constraints
    )


def test_salary_model_uses_decimal_money_and_history_index() -> None:
    amount_type = Salary.__table__.c.amount.type
    assert isinstance(amount_type, Numeric)
    assert amount_type.precision == 14
    assert amount_type.scale == 2

    index_names = {index.name for index in Salary.__table__.indexes}
    assert "ix_salaries_employee_effective_from" in index_names
    assert any(
        constraint.name == "uq_salaries_employee_id_effective_from"
        for constraint in Salary.__table__.constraints
    )
    assert any(
        constraint.name == "ck_salaries_amount_positive"
        for constraint in Salary.__table__.constraints
    )


def test_exchange_rate_model_uses_decimal_conversion_rate() -> None:
    rate_type = ExchangeRate.__table__.c.rate_to_base.type

    assert isinstance(rate_type, Numeric)
    assert rate_type.precision == 18
    assert rate_type.scale == 8
