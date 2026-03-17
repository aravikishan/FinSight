"""Tests for service layer business logic."""

import pytest

from services.market import MarketService


class TestMarketService:
    """Test MarketService technical indicator calculations."""

    def test_generate_ohlcv_length(self):
        """OHLCV generation produces correct number of trading days."""
        data = MarketService.generate_ohlcv(100.0, days=30, seed=42)
        # 30 calendar days minus weekends gives ~21 trading days
        assert len(data) > 15
        assert len(data) <= 30

    def test_generate_ohlcv_consistency(self):
        """OHLCV bars have consistent high >= close >= low."""
        data = MarketService.generate_ohlcv(100.0, days=100, seed=42)
        for bar in data:
            assert bar["high"] >= bar["close"], f"high < close on {bar['date']}"
            assert bar["high"] >= bar["open"], f"high < open on {bar['date']}"
            assert bar["low"] <= bar["close"], f"low > close on {bar['date']}"
            assert bar["low"] <= bar["open"], f"low > open on {bar['date']}"

    def test_generate_ohlcv_deterministic(self):
        """Same seed produces identical data."""
        data1 = MarketService.generate_ohlcv(100.0, days=50, seed=123)
        data2 = MarketService.generate_ohlcv(100.0, days=50, seed=123)
        assert data1 == data2

    def test_compute_sma(self):
        """SMA computation is correct for known values."""
        closes = [10, 11, 12, 13, 14, 15]
        sma = MarketService.compute_sma(closes, 3)
        assert sma[0] is None
        assert sma[1] is None
        assert sma[2] == pytest.approx(11.0)
        assert sma[3] == pytest.approx(12.0)
        assert sma[4] == pytest.approx(13.0)
        assert sma[5] == pytest.approx(14.0)

    def test_compute_ema(self):
        """EMA computation seeds with SMA and applies smoothing."""
        closes = [22, 22.27, 22.19, 22.08, 22.17, 22.18, 22.13, 22.23, 22.43, 22.24, 22.29]
        ema = MarketService.compute_ema(closes, 5)
        assert ema[0] is None
        assert ema[3] is None
        assert ema[4] is not None  # First EMA value (seeded with SMA)
        # All subsequent values should be computed
        for v in ema[4:]:
            assert v is not None

    def test_compute_rsi_bounds(self):
        """RSI values are between 0 and 100."""
        data = MarketService.generate_ohlcv(100.0, days=100, seed=42)
        closes = [bar["close"] for bar in data]
        rsi = MarketService.compute_rsi(closes)
        valid_values = [v for v in rsi if v is not None]
        assert len(valid_values) > 0
        for v in valid_values:
            assert 0 <= v <= 100, f"RSI out of bounds: {v}"

    def test_compute_macd_structure(self):
        """MACD returns dict with required keys."""
        data = MarketService.generate_ohlcv(100.0, days=100, seed=42)
        closes = [bar["close"] for bar in data]
        result = MarketService.compute_macd(closes)
        assert "macd_line" in result
        assert "signal_line" in result
        assert "histogram" in result
        assert len(result["macd_line"]) == len(closes)

    def test_compute_bollinger_bands(self):
        """Bollinger bands bracket the SMA correctly."""
        closes = list(range(30, 80))
        result = MarketService.compute_bollinger_bands(closes, period=20)
        # After initial period, upper > middle > lower
        for i in range(19, len(closes)):
            if result["upper"][i] is not None and result["lower"][i] is not None:
                assert result["upper"][i] >= result["middle"][i]
                assert result["lower"][i] <= result["middle"][i]

    def test_get_all_indicators(self):
        """get_all_indicators returns all expected keys."""
        data = MarketService.generate_ohlcv(100.0, days=100, seed=42)
        indicators = MarketService.get_all_indicators(data)
        assert "sma_20" in indicators
        assert "sma_50" in indicators
        assert "ema_12" in indicators
        assert "ema_26" in indicators
        assert "rsi" in indicators
        assert "macd" in indicators
        assert "bollinger" in indicators
