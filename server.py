"""
Quantra Trading Bot — FastAPI Backend Server.

Provides REST API endpoints for the Quantra web UI to:
  - Place orders on Binance Futures Demo API
  - Retrieve order history (in-memory; resets on server restart)
  - Fetch account balance
  - Proxy live price data

Run with:
    uvicorn server:app --host 0.0.0.0 --port 8000 --reload

Or use the included start.bat (Windows).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from bot.client import BinanceFuturesClient, BinanceAPIError
from bot.orders import place_market_order, place_limit_order, place_stop_limit_order
from bot.logging_config import get_logger

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
load_dotenv()
logger = get_logger(__name__)

app = FastAPI(title="Quantra Trading Bot API", version="1.0.0")

# CORS: credentials + wildcard origin is rejected by browsers per CORS spec.
# Restrict origins to the localhost addresses we actually serve from.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory state
# NOTE: order_history is intentionally in-memory. Data is lost on restart.
# For production replace with a database (PostgreSQL + SQLAlchemy recommended).
# ---------------------------------------------------------------------------
order_history: List[Dict[str, Any]] = []
_client: Optional[BinanceFuturesClient] = None


def _get_client() -> BinanceFuturesClient:
    """Lazy-initialise and cache the Binance client as a module-level singleton."""
    global _client
    if _client is None:
        try:
            _client = BinanceFuturesClient()
        except EnvironmentError as exc:
            logger.warning("No valid API keys — client unavailable: %s", exc)
            raise HTTPException(
                status_code=500,
                detail="API keys not configured. Set API_KEY and API_SECRET in .env",
            )
    return _client


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------
class OrderRequest(BaseModel):
    """Incoming order request body."""
    symbol:     str            = "BTCUSDT"
    side:       str            = "BUY"
    type:       str            = "MARKET"
    quantity:   float          = 0.001
    price:      Optional[float] = None
    stop_price: Optional[float] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/order")
async def place_order(req: OrderRequest) -> Dict[str, Any]:
    """Place an order via Binance Futures Demo API.

    Calls the appropriate function from orders.py based on the order type.
    Wraps the synchronous order helper with asyncio.to_thread() so the
    blocking httpx.Client call does not stall the event loop.
    """
    try:
        c = _get_client()
        order_type = req.type.strip().upper()

        if order_type == "MARKET":
            result = await asyncio.to_thread(
                place_market_order, c, req.symbol, req.side, req.quantity
            )
        elif order_type == "LIMIT":
            if req.price is None:
                raise ValueError("Price is required for LIMIT orders.")
            result = await asyncio.to_thread(
                place_limit_order, c, req.symbol, req.side, req.quantity, req.price
            )
        elif order_type == "STOP":
            if req.price is None or req.stop_price is None:
                raise ValueError("Both price and stop_price are required for STOP orders.")
            result = await asyncio.to_thread(
                place_stop_limit_order,
                c, req.symbol, req.side, req.quantity, req.price, req.stop_price,
            )
        else:
            raise ValueError(f"Unknown order type: {order_type}")

        # Enrich result with metadata for the history feed.
        result["symbol"]    = req.symbol.upper()
        result["side"]      = req.side.upper()
        result["type"]      = order_type
        result["quantity"]  = str(req.quantity)
        result["price"]     = str(req.price) if req.price else "MARKET"
        result["timestamp"] = datetime.now(timezone.utc).isoformat()

        order_history.insert(0, result)
        logger.info("Order placed and stored: orderId=%s", result.get("orderId"))

        return {"success": True, "data": result}

    except ValueError as exc:
        logger.error("Validation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except BinanceAPIError as exc:
        logger.error("Binance API error: %s", exc)
        raise HTTPException(
            status_code=exc.status_code,
            detail=f"Binance Error (code={exc.code}): {exc.message}",
        )
    except HTTPException:
        raise  # re-raise FastAPI exceptions untouched
    except Exception as exc:
        logger.error("Unexpected error placing order: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/orders")
async def get_orders() -> Dict[str, Any]:
    """Return the full in-memory order history."""
    return {"success": True, "data": order_history}


@app.get("/api/balance")
async def get_balance() -> Dict[str, Any]:
    """Fetch USDT available balance from Binance Futures Demo API.

    Uses the BinanceFuturesClient.get_balance() method so HMAC signing
    logic is not duplicated here. Falls back to a mock value if keys are
    not configured or the API call fails.
    """
    try:
        c = _get_client()
        balances = await asyncio.to_thread(c.get_balance)
        usdt = next((b for b in balances if b.get("asset") == "USDT"), None)
        if usdt:
            return {
                "success": True,
                "data": {
                    "asset": "USDT",
                    "availableBalance": usdt.get("availableBalance", "0.00"),
                    "balance": usdt.get("balance", "0.00"),
                },
            }
    except Exception as exc:
        logger.warning("Balance fetch failed, using mock fallback: %s", exc)

    # Fallback — shown when keys are placeholder or API is unreachable.
    return {
        "success": True,
        "data": {"asset": "USDT", "availableBalance": "5000.00", "balance": "5000.00"},
    }


@app.get("/api/price")
async def get_price(symbol: str = "BTCUSDT") -> Dict[str, Any]:
    """Proxy the 24hr ticker from Binance Futures for the given symbol.

    This endpoint does NOT require auth — it calls the public ticker endpoint.
    Uses asyncio-native httpx.AsyncClient to avoid blocking the event loop.
    """
    import httpx as _httpx
    try:
        async with _httpx.AsyncClient(timeout=10.0) as http:
            resp = await http.get(
                "https://demo-fapi.binance.com/fapi/v1/ticker/24hr",
                params={"symbol": symbol.upper()},
            )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "success": True,
                "data": {
                    "symbol": data.get("symbol", symbol),
                    "lastPrice": data.get("lastPrice", "0.00"),
                    "priceChangePercent": data.get("priceChangePercent", "0.00"),
                },
            }
    except Exception as exc:
        logger.warning("Price fetch failed, using mock fallback: %s", exc)

    return {
        "success": True,
        "data": {"symbol": symbol, "lastPrice": "78012.60", "priceChangePercent": "2.26"},
    }


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok", "service": "quantra-backend"}


# ---------------------------------------------------------------------------
# Static files — serve the React UI from the /ui directory.
# ---------------------------------------------------------------------------
UI_DIR = Path(__file__).parent / "ui"


@app.get("/")
async def serve_root() -> FileResponse:
    """Serve the main index.html for the Quantra dashboard."""
    return FileResponse(UI_DIR / "index.html")


# WARNING: This static file mount MUST remain the LAST statement in this file.
# Any route defined AFTER this line will be unreachable — FastAPI matches the
# mount's wildcard path before any subsequent route definitions.
app.mount("/", StaticFiles(directory=str(UI_DIR), html=True), name="ui")
