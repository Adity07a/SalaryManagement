"""Tests for Decimal-based currency conversion."""

from decimal import Decimal

import pytest
from app.services.currency import convert_to_base


def test_usd_conversion_preserves_salary_amount() -> None:
    result = convert_to_base(
        Decimal("95000.00"),
        Decimal("1.00000000"),
    )

    assert result == Decimal("95000.00")


def test_inr_salary_converts_correctly_to_usd() -> None:
    result = convert_to_base(
        Decimal("5000000.00"),
        Decimal("0.01200000"),
    )

    assert result == Decimal("60000.00")


def test_gbp_salary_converts_correctly_to_usd() -> None:
    result = convert_to_base(
        Decimal("100000.00"),
        Decimal("1.27000000"),
    )

    assert result == Decimal("127000.00")


def test_currency_conversion_rounds_using_half_up() -> None:
    result = convert_to_base(
        Decimal("1.005"),
        Decimal("1.00000000"),
    )

    assert result == Decimal("1.01")


def test_currency_conversion_rejects_negative_salary() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        convert_to_base(
            Decimal("-100.00"),
            Decimal("1.00000000"),
        )


def test_currency_conversion_rejects_zero_exchange_rate() -> None:
    with pytest.raises(ValueError, match="positive"):
        convert_to_base(
            Decimal("100.00"),
            Decimal("0.00000000"),
        )


def test_currency_conversion_rejects_float_amount() -> None:
    with pytest.raises(TypeError, match="must be a Decimal"):
        convert_to_base(
            100.50,  # type: ignore[arg-type]
            Decimal("1.00000000"),
        )


def test_currency_conversion_rejects_non_finite_rate() -> None:
    with pytest.raises(ValueError, match="finite"):
        convert_to_base(
            Decimal("100.00"),
            Decimal("NaN"),
        )
