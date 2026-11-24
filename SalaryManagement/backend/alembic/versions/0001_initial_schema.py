"""Create the initial employee, exchange-rate, and salary schema."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("job_title", sa.String(length=120), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("employment_type", sa.String(length=32), nullable=False),
        sa.Column("hire_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(country) = 2",
            name="ck_employees_country_iso2_length",
        ),
        sa.CheckConstraint(
            "country = upper(country)",
            name="ck_employees_country_uppercase",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_employees"),
        sa.UniqueConstraint("email", name="uq_employees_email"),
    )
    op.create_index("ix_employees_country", "employees", ["country"])
    op.create_index("ix_employees_department", "employees", ["department"])
    op.create_index("ix_employees_job_title", "employees", ["job_title"])

    op.create_table(
        "exchange_rates",
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("rate_to_base", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.CheckConstraint(
            "length(currency) = 3 AND currency = upper(currency)",
            name="ck_exchange_rates_currency_iso4217_format",
        ),
        sa.CheckConstraint(
            "rate_to_base > 0",
            name="ck_exchange_rates_rate_to_base_positive",
        ),
        sa.PrimaryKeyConstraint("currency", name="pk_exchange_rates"),
    )

    op.create_table(
        "salaries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "amount > 0",
            name="ck_salaries_amount_positive",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            name="fk_salaries_employee_id_employees",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["currency"],
            ["exchange_rates.currency"],
            name="fk_salaries_currency_exchange_rates",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_salaries"),
        sa.UniqueConstraint(
            "employee_id",
            "effective_from",
            name="uq_salaries_employee_id_effective_from",
        ),
    )
    op.create_index(
        "ix_salaries_employee_effective_from",
        "salaries",
        ["employee_id", sa.text("effective_from DESC")],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_salaries_employee_effective_from",
        table_name="salaries",
    )
    op.drop_table("salaries")
    op.drop_table("exchange_rates")
    op.drop_index("ix_employees_job_title", table_name="employees")
    op.drop_index("ix_employees_department", table_name="employees")
    op.drop_index("ix_employees_country", table_name="employees")
    op.drop_table("employees")
