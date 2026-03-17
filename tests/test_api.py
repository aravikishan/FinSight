"""Tests for REST API endpoints."""

import json

import pytest


class TestStockAPI:
    """Test stock-related API endpoints."""

    def test_list_stocks_empty(self, client, db):
        """GET /api/stocks returns empty list when no data."""
        resp = client.get("/api/stocks")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "stocks" in data
        assert data["count"] == 0

    def test_list_stocks_with_data(self, client, seed_data):
        """GET /api/stocks returns seeded stocks."""
        resp = client.get("/api/stocks")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] > 0
        assert data["stocks"][0]["symbol"] is not None

    def test_get_stock_not_found(self, client, db):
        """GET /api/stocks/<symbol> returns 404 for unknown symbol."""
        resp = client.get("/api/stocks/ZZZZZ")
        assert resp.status_code == 404
        data = resp.get_json()
        assert "error" in data

    def test_get_stock_detail(self, client, seed_data):
        """GET /api/stocks/AAPL returns stock with OHLCV data."""
        resp = client.get("/api/stocks/AAPL")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["symbol"] == "AAPL"
        assert "ohlcv" in data
        assert len(data["ohlcv"]) > 0

    def test_get_indicators(self, client, seed_data):
        """GET /api/stocks/AAPL/indicators returns technical indicators."""
        resp = client.get("/api/stocks/AAPL/indicators")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["symbol"] == "AAPL"
        assert "sma_20" in data
        assert "rsi" in data
        assert "macd" in data
        assert "bollinger" in data


class TestMarketAPI:
    """Test market summary endpoints."""

    def test_market_summary(self, client, seed_data):
        """GET /api/market/summary returns overall market data."""
        resp = client.get("/api/market/summary")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_stocks" in data
        assert data["total_stocks"] > 0

    def test_sector_performance(self, client, seed_data):
        """GET /api/market/sectors returns sector breakdown."""
        resp = client.get("/api/market/sectors")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "sectors" in data
        assert len(data["sectors"]) > 0


class TestPortfolioAPI:
    """Test portfolio endpoints."""

    def test_get_portfolio(self, client, seed_data):
        """GET /api/portfolio returns portfolio summary."""
        resp = client.get("/api/portfolio")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "cash_balance" in data

    def test_get_positions(self, client, seed_data):
        """GET /api/portfolio/positions returns current positions."""
        resp = client.get("/api/portfolio/positions")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "positions" in data

    def test_buy_missing_fields(self, client, seed_data):
        """POST /api/portfolio/buy rejects missing fields."""
        resp = client.post("/api/portfolio/buy", json={})
        assert resp.status_code == 400

    def test_buy_stock(self, client, seed_data):
        """POST /api/portfolio/buy executes a buy order."""
        resp = client.post("/api/portfolio/buy", json={
            "symbol": "KO",
            "shares": 10,
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["status"] == "success"


class TestSentimentAPI:
    """Test sentiment endpoints."""

    def test_list_sentiment(self, client, seed_data):
        """GET /api/sentiment returns sentiment entries."""
        resp = client.get("/api/sentiment")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "sentiment" in data
        assert data["count"] > 0

    def test_sentiment_summary(self, client, seed_data):
        """GET /api/sentiment/summary returns aggregated scores."""
        resp = client.get("/api/sentiment/summary")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "summary" in data
        assert len(data["summary"]) > 0
