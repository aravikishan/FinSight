"""SQLAlchemy models for FinSight financial data."""

from datetime import datetime, timezone

from models.database import db


class Stock(db.Model):
    """Represents a tradable stock with OHLCV history."""

    __tablename__ = "stocks"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    sector = db.Column(db.String(60), nullable=False, default="Technology")
    current_price = db.Column(db.Float, nullable=False, default=0.0)
    previous_close = db.Column(db.Float, nullable=False, default=0.0)
    day_high = db.Column(db.Float, nullable=False, default=0.0)
    day_low = db.Column(db.Float, nullable=False, default=0.0)
    volume = db.Column(db.Integer, nullable=False, default=0)
    market_cap = db.Column(db.Float, nullable=False, default=0.0)
    pe_ratio = db.Column(db.Float, nullable=True)
    dividend_yield = db.Column(db.Float, nullable=True)
    week_52_high = db.Column(db.Float, nullable=False, default=0.0)
    week_52_low = db.Column(db.Float, nullable=False, default=0.0)
    ohlcv_json = db.Column(db.Text, nullable=False, default="[]")
    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    transactions = db.relationship("Transaction", backref="stock", lazy=True)

    def change_percent(self):
        """Calculate daily change percentage."""
        if self.previous_close and self.previous_close > 0:
            return round(
                ((self.current_price - self.previous_close) / self.previous_close) * 100, 2
            )
        return 0.0

    def to_dict(self):
        """Serialize stock to dictionary."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "sector": self.sector,
            "current_price": round(self.current_price, 2),
            "previous_close": round(self.previous_close, 2),
            "day_high": round(self.day_high, 2),
            "day_low": round(self.day_low, 2),
            "volume": self.volume,
            "market_cap": round(self.market_cap, 2),
            "pe_ratio": round(self.pe_ratio, 2) if self.pe_ratio else None,
            "dividend_yield": round(self.dividend_yield, 4) if self.dividend_yield else None,
            "week_52_high": round(self.week_52_high, 2),
            "week_52_low": round(self.week_52_low, 2),
            "change_percent": self.change_percent(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Portfolio(db.Model):
    """User portfolio with cash balance and positions."""

    __tablename__ = "portfolios"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default="Default Portfolio")
    cash_balance = db.Column(db.Float, nullable=False, default=100000.0)
    initial_value = db.Column(db.Float, nullable=False, default=100000.0)
    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    transactions = db.relationship("Transaction", backref="portfolio", lazy=True)

    def to_dict(self):
        """Serialize portfolio to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "cash_balance": round(self.cash_balance, 2),
            "initial_value": round(self.initial_value, 2),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Transaction(db.Model):
    """Buy/sell transaction for portfolio tracking."""

    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey("portfolios.id"), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey("stocks.id"), nullable=False)
    transaction_type = db.Column(db.String(4), nullable=False)  # "buy" or "sell"
    shares = db.Column(db.Float, nullable=False)
    price_per_share = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    executed_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        """Serialize transaction to dictionary."""
        return {
            "id": self.id,
            "portfolio_id": self.portfolio_id,
            "stock_id": self.stock_id,
            "symbol": self.stock.symbol if self.stock else None,
            "transaction_type": self.transaction_type,
            "shares": round(self.shares, 4),
            "price_per_share": round(self.price_per_share, 2),
            "total_amount": round(self.total_amount, 2),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


class MarketSentiment(db.Model):
    """Market sentiment data from simulated news analysis."""

    __tablename__ = "market_sentiment"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False, index=True)
    headline = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(100), nullable=False, default="FinSight Analytics")
    sentiment_score = db.Column(db.Float, nullable=False, default=0.0)
    sentiment_label = db.Column(db.String(10), nullable=False, default="neutral")
    confidence = db.Column(db.Float, nullable=False, default=0.5)
    published_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        """Serialize sentiment to dictionary."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "headline": self.headline,
            "source": self.source,
            "sentiment_score": round(self.sentiment_score, 4),
            "sentiment_label": self.sentiment_label,
            "confidence": round(self.confidence, 4),
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }
