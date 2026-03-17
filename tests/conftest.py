"""Pytest fixtures for FinSight tests."""

import pytest

from app import create_app
from models.database import db as _db


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    app = create_app(testing=True)
    yield app


@pytest.fixture(scope="session")
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    """Provide a clean database for each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture
def seed_data(app, db):
    """Seed the database with test data."""
    with app.app_context():
        from services.market import MarketService
        from services.portfolio import PortfolioService
        MarketService.seed_stocks()
        MarketService.seed_sentiment()
        PortfolioService.seed_portfolio()
        yield db
