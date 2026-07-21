"""
Shared currency conversion utilities.

Single source of truth for cents <-> dollars conversion.
All layers (api/, gateway/, services/) should import from here.
"""

import math


def cents_to_dollars(cents) -> float:
    """Convert cents to dollars for API response."""
    if cents is None:
        return 0.0
    return round(cents / 100, 2)


def dollars_to_cents(dollars) -> int:
    """Convert dollars to cents for storage."""
    if dollars is None:
        return 0
    return int(round(dollars * 100))


def format_price_display(dollars: float, currency: str = "USD") -> str:
    """Format dollar amount as display string (e.g., '$1.50')."""
    if dollars is None:
        dollars = 0.0
    if currency.upper() == "USD":
        return f"${dollars:.2f}"
    return f"{dollars:.2f} {currency.upper()}"


def format_fee_percent_display(decimal_rate: float) -> str:
    """Convert decimal fee rate to display string (e.g., 0.15 -> '15%')."""
    if decimal_rate is None:
        return "0%"
    percent = decimal_rate * 100
    # Use integer display if whole number, otherwise 1 decimal
    if percent == int(percent):
        return f"{int(percent)}%"
    return f"{percent:.1f}%"


def calculate_fee_preview(price_dollars: float, fee_decimal: float) -> dict:
    """
    Calculate fee breakdown for display.

    Args:
        price_dollars: Price in dollars
        fee_decimal: Fee rate as decimal (e.g., 0.15 for 15%)

    Returns:
        Dict with platform_fee, seller_amount, and their display strings.
    """
    if not price_dollars or not fee_decimal:
        return {
            "platform_fee": 0.0,
            "platform_fee_display": "$0.00",
            "seller_amount": price_dollars or 0.0,
            "seller_amount_display": format_price_display(price_dollars or 0.0),
            "fee_percent": 0,
            "fee_percent_display": "0%",
        }
    platform_fee = round(price_dollars * fee_decimal, 2)
    seller_amount = round(price_dollars - platform_fee, 2)
    return {
        "platform_fee": platform_fee,
        "platform_fee_display": format_price_display(platform_fee),
        "seller_amount": seller_amount,
        "seller_amount_display": format_price_display(seller_amount),
        "fee_percent": round(fee_decimal * 100),
        "fee_percent_display": format_fee_percent_display(fee_decimal),
    }


def calculate_net_credits(call_price: int, fee_decimal: float) -> dict:
    """
    Calculate net credits after platform fee for per-call pricing.

    Args:
        call_price: Credits per call (integer)
        fee_decimal: Fee rate as decimal (e.g., 0.15 for 15%)

    Returns:
        Dict with net_credits, fee_credits, and display strings.
    """
    if not call_price or not fee_decimal:
        return {
            "net_credits": call_price or 0,
            "fee_credits": 0,
            "call_price_display": format_price_display(
                cents_to_dollars(call_price) if call_price else 0.0
            ),
            "net_credits_display": format_price_display(
                cents_to_dollars(call_price) if call_price else 0.0
            ),
        }

    fee_credits = math.floor(call_price * fee_decimal)
    net_credits = call_price - fee_credits
    return {
        "net_credits": net_credits,
        "fee_credits": fee_credits,
        "call_price_display": format_price_display(cents_to_dollars(call_price)),
        "net_credits_display": format_price_display(cents_to_dollars(net_credits)),
    }
