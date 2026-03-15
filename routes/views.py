"""HTML-serving view routes for FinSight."""

import json

from flask import Blueprint, render_template

from models.schemas import Stock, MarketSentiment
from services.market import MarketService
from services.portfolio import PortfolioService

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def index():
    """Market dashboard with top movers and summary."""
    summary = MarketService.get_market_summary()
    sectors = MarketService.get_sector_performance()
    stocks = Stock.query.order_by(Stock.symbol).all()
    return render_template(
        "index.html",
        summary=summary,
        sectors=sectors,
        stocks=stocks,
    )


@views_bp.route("/stock/<symbol>")
def stock_detail(symbol):
    """Individual stock detail page with chart and indicators."""
    stock = Stock.query.filter_by(symbol=symbol.upper()).first()
    if not stock:
        return render_template("index.html", error=f"Stock {symbol} not found"), 404

    ohlcv = json.loads(stock.ohlcv_json) if stock.ohlcv_json else []
    indicators = MarketService.get_all_indicators(ohlcv) if ohlcv else {}

    sentiments = (
        MarketSentiment.query
        .filter_by(symbol=symbol.upper())
        .order_by(MarketSentiment.published_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "stock.html",
        stock=stock,
        ohlcv=ohlcv,
        indicators=indicators,
        sentiments=sentiments,
    )


@views_bp.route("/portfolio")
def portfolio_view():
    """Portfolio management page."""
    portfolio = PortfolioService.get_or_create_portfolio()
    positions = PortfolioService.get_positions(portfolio.id)
    allocation = PortfolioService.get_allocation(portfolio.id)
    performance = PortfolioService.get_performance(portfolio.id)

    return render_template(
        "portfolio.html",
        portfolio=portfolio,
        positions=positions,
        allocation=allocation,
        performance=performance,
    )


@views_bp.route("/sentiment")
def sentiment_view():
    """Market sentiment analysis page."""
    entries = (
        MarketSentiment.query
        .order_by(MarketSentiment.published_at.desc())
        .all()
    )

    # Aggregate by symbol
    symbol_scores = {}
    for entry in entries:
        if entry.symbol not in symbol_scores:
            symbol_scores[entry.symbol] = {"scores": [], "labels": []}
        symbol_scores[entry.symbol]["scores"].append(entry.sentiment_score)
        symbol_scores[entry.symbol]["labels"].append(entry.sentiment_label)

    aggregated = []
    for symbol, data in sorted(symbol_scores.items()):
        avg = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
        bull = data["labels"].count("bullish")
        bear = data["labels"].count("bearish")
        neut = data["labels"].count("neutral")
        aggregated.append({
            "symbol": symbol,
            "avg_score": round(avg, 3),
            "bullish": bull,
            "bearish": bear,
            "neutral": neut,
            "total": len(data["scores"]),
            "label": "bullish" if avg > 0.15 else "bearish" if avg < -0.15 else "neutral",
        })

    return render_template(
        "sentiment.html",
        entries=entries,
        aggregated=aggregated,
    )


@views_bp.route("/about")
def about():
    """About page."""
    return render_template("about.html")
