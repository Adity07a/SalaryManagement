"""PostgreSQL queries for organisation-wide salary analytics."""

from decimal import Decimal
from typing import Any, Literal

from sqlalchemy import text
from sqlalchemy.orm import Session

SalaryGroupBy = Literal[
    "country",
    "department",
    "job_title",
]


# Only these trusted database columns may be selected dynamically.
GROUP_COLUMNS = {
    "country": "e.country",
    "department": "e.department",
    "job_title": "e.job_title",
}


# One latest salary per employee, with salary converted to USD.
# The conversion and current-salary selection both happen in PostgreSQL.

CURRENT_SALARIES_CTE = """
WITH ranked_salaries AS (
    SELECT
        s.id AS salary_id,
        s.employee_id,
        s.amount,
        s.currency,
        s.effective_from,
        s.created_at,
        (
            s.amount * fx.rate_to_base
        )::NUMERIC(24, 2) AS salary_usd,
        ROW_NUMBER() OVER (
            PARTITION BY s.employee_id
            ORDER BY
                s.effective_from DESC,
                s.id DESC
        ) AS salary_rank
    FROM salaries AS s
    JOIN exchange_rates AS fx
        ON fx.currency = s.currency
),
current_salaries AS (
    SELECT
        salary_id,
        employee_id,
        amount,
        currency,
        effective_from,
        created_at,
        salary_usd
    FROM ranked_salaries
    WHERE salary_rank = 1
)
"""


def get_salary_summary(
    session: Session,
) -> dict[str, Any]:
    """Calculate organisation-wide headcount and payroll metrics."""

    query = text(
        CURRENT_SALARIES_CTE
        + """
        SELECT
            COUNT(e.id)::INTEGER AS headcount,

            COALESCE(
                SUM(cs.salary_usd),
                0
            )::NUMERIC(28, 2) AS total_payroll_usd,

            ROUND(
                AVG(cs.salary_usd),
                2
            )::NUMERIC(28, 2) AS average_salary_usd,

            (
                percentile_cont(0.50)
                WITHIN GROUP (
                    ORDER BY cs.salary_usd
                )
            )::NUMERIC(28, 2) AS median_salary_usd

        FROM employees AS e

        LEFT JOIN current_salaries AS cs
            ON cs.employee_id = e.id
        """
    )

    row = session.execute(query).mappings().one()

    return dict(row)


def get_salary_statistics(
    session: Session,
    group_by: SalaryGroupBy,
) -> list[dict[str, Any]]:
    """Calculate salary statistics by the selected employee dimension."""

    group_column = GROUP_COLUMNS[group_by]

    query = text(
        CURRENT_SALARIES_CTE
        + f"""
        SELECT
            {group_column} AS group_value,

            COUNT(*)::INTEGER AS count,

            MIN(cs.salary_usd)::NUMERIC(24, 2) AS min_usd,

            (
                percentile_cont(0.25)
                WITHIN GROUP (
                    ORDER BY cs.salary_usd
                )
            )::NUMERIC(24, 2) AS p25_usd,

            (
                percentile_cont(0.50)
                WITHIN GROUP (
                    ORDER BY cs.salary_usd
                )
            )::NUMERIC(24, 2) AS median_usd,

            (
                percentile_cont(0.75)
                WITHIN GROUP (
                    ORDER BY cs.salary_usd
                )
            )::NUMERIC(24, 2) AS p75_usd,

            MAX(cs.salary_usd)::NUMERIC(24, 2) AS max_usd,

            ROUND(
                AVG(cs.salary_usd),
                2
            )::NUMERIC(24, 2) AS avg_usd

        FROM employees AS e

        JOIN current_salaries AS cs
            ON cs.employee_id = e.id

        GROUP BY {group_column}

        ORDER BY {group_column} ASC
        """
    )

    rows = session.execute(query).mappings().all()

    return [dict(row) for row in rows]


