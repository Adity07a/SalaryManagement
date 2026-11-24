"""Pure statistical functions for annual salary analytics."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.services.currency import MONEY_QUANTUM

DEFAULT_IQR_MULTIPLIER = Decimal("1.5")


@dataclass(frozen=True)
class SalaryStatistics:
    """Descriptive statistics for a collection of USD salaries."""

    count: int
    minimum: Decimal | None
    p25: Decimal | None
    median: Decimal | None
    p75: Decimal | None
    maximum: Decimal | None
    average: Decimal | None


@dataclass(frozen=True)
class IQRAnalysis:
    """Interquartile-range outlier analysis."""

    q1: Decimal | None
    q3: Decimal | None
    iqr: Decimal | None
    lower_bound: Decimal | None
    upper_bound: Decimal | None
    outliers: tuple[Decimal, ...]


@dataclass(frozen=True)
class DistributionBucket:
    """One salary histogram bucket."""

    bucket_start: Decimal
    bucket_end: Decimal
    count: int


def _validate_values(
    values: Iterable[Decimal],
) -> list[Decimal]:
    """Validate and copy salary values without modifying the input."""

    result = list(values)

    for value in result:
        if not isinstance(value, Decimal):
            raise TypeError("Salary statistics require Decimal values.")

        if not value.is_finite():
            raise ValueError("Salary values must be finite.")

        if value < 0:
            raise ValueError("Salary values cannot be negative.")

    return result


def _round_money(value: Decimal) -> Decimal:
    """Round a calculated salary statistic to two decimal places."""

    return value.quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def calculate_average(
    values: Iterable[Decimal],
) -> Decimal | None:
    """Calculate arithmetic mean using Decimal arithmetic."""

    salaries = _validate_values(values)

    if not salaries:
        return None

    total = sum(salaries, Decimal("0"))

    return _round_money(total / Decimal(len(salaries)))


def calculate_percentile(
    values: Iterable[Decimal],
    percentile: Decimal,
) -> Decimal | None:
    """Calculate a continuous percentile using linear interpolation.

    This follows the same interpolation convention as PostgreSQL
    percentile_cont.

    percentile:
        A Decimal between 0 and 1.

        0.25 = 25th percentile
        0.50 = median
        0.75 = 75th percentile
    """

    if not isinstance(percentile, Decimal):
        raise TypeError("Percentile must be a Decimal.")

    if not percentile.is_finite():
        raise ValueError("Percentile must be finite.")

    if not Decimal("0") <= percentile <= Decimal("1"):
        raise ValueError("Percentile must be between 0 and 1.")

    salaries = sorted(_validate_values(values))

    if not salaries:
        return None

    if len(salaries) == 1:
        return salaries[0]

    # Continuous percentile position.
    position = Decimal(len(salaries) - 1) * percentile

    lower_index = int(position)

    upper_index = min(
        lower_index + 1,
        len(salaries) - 1,
    )

    interpolation = position - Decimal(lower_index)

    lower_value = salaries[lower_index]
    upper_value = salaries[upper_index]

    result = lower_value + (upper_value - lower_value) * interpolation

    return _round_money(result)


def calculate_median(
    values: Iterable[Decimal],
) -> Decimal | None:
    """Calculate the 50th percentile."""

    return calculate_percentile(
        values,
        Decimal("0.50"),
    )


def calculate_salary_statistics(
    values: Iterable[Decimal],
) -> SalaryStatistics:
    """Calculate descriptive statistics for USD salary values."""

    salaries = _validate_values(values)

    if not salaries:
        return SalaryStatistics(
            count=0,
            minimum=None,
            p25=None,
            median=None,
            p75=None,
            maximum=None,
            average=None,
        )

    return SalaryStatistics(
        count=len(salaries),
        minimum=min(salaries),
        p25=calculate_percentile(
            salaries,
            Decimal("0.25"),
        ),
        median=calculate_median(salaries),
        p75=calculate_percentile(
            salaries,
            Decimal("0.75"),
        ),
        maximum=max(salaries),
        average=calculate_average(salaries),
    )


def detect_iqr_outliers(
    values: Iterable[Decimal],
    multiplier: Decimal = DEFAULT_IQR_MULTIPLIER,
) -> IQRAnalysis:
    """Detect unusually low and high salary values using IQR.

    IQR = Q3 - Q1

    Lower bound = Q1 - (multiplier * IQR)
    Upper bound = Q3 + (multiplier * IQR)

    Values strictly outside these bounds are considered outliers.

    At least four observations are required. Smaller peer groups
    return an analysis without bounds to avoid misleading results.
    """

    if not isinstance(multiplier, Decimal):
        raise TypeError("IQR multiplier must be a Decimal.")

    if not multiplier.is_finite() or multiplier <= 0:
        raise ValueError("IQR multiplier must be finite and positive.")

    salaries = sorted(_validate_values(values))

    if len(salaries) < 4:
        return IQRAnalysis(
            q1=None,
            q3=None,
            iqr=None,
            lower_bound=None,
            upper_bound=None,
            outliers=(),
        )

    q1 = calculate_percentile(
        salaries,
        Decimal("0.25"),
    )

    q3 = calculate_percentile(
        salaries,
        Decimal("0.75"),
    )

    assert q1 is not None
    assert q3 is not None

    iqr = q3 - q1

    lower_bound = _round_money(q1 - multiplier * iqr)

    upper_bound = _round_money(q3 + multiplier * iqr)

    outliers = tuple(
        salary for salary in salaries if salary < lower_bound or salary > upper_bound
    )

    return IQRAnalysis(
        q1=q1,
        q3=q3,
        iqr=iqr,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        outliers=outliers,
    )


def build_salary_distribution(
    values: Iterable[Decimal],
    bucket_count: int = 10,
) -> list[DistributionBucket]:
    """Build evenly spaced histogram buckets from USD salaries.

    All buckets are returned, including empty buckets.

    The first and last bucket include their boundary values.
    If all values are identical, one bucket is returned.
    """

    if (
        isinstance(bucket_count, bool)
        or not isinstance(bucket_count, int)
        or not 1 <= bucket_count <= 100
    ):
        raise ValueError("Bucket count must be an integer between 1 and 100.")

    salaries = sorted(_validate_values(values))

    if not salaries:
        return []

    minimum = salaries[0]
    maximum = salaries[-1]

    if minimum == maximum:
        return [
            DistributionBucket(
                bucket_start=minimum,
                bucket_end=maximum,
                count=len(salaries),
            )
        ]

    width = (maximum - minimum) / Decimal(bucket_count)

    counts = [0] * bucket_count

    for salary in salaries:
        index = int((salary - minimum) / width)

        # The maximum value belongs to the final bucket.
        index = min(index, bucket_count - 1)

        counts[index] += 1

    buckets: list[DistributionBucket] = []

    for index in range(bucket_count):
        start = minimum + width * Decimal(index)

        if index == bucket_count - 1:
            end = maximum
        else:
            end = minimum + width * Decimal(index + 1)

        buckets.append(
            DistributionBucket(
                bucket_start=_round_money(start),
                bucket_end=_round_money(end),
                count=counts[index],
            )
        )

    return buckets
