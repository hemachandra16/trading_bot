"""
Input validators for trading bot parameters.

Every public function raises ``ValueError`` with a human-readable message
when validation fails, making it safe to call before any network request.
"""

from typing import Any, Optional

# ---------------------------------------------------------------------------
# Allowed values
# ---------------------------------------------------------------------------
_VALID_SIDES = {"BUY", "SELL"}
_VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP"}
_PRICE_REQUIRED_TYPES = {"LIMIT", "STOP"}


def validate_symbol(symbol: str) -> str:
    """Validate and normalise a trading pair symbol.

    Rules:
        * Must be a non-empty string.
        * Converted to uppercase.
        * Must be longer than 4 characters (rejects bare "USDT").
        * Must end with ``USDT``.

    Args:
        symbol: Raw symbol string from user input.

    Returns:
        The uppercased, validated symbol.

    Raises:
        ValueError: If the symbol is invalid.
    """
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Symbol must be a non-empty string. Example: BTCUSDT")

    symbol = symbol.strip().upper()

    if len(symbol) <= 4:
        raise ValueError(
            f"Invalid symbol '{symbol}'. Symbol must be longer than 4 characters. "
            f"Example: BTCUSDT, ETHUSDT"
        )

    if not symbol.endswith("USDT"):
        raise ValueError(
            f"Invalid symbol '{symbol}'. Symbol must end with 'USDT'. "
            f"Example: BTCUSDT, ETHUSDT"
        )

    return symbol


def validate_side(side: str) -> str:
    """Validate the order side.

    Args:
        side: Must be ``BUY`` or ``SELL`` (case-insensitive).

    Returns:
        The uppercased, validated side.

    Raises:
        ValueError: If the side is not ``BUY`` or ``SELL``.
    """
    if not side or not isinstance(side, str):
        raise ValueError("Side must be a non-empty string.")

    side = side.strip().upper()

    if side not in _VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(_VALID_SIDES))}."
        )

    return side


def validate_order_type(order_type: str) -> str:
    """Validate the order type.

    Args:
        order_type: Must be ``MARKET``, ``LIMIT``, or ``STOP`` (case-insensitive).

    Returns:
        The uppercased, validated order type.

    Raises:
        ValueError: If the order type is not recognised.
    """
    if not order_type or not isinstance(order_type, str):
        raise ValueError("Order type must be a non-empty string.")

    order_type = order_type.strip().upper()

    if order_type not in _VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(sorted(_VALID_ORDER_TYPES))}."
        )

    return order_type


def validate_quantity(qty: Any) -> float:
    """Validate the order quantity.

    Args:
        qty: Must be a positive number.

    Returns:
        The validated quantity as a float.

    Raises:
        ValueError: If *qty* is not a positive number.
    """
    try:
        qty = float(qty)
    except (TypeError, ValueError):
        raise ValueError(f"Quantity must be a number, got: {qty!r}.")

    if qty <= 0:
        raise ValueError(f"Quantity must be positive, got: {qty}.")

    return qty


def validate_price(price: Any, order_type: str) -> Optional[float]:
    """Validate the price relative to the order type.

    * For ``LIMIT`` and ``STOP`` orders the price is **required** and must be
      a positive float.
    * For ``MARKET`` orders the price is ignored (returns ``None``).

    Args:
        price:      The limit / stop price, or ``None``.
        order_type: Already-validated order type string.

    Returns:
        The validated price as a float, or ``None`` for market orders.

    Raises:
        ValueError: If a required price is missing or non-positive.
    """
    order_type = order_type.strip().upper()

    if order_type in _PRICE_REQUIRED_TYPES:
        if price is None:
            raise ValueError(f"Price is required for {order_type} orders.")
        try:
            price = float(price)
        except (TypeError, ValueError):
            raise ValueError(f"Price must be a number, got: {price!r}.")

        if price <= 0:
            raise ValueError(f"Price must be positive, got: {price}.")

        return price

    # MARKET orders — price is not applicable.
    return None


def validate_stop_price(stop_price: Any, price: Optional[float] = None) -> float:
    """Validate the stop trigger price for stop-limit orders.

    Args:
        stop_price: The stop trigger price to validate.
        price:      The limit price (reserved for future directional checks).

    Returns:
        Validated stop price as a float.

    Raises:
        ValueError: If ``stop_price`` is missing, non-numeric, or not positive.
    """
    if stop_price is None:
        raise ValueError(
            "stop_price is required for STOP orders. "
            "Example: --stop-price 74000"
        )

    try:
        stop_price = float(stop_price)
    except (TypeError, ValueError):
        raise ValueError(
            f"stop_price must be a number, got: {stop_price!r}."
        )

    if stop_price <= 0:
        raise ValueError(
            f"stop_price must be greater than 0, got: {stop_price}."
        )

    return stop_price