def get_salary_distribution(
    session: Session,
    bucket_count: int = 10,
) -> list[dict[str, Any]]:
    """Calculate salary histogram buckets entirely in PostgreSQL."""

    query = text(
        CURRENT_SALARIES_CTE
        + """
        ,
        salary_bounds AS (
            SELECT
                MIN(salary_usd) AS minimum_salary,
                MAX(salary_usd) AS maximum_salary,
                COUNT(*) AS salary_count
            FROM current_salaries
        ),

        bucket_counts AS (
            SELECT
                CASE
                    WHEN bounds.minimum_salary =
                         bounds.maximum_salary
                    THEN 0
                    ELSE LEAST(
                        width_bucket(
                            cs.salary_usd,
                            bounds.minimum_salary,
                            bounds.maximum_salary,
                            :bucket_count
                        ) - 1,
                        :bucket_count - 1
                    )
                END AS bucket_index,

                COUNT(*)::INTEGER AS employee_count

            FROM current_salaries AS cs

            CROSS JOIN salary_bounds AS bounds

            GROUP BY 1
        )

        SELECT
            CASE
                WHEN bounds.minimum_salary =
                     bounds.maximum_salary
                THEN bounds.minimum_salary

                ELSE ROUND(
                    bounds.minimum_salary
                    +
                    (
                        bounds.maximum_salary
                        - bounds.minimum_salary
                    )
                    * bucket.bucket_index::NUMERIC
                    / :bucket_count,
                    2
                )
            END::NUMERIC(24, 2) AS bucket_start_usd,

            CASE
                WHEN bounds.minimum_salary =
                     bounds.maximum_salary
                THEN bounds.maximum_salary

                ELSE ROUND(
                    bounds.minimum_salary
                    +
                    (
                        bounds.maximum_salary
                        - bounds.minimum_salary
                    )
                    * (bucket.bucket_index + 1)::NUMERIC
                    / :bucket_count,
                    2
                )
            END::NUMERIC(24, 2) AS bucket_end_usd,

            COALESCE(
                bucket_counts.employee_count,
                0
            )::INTEGER AS count

        FROM salary_bounds AS bounds

        CROSS JOIN LATERAL generate_series(
            0,
            CASE
                WHEN bounds.salary_count = 0 THEN -1
                WHEN bounds.minimum_salary =
                     bounds.maximum_salary THEN 0
                ELSE :bucket_count - 1
            END
        ) AS bucket(bucket_index)

        LEFT JOIN bucket_counts
            ON bucket_counts.bucket_index =
               bucket.bucket_index

        ORDER BY bucket.bucket_index
        """
    )

    rows = (
        session.execute(
            query,
            {"bucket_count": bucket_count},
        )
        .mappings()
        .all()
    )

    return [dict(row) for row in rows]


def get_salary_outliers(
    session: Session,
    *,
    group_by: SalaryGroupBy,
    threshold: Decimal,
    minimum_peer_count: int = 4,
) -> list[dict[str, Any]]:
    """Identify unusually high and low salaries within peer groups.

    The Interquartile Range method is used.

    Groups containing fewer than minimum_peer_count employees
    are excluded to avoid misleading outlier classifications.
    """

    group_column = GROUP_COLUMNS[group_by]

    query = text(
        CURRENT_SALARIES_CTE
        + f"""
        ,
        peer_statistics AS (
            SELECT
                {group_column} AS group_value,

                COUNT(*)::INTEGER AS peer_count,

                percentile_cont(0.25)
                WITHIN GROUP (
                    ORDER BY cs.salary_usd
                ) AS q1,

                percentile_cont(0.50)
                WITHIN GROUP (
                    ORDER BY cs.salary_usd
                ) AS peer_median,

                percentile_cont(0.75)
                WITHIN GROUP (
                    ORDER BY cs.salary_usd
                ) AS q3

            FROM employees AS e

            JOIN current_salaries AS cs
                ON cs.employee_id = e.id

            GROUP BY {group_column}
        ),

        peer_bounds AS (
            SELECT
                group_value,
                peer_count,
                peer_median,

                q1 - (
                    CAST(:threshold AS NUMERIC)
                    * (q3 - q1)
                ) AS lower_bound,

                q3 + (
                    CAST(:threshold AS NUMERIC)
                    * (q3 - q1)
                ) AS upper_bound

            FROM peer_statistics

            WHERE peer_count >= :minimum_peer_count
        )

        SELECT
            e.id AS employee_id,
            e.full_name,
            e.job_title,
            e.department,
            e.country,

            cs.salary_usd,

            pb.peer_median::NUMERIC(24, 2)
                AS peer_median_usd,

            ROUND(
                (
                    (
                        (
                            cs.salary_usd - pb.peer_median
                        )
                        / NULLIF(pb.peer_median, 0)
                            ) * 100
                        )::NUMERIC,
                        2
                    )::NUMERIC(24, 2) AS deviation_percent,

            CASE
                WHEN cs.salary_usd > pb.upper_bound
                THEN 'high'
                ELSE 'low'
            END AS direction

        FROM employees AS e

        JOIN current_salaries AS cs
            ON cs.employee_id = e.id

        JOIN peer_bounds AS pb
            ON pb.group_value = {group_column}

        WHERE
            cs.salary_usd < pb.lower_bound
            OR cs.salary_usd > pb.upper_bound

        ORDER BY
            ABS(
                (
                    cs.salary_usd - pb.peer_median
                ) / NULLIF(pb.peer_median, 0)
            ) DESC,

            e.id ASC
        """
    )

    rows = (
        session.execute(
            query,
            {
                "threshold": threshold,
                "minimum_peer_count": minimum_peer_count,
            },
        )
        .mappings()
        .all()
    )

    return [dict(row) for row in rows]
