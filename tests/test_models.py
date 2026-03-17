"""Tests for database models."""

import pytest

from models.schemas import Stock, Portfolio, Transaction, MarketSentiment


class TestStockModel:
    """Test Stock model."""

    def test_create_stock(self, app, db):
        """Stock can be created with required fields."""
        with app.app_context():
            stock = Stock(
                symbol="TEST",
                name="Test Corp",
                sector="Technology",
                current_price=100.0,
                previous_close=98.0,
                day_high=102.0,
                day_low=97.0,
                volume=1000000,
                market_cap=1e10,
            )
            db.session.add(stock)
            db.session.commit()

            saved = Stock.query.filter_by(symbol="TEST").first()
            assert saved is not None
            assert saved.name == "Test Corp"
            assert saved.current_price == 100.0

    def test_change_percent(self, app, db):
        """change_percent() computes daily change correctly."""
        with app.app_context():
            stock = Stock(
                symbol="CHG", name="Change Co", sector="Tech",
                current_price=110.0, previous_close=100.0,
            )
            assert stock.change_percent() == 10.0

    def test_to_dict(self, app, db):
        """to_dict() returns serializable dictionary."""
        with app.app_context():
            stock = Stock(
                symbol="DICT", name="Dict Inc", sector="Finance",
                current_price=50.0, previous_close=48.0,
                day_high=51.0, day_low=47.0, volume=500000,
                market_cap=5e9, pe_ratio=20.5,
            )
            d = stock.to_dict()
            assert d["symbol"] == "DICT"
            assert d["change_percent"] == pytest.approx(4.17, abs=0.01)


class TestPortfolioModel:
    """Test Portfolio model."""

    def test_create_portfolio(self, app, db):
        """Portfolio can be created with defaults."""
        with app.app_context():
            portfolio = Portfolio(name="Test Portfolio")
            db.session.add(portfolio)
            db.session.commit()

            saved = Portfolio.query.first()
            assert saved.name == "Test Portfolio"
            assert saved.cash_balance == 100000.0
