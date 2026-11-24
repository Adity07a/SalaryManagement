"""Tests for pure salary statistical calculations."""

from decimal import Decimal

import pytest
from app.services.salary_statistics import (
    build_salary_distribution,
    calculate_average,
    calculate_median,
    calculate_percentile,
    calculate_salary_statistics,
    detect_iqr_outliers,
)


def test_average_uses_decimal_arithmetic() -> None:
    salaries = [
        Decimal("100.00"),
        Decimal("200.00"),
        Decimal("300.00"),
    ]

    assert calculate_average(salaries) == Decimal("200.00")


def test_average_returns_none_for_empty_input() -> None:
    assert calculate_average([]) is None


def test_median_returns_middle_value_for_odd_count() -> None:
    salaries = [
        Decimal("100.00"),
        Decimal("300.00"),
        Decimal("200.00"),
    ]

    assert calculate_median(salaries) == Decimal("200.00")


def test_median_interpolates_for_even_count() -> None:
    salaries = [
        Decimal("100.00"),
        Decimal("200.00"),
        Decimal("300.00"),
        Decimal("400.00"),
    ]

    assert calculate_median(salaries) == Decimal("250.00")


def test_median_returns_none_for_empty_input() -> None:
    assert calculate_median([]) is None


def test_percentile_uses_continuous_interpolation() -> None:
    salaries = [
        Decimal("10.00"),
        Decimal("20.00"),
        Decimal("30.00"),
        Decimal("40.00"),
    ]

    assert calculate_percentile(
        salaries,
        Decimal("0.25"),
    ) == Decimal("17.50")

    assert calculate_percentile(
        salaries,
        Decimal("0.75"),
    ) == Decimal("32.50")


def test_percentile_rejects_values_outside_zero_and_one() -> None:
    salaries = [Decimal("100.00")]

    with pytest.raises(ValueError, match="between 0 and 1"):
        calculate_percentile(
            salaries,
            Decimal("1.5"),
        )


def test_percentile_rejects_float_input() -> None:
    with pytest.raises(TypeError, match="must be a Decimal"):
        calculate_percentile(
            [Decimal("100.00")],
            0.5,  # type: ignore[arg-type]
        )


def test_salary_statistics_calculates_all_required_metrics() -> None:
    salaries = [
        Decimal("100.00"),
        Decimal("200.00"),
        Decimal("300.00"),
        Decimal("400.00"),
    ]

    result = calculate_salary_statistics(salaries)

    assert result.count == 4
    assert result.minimum == Decimal("100.00")
    assert result.p25 == Decimal("175.00")
    assert result.median == Decimal("250.00")
    assert result.p75 == Decimal("325.00")
    assert result.maximum == Decimal("400.00")
    assert result.average == Decimal("250.00")


def test_salary_statistics_handles_empty_input() -> None:
    result = calculate_salary_statistics([])

    assert result.count == 0
    assert result.minimum is None
    assert result.p25 is None
    assert result.median is None
    assert result.p75 is None
    assert result.maximum is None
    assert result.average is None


def test_median_of_converted_salaries_uses_same_base_currency() -> None:
    # Local salaries converted to USD first:
    #
    # 5,000,000 INR * 0.012 = 60,000 USD
    # 100,000 USD = 100,000 USD
    # 80,000 GBP * 1.27 = 101,600 USD

    converted_salaries = [
        Decimal("60000.00"),
        Decimal("100000.00"),
        Decimal("101600.00"),
    ]

    assert calculate_median(converted_salaries) == Decimal("100000.00")


def test_iqr_detects_extreme_high_salary_outlier() -> None:
    salaries = [
        Decimal("10.00"),
        Decimal("11.00"),
        Decimal("12.00"),
        Decimal("13.00"),
        Decimal("14.00"),
        Decimal("15.00"),
        Decimal("16.00"),
        Decimal("1000.00"),
    ]

    result = detect_iqr_outliers(salaries)

    assert result.q1 == Decimal("11.75")
    assert result.q3 == Decimal("15.25")
    assert result.iqr == Decimal("3.50")
    assert result.lower_bound == Decimal("6.50")
    assert result.upper_bound == Decimal("20.50")
    assert result.outliers == (Decimal("1000.00"),)


def test_iqr_does_not_flag_normal_salary_values() -> None:
    salaries = [
        Decimal("50000.00"),
        Decimal("55000.00"),
        Decimal("60000.00"),
        Decimal("65000.00"),
        Decimal("70000.00"),
        Decimal("75000.00"),
        Decimal("80000.00"),
        Decimal("85000.00"),
    ]

    result = detect_iqr_outliers(salaries)

    assert result.outliers == ()


def test_iqr_skips_peer_groups_smaller_than_four() -> None:
    salaries = [
        Decimal("50000.00"),
        Decimal("55000.00"),
        Decimal("250000.00"),
    ]

    result = detect_iqr_outliers(salaries)

    assert result.q1 is None
    assert result.q3 is None
    assert result.lower_bound is None
    assert result.upper_bound is None
    assert result.outliers == ()


def test_iqr_rejects_non_positive_multiplier() -> None:
    with pytest.raises(ValueError, match="positive"):
        detect_iqr_outliers(
            [
                Decimal("100.00"),
                Decimal("200.00"),
                Decimal("300.00"),
                Decimal("400.00"),
            ],
            multiplier=Decimal("0"),
        )


def test_salary_distribution_creates_correct_buckets() -> None:
    salaries = [
        Decimal("10.00"),
        Decimal("20.00"),
        Decimal("30.00"),
        Decimal("40.00"),
    ]

    buckets = build_salary_distribution(
        salaries,
        bucket_count=2,
    )

    assert len(buckets) == 2

    assert buckets[0].bucket_start == Decimal("10.00")
    assert buckets[0].bucket_end == Decimal("25.00")
    assert buckets[0].count == 2

    assert buckets[1].bucket_start == Decimal("25.00")
    assert buckets[1].bucket_end == Decimal("40.00")
    assert buckets[1].count == 2

    assert sum(bucket.count for bucket in buckets) == 4


def test_salary_distribution_handles_empty_input() -> None:
    assert build_salary_distribution([]) == []


def test_salary_distribution_handles_identical_salaries() -> None:
    buckets = build_salary_distribution(
        [
            Decimal("50000.00"),
            Decimal("50000.00"),
            Decimal("50000.00"),
        ],
        bucket_count=10,
    )

    assert len(buckets) == 1
    assert buckets[0].bucket_start == Decimal("50000.00")
    assert buckets[0].bucket_end == Decimal("50000.00")
    assert buckets[0].count == 3


def test_salary_distribution_rejects_invalid_bucket_count() -> None:
    with pytest.raises(ValueError, match="between 1 and 100"):
        build_salary_distribution(
            [Decimal("100.00")],
            bucket_count=0,
        )


def test_statistics_reject_float_values() -> None:
    with pytest.raises(TypeError, match="require Decimal"):
        calculate_average([100.0, 200.0])  # type: ignore[list-item]


def test_statistics_do_not_mutate_input_values() -> None:
    salaries = [
        Decimal("300.00"),
        Decimal("100.00"),
        Decimal("200.00"),
    ]

    original = salaries.copy()

    calculate_salary_statistics(salaries)

    assert salaries == original
