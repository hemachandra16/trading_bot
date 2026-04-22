#!/usr/bin/env python3
"""
CLI entry-point for the Binance Futures Demo Trading Bot.

Run from the trading_bot/ directory::

    python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
    python cli.py --symbol ETHUSDT --side SELL --type LIMIT --qty 0.5 --price 1800
    python cli.py --symbol BTCUSDT --side SELL --type STOP --qty 0.001 --price 25000 --stop-price 25500

The CLI displays a confirmation panel before executing and shows results
in a formatted table on success or an error panel on failure.
"""

from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bot.client import BinanceFuturesClient, BinanceAPIError
from bot.logging_config import get_logger
from bot.orders import place_market_order, place_limit_order, place_stop_limit_order
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
logger = get_logger(__name__)
console = Console()


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for the trading bot CLI."""
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Demo Trading Bot — place orders via CLI.",
    )
    parser.add_argument(
        "--symbol",
        required=True,
        help="Trading pair symbol (e.g. BTCUSDT).",
    )
    parser.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL"],
        help="Order side: BUY or SELL.",
    )
    parser.add_argument(
        "--type",
        required=True,
        dest="order_type",
        choices=["MARKET", "LIMIT", "STOP"],
        help="Order type: MARKET, LIMIT, or STOP.",
    )
    parser.add_argument(
        "--qty",
        required=True,
        type=float,
        help="Order quantity (positive float).",
    )
    parser.add_argument(
        "--price",
        type=float,
        default=None,
        help="Limit price (required for LIMIT and STOP orders).",
    )
    parser.add_argument(
        "--stop-price",
        type=float,
        default=None,
        dest="stop_price",
        help="Stop trigger price (required for STOP orders).",
    )
    return parser


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _show_order_summary(
    symbol: str,
    side: str,
    order_type: str,
    qty: float,
    price: float | None,
    stop_price: float | None,
) -> None:
    """Print a rich Panel summarising the order before confirmation."""
    lines = [
        f"[bold]Symbol:[/bold]     {symbol}",
        f"[bold]Side:[/bold]       {side}",
        f"[bold]Type:[/bold]       {order_type}",
        f"[bold]Quantity:[/bold]   {qty}",
    ]
    if price is not None:
        lines.append(f"[bold]Price:[/bold]      {price}")
    if stop_price is not None:
        lines.append(f"[bold]Stop Price:[/bold] {stop_price}")

    console.print(Panel(
        "\n".join(lines),
        title="[bold]Order Summary[/bold]",
        border_style="yellow",
        padding=(1, 2),
    ))


def _show_result(result: dict) -> None:
    """Print a rich Table with the order result."""
    table = Table(title="Order Result", show_header=True, header_style="bold cyan")
    table.add_column("Field", style="bold white", min_width=14)
    table.add_column("Value", style="green")

    table.add_row("orderId",     str(result.get("orderId", "—")))
    table.add_row("status",      str(result.get("status", "—")))
    table.add_row("executedQty", str(result.get("executedQty", "—")))
    table.add_row("avgPrice",    str(result.get("avgPrice", "—")))

    console.print()
    console.print(table)


def _show_error(message: str) -> None:
    """Print an error panel with a red border."""
    console.print()
    console.print(Panel(
        f"[bold red]{message}[/bold red]",
        title="[bold red]Error[/bold red]",
        border_style="red",
        padding=(1, 2),
    ))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse arguments, validate inputs, confirm with the user, and execute the order."""
    args = _build_parser().parse_args()

    # --- Validate all inputs early, before any network call ------------------
    try:
        symbol     = validate_symbol(args.symbol)
        side       = validate_side(args.side)
        order_type = validate_order_type(args.order_type)
        quantity   = validate_quantity(args.qty)
        price      = validate_price(args.price, order_type)

        # stop_price validation uses the dedicated validator
        if order_type == "STOP":
            stop_price = validate_stop_price(args.stop_price, price)
        else:
            stop_price = None

    except ValueError as exc:
        logger.error("Validation failed: %s", exc)
        _show_error(str(exc))
        sys.exit(1)

    # --- Show summary and ask for confirmation --------------------------------
    _show_order_summary(symbol, side, order_type, quantity, price, stop_price)

    try:
        confirm = console.input("\n[bold yellow]Confirm order? (Y/N): [/bold yellow]")
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Order cancelled.[/dim]")
        sys.exit(0)

    if confirm.strip().upper() != "Y":
        console.print("[dim]Order cancelled by user.[/dim]")
        logger.info("Order cancelled by user.")
        sys.exit(0)

    # --- Place the order ------------------------------------------------------
    # client is initialised to None BEFORE the try block so that the finally
    # clause can safely check `if client is not None` without risking NameError.
    client = None
    try:
        client = BinanceFuturesClient()

        if order_type == "MARKET":
            result = place_market_order(client, symbol, side, quantity)
        elif order_type == "LIMIT":
            result = place_limit_order(client, symbol, side, quantity, price)
        else:  # STOP
            result = place_stop_limit_order(client, symbol, side, quantity, price, stop_price)

        _show_result(result)

    except BinanceAPIError as exc:
        logger.error("Binance API error: %s", exc)
        _show_error(f"Binance API Error (code={exc.code}): {exc.message}")
        sys.exit(1)

    except EnvironmentError as exc:
        logger.error("Environment error: %s", exc)
        _show_error(str(exc))
        sys.exit(1)

    except Exception as exc:
        logger.error("Unexpected error: %s", exc, exc_info=True)
        _show_error(f"Unexpected error: {exc}")
        sys.exit(1)

    finally:
        # Safe — client is always defined (either None or a live client).
        if client is not None:
            try:
                client.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
