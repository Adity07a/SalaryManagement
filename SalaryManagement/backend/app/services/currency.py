"""Pure currency conversion utilities using Decimal."""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

BASE_CURRENCY = "USD"
MONEY_QUANTUM = Decimal("0.01")


def convert_to_base(
    amount: Decimal,
    rate_to_base: Decimal,
) -> Decimal:
    """Convert a local-currency amount into the base currency.

    rate_to_base represents the value of one unit of local
    currency in USD.

    Example:
        1 INR = 0.012 USD

        5000000 INR * 0.012 = 60000 USD

    No floating-point arithmetic is used.
    """

    if not isinstance(amount, Decimal):
        raise TypeError("Salary amount must be a Decimal.")

    if not isinstance(rate_to_base, Decimal):
        raise TypeError("Exchange rate must be a Decimal.")

    if not amount.is_finite():
        raise ValueError("Salary amount must be finite.")

    if not rate_to_base.is_finite() or rate_to_base <= 0:
        raise ValueError("Exchange rate must be finite and positive.")

    if amount < 0:
        raise ValueError("Salary amount cannot be negative.")

    try:
        converted_amount = amount * rate_to_base

        return converted_amount.quantize(
            MONEY_QUANTUM,
            rounding=ROUND_HALF_UP,
        )

    except InvalidOperation as exc:
        raise ValueError("Currency conversion failed.") from exc
