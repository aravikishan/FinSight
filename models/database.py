"""SQLite database setup and initialization for FinSight."""

import os

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Initialize the database with the Flask app."""
    instance_dir = os.path.join(app.root_path, "instance")
    os.makedirs(instance_dir, exist_ok=True)

    db.init_app(app)

    with app.app_context():
        from models.schemas import Stock, Portfolio, Transaction, MarketSentiment  # noqa: F401
        db.create_all()

    return db
