"""REST API endpoints for FinSight financial data."""

import json

from flask import Blueprint, jsonify, request

from models.schemas import Stock, MarketSentiment
from services.market import MarketService
from services.portfolio import PortfolioService

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/stocks", methods=["GET"])
def list_stocks():
    """List all stocks with optional sector filter."""
    sector = request.args.get("sector")
    query = Stock.query
    if sector:
        query = query.filter(Stock.sector == sector)
    stocks = query.order_by(Stock.symbol).all()
    return jsonify({"stocks": [s.to_dict() for s in stocks], "count": len(stocks)})


@api_bp.route("/stocks/<symbol>", methods=["GET"])
def get_stock(symbol):
    """Get detailed stock data including OHLCV history."""
    stock = Stock.query.filter_by(symbol=symbol.upper()).first()
    if not stock:
        return jsonify({"error": f"Stock {symbol} not found"}), 404

    data = stock.to_dict()
    ohlcv = json.loads(stock.ohlcv_json) if stock.ohlcv_json else []
    data["ohlcv"] = ohlcv
    return jsonify(data)


@api_bp.route("/stocks/<symbol>/indicators", methods=["GET"])
def get_indicators(symbol):
    """Get technical indicators for a stock."""
    stock = Stock.query.filter_by(symbol=symbol.upper()).first()
    if not stock:
        return jsonify({"error": f"Stock {symbol} not found"}), 404

    ohlcv = json.loads(stock.ohlcv_json) if stock.ohlcv_json else []
    if len(ohlcv) < 2:
        return jsonify({"error": "Insufficient data for indicators"}), 400

    indicators = MarketService.get_all_indicators(ohlcv)
    dates = [bar["date"] for bar in ohlcv]
    indicators["dates"] = dates
    indicators["symbol"] = symbol.upper()
    return jsonify(indicators)


@api_bp.route("/market/summary", methods=["GET"])
def market_summary():
    """Get overall market summary."""
    summary = MarketService.get_market_summary()
    return jsonify(summary)


@api_bp.route("/market/sectors", methods=["GET"])
def sector_performance():
    """Get performance breakdown by sector."""
    sectors = MarketService.get_sector_performance()
    return jsonify({"sectors": sectors})


@api_bp.route("/sentiment", methods=["GET"])
def list_sentiment():
    """List all sentiment entries with optional symbol filter."""
    symbol = request.args.get("symbol")
    query = MarketSentiment.query
    if symbol:
        query = query.filter(MarketSentiment.symbol == symbol.upper())
    entries = query.order_by(MarketSentiment.published_at.desc()).all()
    return jsonify({"sentiment": [e.to_dict() for e in entries], "count": len(entries)})


@api_bp.route("/sentiment/summary", methods=["GET"])
def sentiment_summary():
    """Get aggregated sentiment summary per stock."""
    entries = MarketSentiment.query.all()
    symbol_data = {}
    for entry in entries:
        if entry.symbol not in symbol_data:
            symbol_data[entry.symbol] = {
                "scores": [],
                "bullish": 0,
                "bearish": 0,
                "neutral": 0,
            }
        symbol_data[entry.symbol]["scores"].append(entry.sentiment_score)
        symbol_data[entry.symbol][entry.sentiment_label] += 1

    summary = []
    for symbol, data in sorted(symbol_data.items()):
        scores = data["scores"]
        avg_score = sum(scores) / len(scores) if scores else 0
        total = data["bullish"] + data["bearish"] + data["neutral"]
        summary.append({
            "symbol": symbol,
            "avg_score": round(avg_score, 4),
            "total_entries": total,
            "bullish_count": data["bullish"],
            "bearish_count": data["bearish"],
            "neutral_count": data["neutral"],
            "overall_label": (
                "bullish" if avg_score > 0.15
                else "bearish" if avg_score < -0.15
                else "neutral"
            ),
        })
    return jsonify({"summary": summary})


@api_bp.route("/portfolio", methods=["GET"])
def get_portfolio():
    """Get portfolio summary."""
    portfolio = PortfolioService.get_or_create_portfolio()
    return jsonify(portfolio.to_dict())


@api_bp.route("/portfolio/positions", methods=["GET"])
def get_positions():
    """Get current portfolio positions."""
    portfolio = PortfolioService.get_or_create_portfolio()
    positions = PortfolioService.get_positions(portfolio.id)
    return jsonify({"positions": positions, "count": len(positions)})


@api_bp.route("/portfolio/allocation", methods=["GET"])
def get_allocation():
    """Get portfolio allocation breakdown."""
    portfolio = PortfolioService.get_or_create_portfolio()
    allocation = PortfolioService.get_allocation(portfolio.id)
    return jsonify(allocation)


@api_bp.route("/portfolio/performance", methods=["GET"])
def get_performance():
    """Get portfolio performance metrics."""
    portfolio = PortfolioService.get_or_create_portfolio()
    performance = PortfolioService.get_performance(portfolio.id)
    return jsonify(performance)


@api_bp.route("/portfolio/transactions", methods=["GET"])
def get_transactions():
    """Get portfolio transaction history."""
    from models.schemas import Transaction

    portfolio = PortfolioService.get_or_create_portfolio()
    txns = (
        Transaction.query
        .filter_by(portfolio_id=portfolio.id)
        .order_by(Transaction.executed_at.desc())
        .all()
    )
    return jsonify({"transactions": [t.to_dict() for t in txns], "count": len(txns)})


@api_bp.route("/portfolio/buy", methods=["POST"])
def buy_stock():
    """Execute a buy order."""
    data = request.get_json()
    if not data or "symbol" not in data or "shares" not in data:
        return jsonify({"error": "symbol and shares are required"}), 400

    portfolio = PortfolioService.get_or_create_portfolio()
    try:
        shares = float(data["shares"])
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid shares value"}), 400

    result = PortfolioService.buy_stock(portfolio.id, data["symbol"], shares)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 201


@api_bp.route("/portfolio/sell", methods=["POST"])
def sell_stock():
    """Execute a sell order."""
    data = request.get_json()
    if not data or "symbol" not in data or "shares" not in data:
        return jsonify({"error": "symbol and shares are required"}), 400

    portfolio = PortfolioService.get_or_create_portfolio()
    try:
        shares = float(data["shares"])
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid shares value"}), 400

    result = PortfolioService.sell_stock(portfolio.id, data["symbol"], shares)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 201
