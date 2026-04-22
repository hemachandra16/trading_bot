"""
Order placement helpers for Binance Futures Testnet.

Each function validates inputs, delegates to the client, and returns a
clean, normalised response dict with the following keys:

    - ``orderId``     – Unique order identifier.
    - ``status``      – Order status (e.g. ``NEW``, ``FILLED``).
    - ``executedQty`` – Quantity filled so far.
    - ``avgPrice``    – Average fill price.
"""

from __future__ import annotations

from typing import Any, Dict

from bot.client import BinanceFuturesClient
from bot.logging_config import get_logger
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_response(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Extract a clean subset from the raw Binance order response.

    Args:
        raw: Full JSON response dict from the Binance API.

    Returns:
        A dict with ``orderId``, ``status``, ``executedQty``, and ``avgPrice``.
    """
    return {
        "orderId": raw.get("orderId"),
        "status": raw.get("status"),
        "executedQty": raw.get("executedQty", "0"),
        "avgPrice": raw.get("avgPrice", "0"),
    }


# ---------------------------------------------------------------------------
# Public order functions
# ---------------------------------------------------------------------------

def place_market_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: float,
) -> Dict[str, Any]:
    """Place a **market** order.

    Args:
        client:   An initialised ``BinanceFuturesClient``.
        symbol:   Trading pair (e.g. ``BTCUSDT``).
        side:     ``BUY`` or ``SELL``.
        quantity: Order quantity.

    Returns:
        Parsed response dict with ``orderId``, ``status``,
        ``executedQty``, and ``avgPrice``.

    Raises:
        ValueError: If any input fails validation.
        BinanceAPIError: On API-level errors.
    """
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    validate_order_type("MARKET")
    quantity = validate_quantity(quantity)

    logger.info("Placing MARKET %s order for %s qty=%s", side, symbol, quantity)

    try:
        raw = client.place_order(
            symbol=symbol,
            side=side,
            order_type="MARKET",
            quantity=quantity,
        )
    except Exception as exc:
        logger.error("Failed to place MARKET order: %s", exc)
        raise

    result = _parse_response(raw)
    logger.info("MARKET order result: %s", result)
    return result


def place_limit_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
) -> Dict[str, Any]:
    """Place a **limit** order.

    Args:
        client:   An initialised ``BinanceFuturesClient``.
        symbol:   Trading pair (e.g. ``BTCUSDT``).
        side:     ``BUY`` or ``SELL``.
        quantity: Order quantity.
        price:    Limit price.

    Returns:
        Parsed response dict with ``orderId``, ``status``,
        ``executedQty``, and ``avgPrice``.

    Raises:
        ValueError: If any input fails validation.
        BinanceAPIError: On API-level errors.
    """
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    validate_order_type("LIMIT")
    quantity = validate_quantity(quantity)
    price = validate_price(price, "LIMIT")

    logger.info(
        "Placing LIMIT %s order for %s qty=%s price=%s",
        side, symbol, quantity, price,
    )

    try:
        raw = client.place_order(
            symbol=symbol,
            side=side,
            order_type="LIMIT",
            quantity=quantity,
            price=price,
        )
    except Exception as exc:
        logger.error("Failed to place LIMIT order: %s", exc)
        raise

    result = _parse_response(raw)
    logger.info("LIMIT order result: %s", result)
    return result


def place_stop_limit_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    stop_price: float,
) -> Dict[str, Any]:
    """Place a **stop-limit** order.

    A stop-limit order becomes a limit order once the *stop_price* is
    triggered.

    Args:
        client:     An initialised ``BinanceFuturesClient``.
        symbol:     Trading pair (e.g. ``BTCUSDT``).
        side:       ``BUY`` or ``SELL``.
        quantity:   Order quantity.
        price:      Limit price (activated after stop triggers).
        stop_price: Trigger / stop price.

    Returns:
        Parsed response dict with ``orderId``, ``status``,
        ``executedQty``, and ``avgPrice``.

    Raises:
        ValueError: If any input fails validation.
        BinanceAPIError: On API-level errors.
    """
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    validate_order_type("STOP")
    quantity = validate_quantity(quantity)
    price = validate_price(price, "STOP")

    stop_price = validate_stop_price(stop_price, price)

    logger.info(
        "Placing STOP %s order for %s qty=%s price=%s stop=%s",
        side, symbol, quantity, price, stop_price,
    )

    try:
        raw = client.place_order(
            symbol=symbol,
            side=side,
            order_type="STOP",
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
    except Exception as exc:
        logger.error("Failed to place STOP order: %s", exc)
        raise

    result = _parse_response(raw)
    logger.info("STOP order result: %s", result)
    return result
