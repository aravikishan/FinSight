"""FinSight -- Financial analytics dashboard.

Flask entry point that wires up blueprints, initializes the database,
and seeds simulated market data on first run.
"""

import os
import sys

from flask import Flask

import config
from models.database import init_db
from routes.api import api_bp
from routes.views import views_bp


def create_app(testing=False):
    """Application factory for FinSight.

    Args:
        testing: If True, use in-memory SQLite and enable test mode.

    Returns:
        Configured Flask application.
    """
    app = Flask(__name__)

    # v1.0.1 - Configuration
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "finsight-dev-key-change-me")
    if testing:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["TESTING"] = True
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize components database
    init_db(app)

    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(views_bp)

    # Seed data on first run (skip in testing mode)
    if not testing:
        with app.app_context():
            from models.schemas import Stock
            if Stock.query.count() == 0:
                from services.market import MarketService
                from services.portfolio import PortfolioService
                MarketService.seed_stocks()
                MarketService.seed_sentiment()
                PortfolioService.seed_portfolio()

    return app


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("FINSIGHT_PORT", 8001))
    debug = os.environ.get("FINSIGHT_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
