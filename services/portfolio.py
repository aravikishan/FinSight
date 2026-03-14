"""Portfolio management service: tracking, P&L, allocation analysis."""

import json
from collections import defaultdict
from datetime import datetime, timezone

from models.database import db
from models.schemas import Stock, Portfolio, Transaction


class PortfolioService:
    """Service for portfolio operations and analytics."""

    @staticmethod
    def get_or_create_portfolio(name="Default Portfolio"):
        """Get existing portfolio or create a new one."""
        portfolio = Portfolio.query.filter_by(name=name).first()
        if not portfolio:
            portfolio = Portfolio(name=name, cash_balance=100000.0, initial_value=100000.0)
            db.session.add(portfolio)
            db.session.commit()
        return portfolio

    @staticmethod
    def buy_stock(portfolio_id, symbol, shares):
        """Execute a buy transaction.

        Args:
            portfolio_id: ID of the portfolio.
            symbol: Stock ticker symbol.
            shares: Number of shares to buy.

        Returns:
            Dict with transaction details or error message.
        """
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return {"error": "Portfolio not found"}

        stock = Stock.query.filter_by(symbol=symbol.upper()).first()
        if not stock:
            return {"error": f"Stock {symbol} not found"}

        if shares <= 0:
            return {"error": "Shares must be positive"}

        total_cost = round(stock.current_price * shares, 2)
        if total_cost > portfolio.cash_balance:
            return {"error": "Insufficient funds", "available": portfolio.cash_balance}

        transaction = Transaction(
            portfolio_id=portfolio.id,
            stock_id=stock.id,
            transaction_type="buy",
            shares=shares,
            price_per_share=stock.current_price,
            total_amount=total_cost,
            executed_at=datetime.now(timezone.utc),
        )
        portfolio.cash_balance -= total_cost

        db.session.add(transaction)
        db.session.commit()

        return {
            "status": "success",
            "transaction": transaction.to_dict(),
            "remaining_cash": round(portfolio.cash_balance, 2),
        }

    @staticmethod
    def sell_stock(portfolio_id, symbol, shares):
        """Execute a sell transaction.

        Args:
            portfolio_id: ID of the portfolio.
            symbol: Stock ticker symbol.
            shares: Number of shares to sell.

        Returns:
            Dict with transaction details or error message.
        """
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return {"error": "Portfolio not found"}

        stock = Stock.query.filter_by(symbol=symbol.upper()).first()
        if not stock:
            return {"error": f"Stock {symbol} not found"}

        if shares <= 0:
            return {"error": "Shares must be positive"}

        # Check current position
        positions = PortfolioService.get_positions(portfolio.id)
        current_shares = 0
        for pos in positions:
            if pos["symbol"] == symbol.upper():
                current_shares = pos["shares"]
                break

        if shares > current_shares:
            return {"error": "Insufficient shares", "available": current_shares}

        total_proceeds = round(stock.current_price * shares, 2)

        transaction = Transaction(
            portfolio_id=portfolio.id,
            stock_id=stock.id,
            transaction_type="sell",
            shares=shares,
            price_per_share=stock.current_price,
            total_amount=total_proceeds,
            executed_at=datetime.now(timezone.utc),
        )
        portfolio.cash_balance += total_proceeds

        db.session.add(transaction)
        db.session.commit()

        return {
            "status": "success",
            "transaction": transaction.to_dict(),
            "remaining_cash": round(portfolio.cash_balance, 2),
        }

    @staticmethod
    def get_positions(portfolio_id):
        """Calculate current positions from transaction history.

        Aggregates all buy/sell transactions to compute net share count,
        average cost basis, and current market value per holding.

        Args:
            portfolio_id: ID of the portfolio.

        Returns:
            List of position dicts with P&L data.
        """
        transactions = Transaction.query.filter_by(portfolio_id=portfolio_id).all()
        positions = defaultdict(lambda: {"shares": 0.0, "total_cost": 0.0})

        for txn in transactions:
            symbol = txn.stock.symbol
            if txn.transaction_type == "buy":
                positions[symbol]["shares"] += txn.shares
                positions[symbol]["total_cost"] += txn.total_amount
            elif txn.transaction_type == "sell":
                if positions[symbol]["shares"] > 0:
                    avg_cost = positions[symbol]["total_cost"] / positions[symbol]["shares"]
                    positions[symbol]["shares"] -= txn.shares
                    positions[symbol]["total_cost"] = positions[symbol]["shares"] * avg_cost

        result = []
        for symbol, data in positions.items():
            if data["shares"] <= 0.0001:
                continue

            stock = Stock.query.filter_by(symbol=symbol).first()
            if not stock:
                continue

            avg_cost_basis = data["total_cost"] / data["shares"] if data["shares"] > 0 else 0
            market_value = round(stock.current_price * data["shares"], 2)
            unrealized_pnl = round(market_value - data["total_cost"], 2)
            pnl_percent = (
                round((unrealized_pnl / data["total_cost"]) * 100, 2)
                if data["total_cost"] > 0 else 0.0
            )

            result.append({
                "symbol": symbol,
                "name": stock.name,
                "shares": round(data["shares"], 4),
                "avg_cost_basis": round(avg_cost_basis, 2),
                "current_price": round(stock.current_price, 2),
                "market_value": market_value,
                "total_cost": round(data["total_cost"], 2),
                "unrealized_pnl": unrealized_pnl,
                "pnl_percent": pnl_percent,
            })

        return sorted(result, key=lambda x: x["market_value"], reverse=True)

    @staticmethod
    def get_allocation(portfolio_id):
        """Compute portfolio allocation percentages.

        Args:
            portfolio_id: ID of the portfolio.

        Returns:
            Dict with allocation data by stock and by sector.
        """
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return {"error": "Portfolio not found"}

        positions = PortfolioService.get_positions(portfolio_id)
        total_equity = sum(p["market_value"] for p in positions)
        total_value = total_equity + portfolio.cash_balance

        stock_allocation = []
        sector_totals = defaultdict(float)

        for pos in positions:
            pct = round((pos["market_value"] / total_value) * 100, 2) if total_value > 0 else 0
            stock_allocation.append({
                "symbol": pos["symbol"],
                "name": pos["name"],
                "market_value": pos["market_value"],
                "allocation_pct": pct,
            })
            stock = Stock.query.filter_by(symbol=pos["symbol"]).first()
            if stock:
                sector_totals[stock.sector] += pos["market_value"]

        sector_allocation = []
        for sector, value in sorted(sector_totals.items(), key=lambda x: x[1], reverse=True):
            pct = round((value / total_value) * 100, 2) if total_value > 0 else 0
            sector_allocation.append({
                "sector": sector,
                "market_value": round(value, 2),
                "allocation_pct": pct,
            })

        cash_pct = round((portfolio.cash_balance / total_value) * 100, 2) if total_value > 0 else 0

        return {
            "total_value": round(total_value, 2),
            "total_equity": round(total_equity, 2),
            "cash_balance": round(portfolio.cash_balance, 2),
            "cash_allocation_pct": cash_pct,
            "stock_allocation": stock_allocation,
            "sector_allocation": sector_allocation,
        }

    @staticmethod
    def get_performance(portfolio_id):
        """Calculate portfolio performance metrics.

        Args:
            portfolio_id: ID of the portfolio.

        Returns:
            Dict with performance metrics including total return, P&L.
        """
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return {"error": "Portfolio not found"}

        positions = PortfolioService.get_positions(portfolio_id)
        total_equity = sum(p["market_value"] for p in positions)
        total_value = total_equity + portfolio.cash_balance
        total_cost_basis = sum(p["total_cost"] for p in positions)

        total_unrealized_pnl = round(total_equity - total_cost_basis, 2)
        total_return_pct = (
            round(((total_value - portfolio.initial_value) / portfolio.initial_value) * 100, 2)
            if portfolio.initial_value > 0 else 0.0
        )

        # Realized P&L from sell transactions
        sell_txns = Transaction.query.filter_by(
            portfolio_id=portfolio_id, transaction_type="sell"
        ).all()
        realized_pnl = 0.0
        for txn in sell_txns:
            buy_txns = Transaction.query.filter_by(
                portfolio_id=portfolio_id,
                stock_id=txn.stock_id,
                transaction_type="buy",
            ).all()
            if buy_txns:
                total_bought = sum(t.shares for t in buy_txns)
                total_cost = sum(t.total_amount for t in buy_txns)
                avg_buy_price = total_cost / total_bought if total_bought > 0 else 0
                realized_pnl += (txn.price_per_share - avg_buy_price) * txn.shares

        best_performer = max(positions, key=lambda p: p["pnl_percent"]) if positions else None
        worst_performer = min(positions, key=lambda p: p["pnl_percent"]) if positions else None

        return {
            "total_value": round(total_value, 2),
            "initial_value": round(portfolio.initial_value, 2),
            "cash_balance": round(portfolio.cash_balance, 2),
            "total_equity": round(total_equity, 2),
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_realized_pnl": round(realized_pnl, 2),
            "total_return_pct": total_return_pct,
            "num_positions": len(positions),
            "best_performer": best_performer,
            "worst_performer": worst_performer,
        }

    @staticmethod
    def seed_portfolio():
        """Create a default portfolio with some initial positions."""
        portfolio = PortfolioService.get_or_create_portfolio()
        existing_txns = Transaction.query.filter_by(portfolio_id=portfolio.id).count()
        if existing_txns > 0:
            return portfolio

        seed_trades = [
            ("AAPL", 50), ("MSFT", 25), ("GOOGL", 40), ("AMZN", 30),
            ("NVDA", 20), ("JPM", 60), ("V", 35), ("JNJ", 45),
        ]

        for symbol, shares in seed_trades:
            stock = Stock.query.filter_by(symbol=symbol).first()
            if not stock:
                continue
            # Use a price slightly different from current for realistic P&L
            buy_price = round(stock.current_price * 0.92, 2)
            total_cost = round(buy_price * shares, 2)

            if total_cost > portfolio.cash_balance:
                continue

            txn = Transaction(
                portfolio_id=portfolio.id,
                stock_id=stock.id,
                transaction_type="buy",
                shares=shares,
                price_per_share=buy_price,
                total_amount=total_cost,
            )
            portfolio.cash_balance -= total_cost
            db.session.add(txn)

        db.session.commit()
        return portfolio
