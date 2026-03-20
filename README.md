# FinSight - Financial Analytics Dashboard

[![CI](https://github.com/ravikishan/finsight/actions/workflows/ci.yml/badge.svg)](https://github.com/ravikishan/finsight/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask 3.0](https://img.shields.io/badge/flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive financial analytics dashboard built with Flask, featuring simulated
stock market data, technical analysis indicators, portfolio management, and market
sentiment scoring.

![FinSight Dashboard](https://img.shields.io/badge/status-live-brightgreen)

---

## Features

- **Market Dashboard** -- Real-time overview of 22 simulated stocks with top gainers,
  losers, and sector performance breakdown
- **Stock Analysis** -- Individual stock pages with OHLCV candlestick-style price charts,
  volume analysis, and overlaid technical indicators
- **Technical Indicators** -- Industry-standard calculations:
  - Simple Moving Average (SMA) with configurable periods
  - Exponential Moving Average (EMA) with proper seeding
  - Relative Strength Index (RSI) using Wilder's smoothing
  - MACD with signal line and histogram
  - Bollinger Bands with standard deviation envelope
- **Portfolio Management** -- Buy/sell stocks, track positions, monitor unrealized
  and realized P&L, view cost basis and returns
- **Portfolio Allocation** -- Interactive donut chart showing allocation by stock
  and by sector with cash position
- **Market Sentiment** -- Simulated news headlines with bull/bear/neutral scoring,
  confidence metrics, and aggregated sentiment views
- **REST API** -- Full JSON API for programmatic access to all data
- **Responsive Design** -- Dark finance theme with green/red gain/loss coloring

## Architecture

```
finsight/
|-- app.py                     # Flask application factory
|-- config.py                  # Configuration and constants
|-- models/
|   |-- database.py            # SQLAlchemy / SQLite setup
|   |-- schemas.py             # Stock, Portfolio, Transaction, MarketSentiment
|-- routes/
|   |-- api.py                 # REST API endpoints (/api/*)
|   |-- views.py               # HTML template routes
|-- services/
|   |-- market.py              # OHLCV generation, technical indicators
|   |-- portfolio.py           # Portfolio tracking, P&L, allocation
|-- templates/                 # Jinja2 HTML templates
|-- static/
|   |-- css/style.css          # Dark finance theme
|   |-- js/main.js             # Chart.js visualizations
|-- tests/                     # pytest test suite
|-- seed_data/data.json        # Stock metadata
```

## Quick Start

### Option 1: Local Python

```bash
# Clone the repository
git clone https://github.com/ravikishan/finsight.git
cd finsight

# Run the start script
chmod +x start.sh
./start.sh
```

Or manually:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Option 2: Docker

```bash
docker-compose up --build
```

The dashboard will be available at **http://localhost:8001**

## API Documentation

### Stocks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stocks` | List all stocks (optional `?sector=Technology`) |
| GET | `/api/stocks/<symbol>` | Get stock detail with OHLCV history |
| GET | `/api/stocks/<symbol>/indicators` | Get technical indicators (SMA, EMA, RSI, MACD, BB) |

### Market

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/market/summary` | Market overview: gainers, losers, avg change |
| GET | `/api/market/sectors` | Performance breakdown by sector |

### Portfolio

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/portfolio` | Portfolio summary (cash, initial value) |
| GET | `/api/portfolio/positions` | Current holdings with P&L |
| GET | `/api/portfolio/allocation` | Allocation by stock and sector |
| GET | `/api/portfolio/performance` | Performance metrics and returns |
| GET | `/api/portfolio/transactions` | Transaction history |
| POST | `/api/portfolio/buy` | Execute buy order (`{"symbol": "AAPL", "shares": 10}`) |
| POST | `/api/portfolio/sell` | Execute sell order (`{"symbol": "AAPL", "shares": 5}`) |

### Sentiment

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sentiment` | All sentiment entries (optional `?symbol=AAPL`) |
| GET | `/api/sentiment/summary` | Aggregated sentiment per stock |

### Example API Calls

```bash
# Get all stocks
curl http://localhost:8001/api/stocks

# Get AAPL details with OHLCV data
curl http://localhost:8001/api/stocks/AAPL

# Get technical indicators
curl http://localhost:8001/api/stocks/AAPL/indicators

# Buy 10 shares of MSFT
curl -X POST http://localhost:8001/api/portfolio/buy \
  -H "Content-Type: application/json" \
  -d '{"symbol": "MSFT", "shares": 10}'

# Get portfolio performance
curl http://localhost:8001/api/portfolio/performance
```

## Data Generation

### Stock Prices

Stock prices are simulated using **Geometric Brownian Motion** (GBM):

```
dS/S = mu * dt + sigma * dW
```

Where:
- `S` = stock price
- `mu` = drift (expected return)
- `sigma` = volatility
- `dW` = Wiener process increment

Each stock has unique volatility and drift parameters calibrated to produce
realistic price movements over 252 trading days.

### Technical Indicators

All indicators are computed using standard financial mathematics:

- **SMA**: Simple arithmetic mean over N periods
- **EMA**: Exponentially weighted average with smoothing factor k = 2/(N+1)
- **RSI**: Relative Strength Index using Wilder's smoothing method
- **MACD**: Difference between fast and slow EMAs with signal line
- **Bollinger Bands**: SMA +/- 2 standard deviations

### Sentiment

Market sentiment is generated from templated news headlines categorized as
bullish, bearish, or neutral, with randomized confidence scores.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_services.py -v
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11+, Flask 3.0 |
| Database | SQLite with SQLAlchemy ORM |
| Charts | Chart.js 4.4 |
| Testing | pytest, pytest-cov |
| Deployment | Docker, Gunicorn |
| CI/CD | GitHub Actions |

## Configuration

Configuration is managed through `config.py` and environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `FINSIGHT_PORT` | 8001 | Server port |
| `FINSIGHT_DEBUG` | false | Debug mode |
| `DATABASE_URL` | sqlite:///... | Database connection string |
| `SECRET_KEY` | (dev key) | Flask secret key |

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Disclaimer

FinSight is a demonstration project. All market data is simulated using mathematical
models and does not reflect actual market conditions. This application should **not**
be used for real trading or investment decisions.

---

Built with Flask and Chart.js.
