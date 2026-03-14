"""Market data simulation and technical indicator calculations.

Generates realistic OHLCV data using geometric Brownian motion (random walk
with drift) and computes industry-standard technical indicators.
"""

import json
import math
import random
from datetime import datetime, timedelta, timezone

from models.database import db
from models.schemas import Stock, MarketSentiment


# Stock metadata: symbol -> (name, sector, base_price, volatility, shares_outstanding)
STOCK_METADATA = {
    "AAPL": ("Apple Inc.", "Technology", 175.0, 0.018, 15_400_000_000),
    "MSFT": ("Microsoft Corp.", "Technology", 380.0, 0.016, 7_430_000_000),
    "GOOGL": ("Alphabet Inc.", "Technology", 140.0, 0.020, 5_870_000_000),
    "AMZN": ("Amazon.com Inc.", "Consumer Cyclical", 155.0, 0.022, 10_300_000_000),
    "TSLA": ("Tesla Inc.", "Automotive", 245.0, 0.035, 3_170_000_000),
    "META": ("Meta Platforms Inc.", "Technology", 370.0, 0.024, 2_560_000_000),
    "NVDA": ("NVIDIA Corp.", "Technology", 480.0, 0.028, 24_700_000_000),
    "JPM": ("JPMorgan Chase & Co.", "Financial Services", 170.0, 0.014, 2_870_000_000),
    "V": ("Visa Inc.", "Financial Services", 265.0, 0.013, 1_640_000_000),
    "JNJ": ("Johnson & Johnson", "Healthcare", 160.0, 0.011, 2_410_000_000),
    "WMT": ("Walmart Inc.", "Consumer Defensive", 165.0, 0.012, 2_690_000_000),
    "PG": ("Procter & Gamble Co.", "Consumer Defensive", 155.0, 0.010, 2_360_000_000),
    "MA": ("Mastercard Inc.", "Financial Services", 420.0, 0.014, 928_000_000),
    "UNH": ("UnitedHealth Group", "Healthcare", 530.0, 0.015, 936_000_000),
    "HD": ("Home Depot Inc.", "Consumer Cyclical", 340.0, 0.016, 996_000_000),
    "DIS": ("Walt Disney Co.", "Communication Services", 95.0, 0.021, 1_830_000_000),
    "BAC": ("Bank of America Corp.", "Financial Services", 33.0, 0.018, 7_950_000_000),
    "XOM": ("Exxon Mobil Corp.", "Energy", 105.0, 0.017, 3_990_000_000),
    "KO": ("Coca-Cola Co.", "Consumer Defensive", 60.0, 0.009, 4_320_000_000),
    "PFE": ("Pfizer Inc.", "Healthcare", 28.0, 0.020, 5_630_000_000),
    "NFLX": ("Netflix Inc.", "Communication Services", 485.0, 0.025, 432_000_000),
    "INTC": ("Intel Corp.", "Technology", 42.0, 0.023, 4_200_000_000),
}

# Simulated headlines templates for sentiment generation
HEADLINE_TEMPLATES = {
    "bullish": [
        "{company} reports record quarterly revenue, beating estimates by 12%",
        "{company} announces $5B share buyback program",
        "Analysts upgrade {symbol} to Strong Buy with raised price target",
        "{company} secures major partnership with leading enterprise client",
        "{symbol} rallies as new product launch exceeds expectations",
        "Institutional investors increase positions in {symbol} by 15%",
        "{company} posts stronger-than-expected guidance for next quarter",
        "{symbol} breaks through key resistance level on heavy volume",
    ],
    "bearish": [
        "{company} misses revenue estimates, shares drop in after-hours trading",
        "Regulatory concerns mount for {company} amid new investigation",
        "Analysts downgrade {symbol} citing competitive headwinds",
        "{company} announces restructuring, plans to cut 8% of workforce",
        "{symbol} falls as insider selling accelerates",
        "{company} lowers full-year guidance amid macro uncertainty",
        "Supply chain disruptions impact {company} production timeline",
        "{symbol} faces margin pressure as costs rise faster than revenue",
    ],
    "neutral": [
        "{company} trading sideways as market awaits earnings report",
        "{symbol} holds steady near 50-day moving average",
        "Mixed analyst opinions on {company} ahead of sector rotation",
        "{company} maintains dividend, signals stable outlook",
        "{symbol} consolidates in narrow range on low volume",
        "Market participants await Fed decision impact on {symbol}",
    ],
}

