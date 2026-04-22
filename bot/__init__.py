"""
Binance Futures Testnet Trading Bot Package.

Provides a lightweight, httpx-based client for placing orders on the
Binance Futures Demo API with full HMAC-SHA256 request signing.
"""

from bot.client import BinanceFuturesClient, BinanceAPIError
from bot.orders import place_market_order, place_limit_order, place_stop_limit_order
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)
from bot.logging_config import get_logger

__all__ = [
    "BinanceFuturesClient",
    "BinanceAPIError",           # was missing — external callers need this
    "place_market_order",
    "place_limit_order",
    "place_stop_limit_order",
    "validate_symbol",
    "validate_side",
    "validate_order_type",
    "validate_quantity",
    "validate_price",
    "validate_stop_price",       # new validator added
    "get_logger",
]
