"""
Binance Futures Demo REST client.

Uses ``httpx`` for all HTTP communication and HMAC-SHA256 for request
signing.  Credentials are loaded from a ``.env`` file via ``python-dotenv``.

Usage:
    from bot.client import BinanceFuturesClient

    client = BinanceFuturesClient()
    response = client.place_order("BTCUSDT", "BUY", "MARKET", 0.001)
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv

from bot.logging_config import get_logger

# ---------------------------------------------------------------------------
# Load environment variables once at module level, not per-instantiation.
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Module-level logger
# ---------------------------------------------------------------------------
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_URL = "https://demo-fapi.binance.com"
ORDER_ENDPOINT = "/fapi/v1/order"
BALANCE_ENDPOINT = "/fapi/v2/balance"
DEFAULT_TIMEOUT = 10.0        # seconds
DEFAULT_RECV_WINDOW = 5000    # milliseconds


class BinanceAPIError(Exception):
    """Raised when the Binance API returns a non-2xx response or a non-JSON body."""

    def __init__(self, status_code: int, code: int, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(
            f"Binance API Error {status_code} (code={code}): {message}"
        )


class BinanceFuturesClient:
    """Lightweight Binance Futures Demo client with HMAC-SHA256 signing.

    The client reads ``API_KEY`` and ``API_SECRET`` from a ``.env`` file
    located in the project root (or any parent directory picked up by
    ``python-dotenv``).

    Args:
        api_key:    Override the API key (defaults to ``$API_KEY`` from env).
        api_secret: Override the API secret (defaults to ``$API_SECRET`` from env).
        base_url:   Override the base URL (defaults to demo-fapi.binance.com).
        timeout:    HTTP timeout in seconds.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: str = BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        # load_dotenv() is called at module level — no need to repeat here.
        self._api_key = api_key or os.getenv("API_KEY")
        self._api_secret = api_secret or os.getenv("API_SECRET")

        if not self._api_key or not self._api_secret:
            raise EnvironmentError(
                "API_KEY and API_SECRET must be set in the .env file or "
                "passed explicitly to BinanceFuturesClient."
            )

        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._recv_window = DEFAULT_RECV_WINDOW

        self._http = httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers={"X-MBX-APIKEY": self._api_key},
        )

        logger.info("BinanceFuturesClient initialised (base_url=%s)", self._base_url)

    # ------------------------------------------------------------------
    # Signing
    # ------------------------------------------------------------------
    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sign request parameters with HMAC-SHA256.

        Creates a **defensive copy** of params before adding timestamp and
        signature.  The caller's dict is never mutated.

        Args:
            params: Query parameters to sign. This dict is NOT mutated.

        Returns:
            New dict with ``timestamp``, ``recvWindow``, and ``signature`` added.
        """
        signed = {**params}  # defensive copy — never mutate the caller's dict
        signed["timestamp"] = int(time.time() * 1000)
        signed["recvWindow"] = self._recv_window

        query_string = urlencode(signed)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        signed["signature"] = signature
        return signed

    # ------------------------------------------------------------------
    # Internal HTTP helper
    # ------------------------------------------------------------------
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Any:
        """Make an HTTP request to the Binance API.

        Args:
            method:   HTTP method — ``"GET"`` or ``"POST"``.
            endpoint: API path (e.g. ``"/fapi/v1/order"``).
            params:   Query / body parameters.
            signed:   Whether to add HMAC-SHA256 timestamp + signature.

        Returns:
            Parsed JSON response (dict or list).

        Raises:
            BinanceAPIError: On non-2xx responses or non-JSON body.
            httpx.TimeoutException: On request timeout.
            httpx.ConnectError: On connection failure.
        """
        if params is None:
            params = {}

        if signed:
            params = self._sign(params)

        try:
            if method.upper() == "GET":
                response = self._http.get(endpoint, params=params)
            else:
                response = self._http.post(endpoint, params=params)
        except httpx.TimeoutException:
            logger.error("Request timed out: %s %s", method, endpoint)
            raise
        except httpx.ConnectError:
            logger.error("Connection error — cannot reach %s", self._base_url)
            raise
        except httpx.HTTPError as exc:
            logger.error("HTTP error: %s", exc)
            raise

        # Guard against non-JSON error pages (e.g. 502 gateway responses).
        try:
            data = response.json()
        except Exception:
            raise BinanceAPIError(
                status_code=response.status_code,
                code=-1,
                message=f"Non-JSON response from Binance: {response.text[:200]}",
            )

        if response.status_code != 200:
            api_code = data.get("code", -1)
            api_msg = data.get("msg", "Unknown error")
            logger.error(
                "Binance API error %d (code=%d): %s",
                response.status_code, api_code, api_msg,
            )
            raise BinanceAPIError(response.status_code, api_code, api_msg)

        return data

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Place an order on Binance Futures Demo.

        Args:
            symbol:     Trading pair (e.g. ``BTCUSDT``).
            side:       ``BUY`` or ``SELL``.
            order_type: ``MARKET``, ``LIMIT``, or ``STOP``.
            quantity:   Order quantity.
            price:      Limit price (required for LIMIT / STOP).
            stop_price: Stop trigger price (required for STOP).

        Returns:
            The raw JSON response dict from the Binance API.

        Raises:
            BinanceAPIError: On non-2xx API responses.
            httpx.TimeoutException: On request timeout.
            httpx.ConnectError: On connection failure.
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }

        # LIMIT orders require timeInForce and price.
        if order_type == "LIMIT":
            params["timeInForce"] = "GTC"
            if price is not None:
                params["price"] = str(price)

        # STOP becomes a stop-limit when both price and stopPrice are given.
        if order_type == "STOP":
            if stop_price is not None:
                params["stopPrice"] = str(stop_price)
            if price is not None:
                params["price"] = str(price)
                params["timeInForce"] = "GTC"

        logger.debug(
            "Placing order — symbol=%s side=%s type=%s qty=%s price=%s stop=%s",
            symbol, side, order_type, quantity, price, stop_price,
        )

        data = self._request("POST", ORDER_ENDPOINT, params=params, signed=True)

        logger.info(
            "Order placed successfully — orderId=%s status=%s",
            data.get("orderId"), data.get("status"),
        )
        return data

    def get_balance(self) -> List[Dict[str, Any]]:
        """Fetch account balance from Binance Futures Demo.

        Returns:
            List of balance dicts each containing ``asset``, ``balance``,
            and ``availableBalance`` fields.

        Raises:
            BinanceAPIError: If the API call fails.
        """
        logger.debug("Fetching account balance")
        result = self._request("GET", BALANCE_ENDPOINT, signed=True)
        # The endpoint returns a list; guard against unexpected shapes.
        return result if isinstance(result, list) else []

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()
        logger.debug("HTTP client closed.")

    def __enter__(self) -> "BinanceFuturesClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