NEWS_SOURCES = [
    "Bloomberg", "Reuters", "CNBC", "MarketWatch", "Financial Times",
    "Barron's", "Seeking Alpha", "The Wall Street Journal", "Yahoo Finance",
    "Morningstar",
]


class MarketService:
    """Service for generating and managing simulated market data."""

    @staticmethod
    def generate_ohlcv(base_price, days=252, volatility=0.02, drift=0.0003, seed=None):
        """Generate realistic OHLCV data using geometric Brownian motion.

        Uses a random walk with drift to simulate stock price movements.
        Intraday OHLC is derived from daily close with realistic spread.

        Args:
            base_price: Starting price for the simulation.
            days: Number of trading days to simulate.
            volatility: Daily volatility (standard deviation of log returns).
            drift: Daily drift (mean of log returns), positive = uptrend.
            seed: Optional random seed for reproducibility.

        Returns:
            List of dicts with keys: date, open, high, low, close, volume.
        """
        if seed is not None:
            rng = random.Random(seed)
        else:
            rng = random.Random()

        data = []
        price = base_price
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        for i in range(days):
            current_date = start_date + timedelta(days=i)
            # Skip weekends
            if current_date.weekday() >= 5:
                continue

            # Geometric Brownian motion: dS/S = mu*dt + sigma*dW
            log_return = drift + volatility * rng.gauss(0, 1)
            price = price * math.exp(log_return)

            # Generate realistic OHLC from close price
            daily_range = price * rng.uniform(0.005, 0.03)
            open_price = price + rng.uniform(-daily_range * 0.4, daily_range * 0.4)
            high_price = max(open_price, price) + rng.uniform(0, daily_range * 0.5)
            low_price = min(open_price, price) - rng.uniform(0, daily_range * 0.5)
            close_price = price

            # Ensure OHLC consistency
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)

            # Volume with some randomness and mean-reversion
            base_volume = rng.randint(5_000_000, 50_000_000)
            volume_spike = rng.random()
            if volume_spike > 0.95:
                base_volume = int(base_volume * rng.uniform(2.0, 4.0))
            elif volume_spike > 0.85:
                base_volume = int(base_volume * rng.uniform(1.3, 2.0))

            data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": base_volume,
            })

        return data

    @staticmethod
    def compute_sma(closes, period):
        """Compute Simple Moving Average.

        SMA = sum(close[i-period+1..i]) / period

        Args:
            closes: List of closing prices.
            period: Number of periods for the average.

        Returns:
            List of SMA values (None for insufficient data points).
        """
        result = []
        for i in range(len(closes)):
            if i < period - 1:
                result.append(None)
            else:
                window = closes[i - period + 1: i + 1]
                result.append(round(sum(window) / period, 4))
        return result

    @staticmethod
    def compute_ema(closes, period):
        """Compute Exponential Moving Average.

        EMA_t = close_t * k + EMA_(t-1) * (1 - k)
        where k = 2 / (period + 1)

        Args:
            closes: List of closing prices.
            period: Number of periods for the EMA.

        Returns:
            List of EMA values (None for insufficient data points).
        """
        if len(closes) < period:
            return [None] * len(closes)

        k = 2.0 / (period + 1)
        result = [None] * (period - 1)

        # Seed EMA with SMA of first 'period' values
        sma_seed = sum(closes[:period]) / period
        result.append(round(sma_seed, 4))

        for i in range(period, len(closes)):
            ema_val = closes[i] * k + result[-1] * (1 - k)
            result.append(round(ema_val, 4))

        return result

    @staticmethod
    def compute_rsi(closes, period=14):
        """Compute Relative Strength Index.

        RSI = 100 - (100 / (1 + RS))
        RS = avg_gain / avg_loss over 'period' days.
        Uses Wilder's smoothing method.

        Args:
            closes: List of closing prices.
            period: Lookback period (default 14).

        Returns:
            List of RSI values (None for insufficient data points).
        """
        if len(closes) < period + 1:
            return [None] * len(closes)

        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

        result = [None] * period

        # Initial average gain and loss
        gains = [max(d, 0) for d in deltas[:period]]
        losses = [abs(min(d, 0)) for d in deltas[:period]]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(round(100 - (100 / (1 + rs)), 2))

        # Wilder's smoothing
        for i in range(period, len(deltas)):
            current_gain = max(deltas[i], 0)
            current_loss = abs(min(deltas[i], 0))

            avg_gain = (avg_gain * (period - 1) + current_gain) / period
            avg_loss = (avg_loss * (period - 1) + current_loss) / period

            if avg_loss == 0:
                result.append(100.0)
            else:
                rs = avg_gain / avg_loss
                result.append(round(100 - (100 / (1 + rs)), 2))

        return result

    @staticmethod
    def compute_macd(closes, fast=12, slow=26, signal_period=9):
        """Compute MACD (Moving Average Convergence Divergence).

        MACD Line = EMA(fast) - EMA(slow)
        Signal Line = EMA(MACD Line, signal_period)
        Histogram = MACD Line - Signal Line

        Args:
            closes: List of closing prices.
            fast: Fast EMA period (default 12).
            slow: Slow EMA period (default 26).
            signal_period: Signal line EMA period (default 9).

        Returns:
            Dict with keys: macd_line, signal_line, histogram (lists).
        """
        ema_fast = MarketService.compute_ema(closes, fast)
        ema_slow = MarketService.compute_ema(closes, slow)

        macd_line = []
        for f, s in zip(ema_fast, ema_slow):
            if f is not None and s is not None:
                macd_line.append(round(f - s, 4))
            else:
                macd_line.append(None)

        # Compute signal line as EMA of MACD values (skip Nones)
        valid_macd = [v for v in macd_line if v is not None]
        if len(valid_macd) >= signal_period:
            signal_ema = MarketService.compute_ema(valid_macd, signal_period)
            # Pad signal back to full length
            pad_length = len(macd_line) - len(signal_ema)
            signal_line = [None] * pad_length + signal_ema
        else:
            signal_line = [None] * len(macd_line)

        histogram = []
        for m, s in zip(macd_line, signal_line):
            if m is not None and s is not None:
                histogram.append(round(m - s, 4))
            else:
                histogram.append(None)

        return {
            "macd_line": macd_line,
            "signal_line": signal_line,
            "histogram": histogram,
        }

    @staticmethod
    def compute_bollinger_bands(closes, period=20, num_std=2):
        """Compute Bollinger Bands.

        Middle Band = SMA(period)
        Upper Band = Middle + num_std * StdDev(period)
        Lower Band = Middle - num_std * StdDev(period)

        Args:
            closes: List of closing prices.
            period: SMA period (default 20).
            num_std: Number of standard deviations (default 2).

        Returns:
            Dict with keys: upper, middle, lower (lists).
        """
        sma = MarketService.compute_sma(closes, period)
        upper = []
        lower = []

        for i in range(len(closes)):
            if i < period - 1:
                upper.append(None)
                lower.append(None)
            else:
                window = closes[i - period + 1: i + 1]
                mean = sum(window) / period
                variance = sum((x - mean) ** 2 for x in window) / period
                std_dev = math.sqrt(variance)
                upper.append(round(mean + num_std * std_dev, 4))
                lower.append(round(mean - num_std * std_dev, 4))

        return {
            "upper": upper,
            "middle": sma,
            "lower": lower,
        }

    @staticmethod
    def get_all_indicators(ohlcv_data):
        """Compute all technical indicators for a stock.

        Args:
            ohlcv_data: List of OHLCV dicts.

        Returns:
            Dict containing all indicator results.
        """
        closes = [bar["close"] for bar in ohlcv_data]
        if len(closes) < 2:
            return {}

        return {
            "sma_20": MarketService.compute_sma(closes, 20),
            "sma_50": MarketService.compute_sma(closes, 50),
            "ema_12": MarketService.compute_ema(closes, 12),
            "ema_26": MarketService.compute_ema(closes, 26),
            "rsi": MarketService.compute_rsi(closes, 14),
            "macd": MarketService.compute_macd(closes),
            "bollinger": MarketService.compute_bollinger_bands(closes),
        }

    @staticmethod
    def seed_stocks():
        """Generate and persist simulated stock data to the database."""
        for symbol, (name, sector, base_price, vol, shares_out) in STOCK_METADATA.items():
            existing = Stock.query.filter_by(symbol=symbol).first()
            if existing:
                continue

            seed_val = hash(symbol) % 100000
            ohlcv = MarketService.generate_ohlcv(
                base_price, days=300, volatility=vol, drift=0.0002, seed=seed_val
            )

            if not ohlcv:
                continue

            last_bar = ohlcv[-1]
            prev_bar = ohlcv[-2] if len(ohlcv) > 1 else ohlcv[-1]

            all_highs = [bar["high"] for bar in ohlcv]
            all_lows = [bar["low"] for bar in ohlcv]

            stock = Stock(
                symbol=symbol,
                name=name,
                sector=sector,
                current_price=last_bar["close"],
                previous_close=prev_bar["close"],
                day_high=last_bar["high"],
                day_low=last_bar["low"],
                volume=last_bar["volume"],
                market_cap=round(last_bar["close"] * shares_out, 2),
                pe_ratio=round(random.uniform(10, 45), 2),
                dividend_yield=round(random.uniform(0, 0.04), 4),
                week_52_high=round(max(all_highs), 2),
                week_52_low=round(min(all_lows), 2),
                ohlcv_json=json.dumps(ohlcv),
            )
            db.session.add(stock)

        db.session.commit()

    @staticmethod
    def seed_sentiment():
        """Generate simulated market sentiment entries."""
        for symbol, (name, sector, _, _, _) in STOCK_METADATA.items():
            existing = MarketSentiment.query.filter_by(symbol=symbol).first()
            if existing:
                continue

            num_entries = random.randint(3, 6)
            for _ in range(num_entries):
                category = random.choice(["bullish", "bearish", "neutral"])
                templates = HEADLINE_TEMPLATES[category]
                headline = random.choice(templates).format(company=name, symbol=symbol)
                source = random.choice(NEWS_SOURCES)

                if category == "bullish":
                    score = round(random.uniform(0.3, 1.0), 4)
                elif category == "bearish":
                    score = round(random.uniform(-1.0, -0.3), 4)
                else:
                    score = round(random.uniform(-0.2, 0.2), 4)

                confidence = round(random.uniform(0.5, 0.98), 4)
                published_offset = random.randint(0, 30)
                published_at = datetime.now(timezone.utc) - timedelta(days=published_offset)

                sentiment = MarketSentiment(
                    symbol=symbol,
                    headline=headline,
                    source=source,
                    sentiment_score=score,
                    sentiment_label=category,
                    confidence=confidence,
                    published_at=published_at,
                )
                db.session.add(sentiment)

        db.session.commit()

    @staticmethod
    def get_market_summary():
        """Get a summary of overall market conditions."""
        stocks = Stock.query.all()
        if not stocks:
            return {"total_stocks": 0, "gainers": 0, "losers": 0, "unchanged": 0}

        gainers = [s for s in stocks if s.change_percent() > 0]
        losers = [s for s in stocks if s.change_percent() < 0]
        unchanged = [s for s in stocks if s.change_percent() == 0]

        total_market_cap = sum(s.market_cap for s in stocks)
        avg_change = sum(s.change_percent() for s in stocks) / len(stocks)

        top_gainers = sorted(gainers, key=lambda s: s.change_percent(), reverse=True)[:5]
        top_losers = sorted(losers, key=lambda s: s.change_percent())[:5]

        return {
            "total_stocks": len(stocks),
            "gainers": len(gainers),
            "losers": len(losers),
            "unchanged": len(unchanged),
            "total_market_cap": round(total_market_cap, 2),
            "avg_change_percent": round(avg_change, 2),
            "top_gainers": [s.to_dict() for s in top_gainers],
            "top_losers": [s.to_dict() for s in top_losers],
        }

    @staticmethod
    def get_sector_performance():
        """Calculate performance by sector."""
        stocks = Stock.query.all()
        sectors = {}
        for stock in stocks:
            if stock.sector not in sectors:
                sectors[stock.sector] = {"stocks": [], "total_change": 0.0}
            sectors[stock.sector]["stocks"].append(stock.symbol)
            sectors[stock.sector]["total_change"] += stock.change_percent()

        result = {}
        for sector, data in sectors.items():
            count = len(data["stocks"])
            result[sector] = {
                "stocks": data["stocks"],
                "count": count,
                "avg_change": round(data["total_change"] / count, 2) if count else 0,
            }
        return result
