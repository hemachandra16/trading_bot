# Binance Futures Demo Trading Bot — Quantra

A lightweight, production-quality trading bot for the **Binance Futures Demo API** (`demo-fapi.binance.com`) built with pure `httpx` — no `python-binance` dependency. Includes a full **Quantra React dashboard** served by a FastAPI backend.

> **API Endpoint Note:** This project uses `https://demo-fapi.binance.com` instead of the legacy `https://testnet.binancefuture.com`. The legacy URL now redirects to `demo.binance.com` and is no longer a standalone API endpoint. The demo API provides identical Futures USDT-M paper trading functionality. All order types, HMAC-SHA256 signing, and response formats are the same.

## Features

- **HMAC-SHA256 request signing** — secure, from-scratch implementation
- **Three order types** — Market, Limit, and Stop-Limit
- **Input validation** — all parameters validated before network calls
- **Rich CLI output** — colored confirmation panels, result tables, and error displays
- **Dual logging** — colored console output (INFO) + rotating file logging (DEBUG, 5MB/3 backups)
- **Secure config** — credentials loaded from `.env`, never hardcoded
- **React Web UI** — live price ticker, order placement, portfolio view, onboarding tour

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package exports (including BinanceAPIError)
│   ├── client.py            # httpx-based Binance Futures client with HMAC signing
│   ├── orders.py            # Order placement helpers (market, limit, stop-limit)
│   ├── validators.py        # Input validation with clear error messages
│   └── logging_config.py    # Dual console + rotating file logging
├── ui/
│   ├── index.html           # Quantra dashboard entry point
│   ├── app.jsx              # React application (Babel in-browser transpile)
│   └── styles.css           # Full design system — dark neon theme
├── logs/
│   └── .gitkeep             # Preserves log directory in git
├── server.py                # FastAPI backend — serves REST API + static UI
├── cli.py                   # CLI entry point (argparse + rich output)
├── start.bat                # Windows: start the FastAPI server
├── requirements.txt         # Python dependencies
├── .env                     # API credentials (NOT committed to git)
└── README.md                # This file
```

## Setup

### 1. Clone the repository

> Requires **Python 3.9+**

```bash
git clone <repo-url>
cd trading_bot
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create your `.env` file

Create a file named `.env` in the `trading_bot/` directory:

```env
API_KEY=your_binance_demo_api_key_here
API_SECRET=your_binance_demo_api_secret_here
```

> **Get demo credentials:** Sign in to [https://www.binance.com](https://www.binance.com) and create an API key pair. Use them with the Demo Trading API at `https://demo-fapi.binance.com`. No separate testnet registration is needed for the demo endpoint.

⚠️ **Never commit your `.env` file.** It is already included in `.gitignore`.

---

## CLI Usage

All commands are run from the `trading_bot/` project root.

### Market Order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
```

### Limit Order

```bash
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --qty 0.5 --price 1800.00
```

### Stop-Limit Order

```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP --qty 0.001 --price 25000 --stop-price 25500
```

### CLI Output

After running a command, you'll see:

1. **Order Summary** — a yellow-bordered panel showing all order parameters
2. **Confirmation Prompt** — type `Y` to proceed or `N` to cancel
3. **Result Table** — displays `orderId`, `status`, `executedQty`, and `avgPrice`

On error, a red-bordered panel shows the error message.

---

## Web UI — Quantra Dashboard

Quantra includes a full React-based trading dashboard with live price ticker, order placement, portfolio view, and an interactive onboarding tour.

### Start the backend server

```bash
cd trading_bot
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Or use the included batch file (Windows):

```bash
start.bat
```

### Open the dashboard

Navigate to:

```
http://localhost:8000
```

### Dashboard features

- **Layout selector** on startup — Dashboard View (all panels) or Tabbed View
- **Live BTCUSDT price ticker** polling Binance every 3 seconds
- **Order placement** — Market, Limit, and Stop-Limit with confirmation modal
- **Real-time order history** and recent activity feed
- **Live margin balance** from Binance Demo API (falls back to mock if unconfigured)
- **Interactive 7-step onboarding tour** (first visit only, stored in sessionStorage)
- **Sidebar navigation** — Terminal, Portfolio, Strategies, Signals, Settings
- **Settings modal** — Switch Layout returns to startup selector

---

## Logging

- **Console:** INFO-level messages with color via `rich`
- **File:** Configurable level (default: DEBUG) written to `logs/trading_bot.log`
- **Rotation:** 5 MB per file, 3 backup files kept automatically

Log format: `[TIMESTAMP] [LEVEL] [MODULE] — message`

Override log level via environment variable:
```bash
LOG_LEVEL=INFO uvicorn server:app --reload
```

---

## Assumptions

- **Demo API** — This bot is configured for the Binance Demo Trading API (`https://demo-fapi.binance.com`), which is the current recommended environment for paper trading. The legacy testnet URL (`https://testnet.binancefuture.com`) is not used.
- **Orders show `status=NEW` with `executedQty=0.0000`** — this is expected on the demo environment. Market makers are simulated; order placement and API communication are confirmed working (see `logs/trading_bot.log`).
- **In-memory order history** — the server's order list resets on restart. This is intentional for a demo. In production, replace with a database (PostgreSQL + SQLAlchemy recommended).
- **Web UI requires the server** — open `http://localhost:8000` only after the FastAPI server is running.
- **USDT pairs only** — all symbols must end with `USDT` (e.g. `BTCUSDT`, `ETHUSDT`).
- **Python 3.9+** — requires Python 3.9 or later.

---

## Dependencies

| Package          | Purpose                                  |
| ---------------- | ---------------------------------------- |
| `httpx`          | HTTP client for REST API calls           |
| `python-dotenv`  | Load credentials from `.env` file        |
| `rich`           | Colored console output and tables        |
| `fastapi`        | Web framework for the REST API + UI host |
| `uvicorn`        | ASGI server for FastAPI                  |
| `pydantic`       | Request body validation for FastAPI      |
