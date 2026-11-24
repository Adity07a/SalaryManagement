from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def test_initial_migration_creates_expected_tables_and_indexes(tmp_path: Path) -> None:
    database_path = tmp_path / "migration-test.sqlite"
    engine = create_engine(f"sqlite:///{database_path}")
    config = Config(str(BACKEND_ROOT / "alembic.ini"))

    try:
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")

            inspector = inspect(connection)
            table_names = set(inspector.get_table_names())
            assert {
                "employees",
                "exchange_rates",
                "salaries",
                "alembic_version",
            }.issubset(table_names)

            employee_indexes = {
                index["name"] for index in inspector.get_indexes("employees")
            }
            assert employee_indexes == {
                "ix_employees_country",
                "ix_employees_department",
                "ix_employees_job_title",
            }

            salary_indexes = {
                index["name"] for index in inspector.get_indexes("salaries")
            }
            assert "ix_salaries_employee_effective_from" in salary_indexes

            command.downgrade(config, "base")
            remaining_tables = set(inspect(connection).get_table_names())
            assert "employees" not in remaining_tables
            assert "exchange_rates" not in remaining_tables
            assert "salaries" not in remaining_tables
    finally:
        engine.dispose()
