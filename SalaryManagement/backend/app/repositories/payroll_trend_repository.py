"""Database queries for historical payroll trends."""

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

PAYROLL_TREND_QUERY = text("""
    WITH monthly_periods AS (
        SELECT
            (
                DATE_TRUNC('month', CURRENT_DATE)
                - (
                    series.month_offset
                    * INTERVAL '1 month'
                )
            )::DATE AS month_start,

            LEAST(
                (
                    DATE_TRUNC('month', CURRENT_DATE)
                    - (
                        series.month_offset
                        * INTERVAL '1 month'
                    )
                    + INTERVAL '1 month'
                    - INTERVAL '1 day'
                )::DATE,
                CURRENT_DATE
            ) AS as_of_date

        FROM GENERATE_SERIES(
            CAST(:months AS INTEGER) - 1,
            0,
            -1
        ) AS series(month_offset)
    ),

    ranked_salaries AS (
        SELECT
            mp.month_start,
            e.id AS employee_id,

            (
                s.amount * fx.rate_to_base
            )::NUMERIC(24, 2) AS salary_usd,

            ROW_NUMBER() OVER (
                PARTITION BY mp.month_start, e.id
                ORDER BY
                    s.effective_from DESC,
                    s.id DESC
            ) AS salary_rank

        FROM monthly_periods AS mp

        JOIN employees AS e
            ON e.hire_date <= mp.as_of_date
            AND (
                CAST(:country AS VARCHAR) IS NULL
                OR e.country = CAST(:country AS VARCHAR)
            )
            AND (
                CAST(:department AS VARCHAR) IS NULL
                OR e.department = CAST(:department AS VARCHAR)
            )

        JOIN salaries AS s
            ON s.employee_id = e.id
            AND s.effective_from <= mp.as_of_date

        JOIN exchange_rates AS fx
            ON fx.currency = s.currency
    ),

    monthly_totals AS (
        SELECT
            month_start,

            COUNT(*)::INTEGER AS headcount,

            COALESCE(
                SUM(salary_usd),
                0
            )::NUMERIC(24, 2) AS total_payroll_usd,

            COALESCE(
                ROUND(AVG(salary_usd), 2),
                0
            )::NUMERIC(24, 2) AS average_salary_usd

        FROM ranked_salaries

        WHERE salary_rank = 1

        GROUP BY month_start
    )

    SELECT
        TO_CHAR(mp.month_start, 'YYYY-MM') AS month,

        COALESCE(
            mt.headcount,
            0
        )::INTEGER AS headcount,

        COALESCE(
            mt.total_payroll_usd,
            0
        )::NUMERIC(24, 2) AS total_payroll_usd,

        COALESCE(
            mt.average_salary_usd,
            0
        )::NUMERIC(24, 2) AS average_salary_usd

    FROM monthly_periods AS mp

    LEFT JOIN monthly_totals AS mt
        ON mt.month_start = mp.month_start

    ORDER BY mp.month_start ASC
    """)


def fetch_payroll_trends(
    session: Session,
    months: int,
    country: str | None = None,
    department: str | None = None,
) -> list[dict[str, Any]]:
    """Return monthly payroll snapshots with optional filters."""

    result = session.execute(
        PAYROLL_TREND_QUERY,
        {
            "months": months,
            "country": country,
            "department": department,
        },
    )

    return [dict(row) for row in result.mappings().all()]
