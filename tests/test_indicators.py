"""
Unit tests for technical indicators
"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.indicators.rsi import RSI
from src.indicators.awesome_oscillator import AwesomeOscillator


class TestRSI(unittest.TestCase):
    """Test RSI indicator calculations"""

    def setUp(self):
        """Set up test data"""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        # Create trending data with some volatility
        trend = np.linspace(100, 120, 100)
        noise = np.random.randn(100) * 2
        self.df = pd.DataFrame({
            'Close': trend + noise
        }, index=dates)
        self.rsi_calc = RSI(period=14)

    def test_rsi_calculation(self):
        """Test that RSI is calculated correctly"""
        rsi = self.rsi_calc.calculate(self.df)

        # RSI should be between 0 and 100
        self.assertTrue((rsi.dropna() >= 0).all())
        self.assertTrue((rsi.dropna() <= 100).all())

        # First 14 values should be NaN (period = 14)
        self.assertTrue(rsi.iloc[:14].isna().all())

        # Should have values after the period
        self.assertFalse(rsi.iloc[14:].isna().all())

    def test_rsi_with_all_gains(self):
        """Test RSI with all positive changes"""
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        df = pd.DataFrame({
            'Close': np.arange(100, 130, 1)  # All gains
        }, index=dates)

        rsi = self.rsi_calc.calculate(df)

        # With all gains, RSI should approach 100
        self.assertGreater(rsi.iloc[-1], 90)

    def test_rsi_with_all_losses(self):
        """Test RSI with all negative changes"""
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        df = pd.DataFrame({
            'Close': np.arange(130, 100, -1)  # All losses
        }, index=dates)

        rsi = self.rsi_calc.calculate(df)

        # With all losses, RSI should approach 0
        self.assertLess(rsi.iloc[-1], 10)

    def test_find_pivots(self):
        """Test pivot detection"""
        # Create data with clear highs and lows
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        prices = [100, 102, 105, 103, 101,  # High at 105
                  99, 97, 95, 97, 99,       # Low at 95
                  101, 103, 106, 104, 102,  # High at 106
                  100] + [100] * 34

        df = pd.DataFrame({'Close': prices}, index=dates[:len(prices)])
        rsi = self.rsi_calc.calculate(df)

        highs, lows = self.rsi_calc.find_pivots(rsi, df['Close'], lookback=2)

        # Should find some pivots
        self.assertGreater(len(highs), 0)
        self.assertGreater(len(lows), 0)


class TestAwesomeOscillator(unittest.TestCase):
    """Test Awesome Oscillator calculations"""

    def setUp(self):
        """Set up test data"""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        close = np.linspace(100, 120, 100) + np.random.randn(100) * 2

        self.df = pd.DataFrame({
            'High': close + np.random.rand(100) * 2,
            'Low': close - np.random.rand(100) * 2,
            'Close': close
        }, index=dates)

        self.ao_calc = AwesomeOscillator(fast_period=5, slow_period=34)

    def test_ao_calculation(self):
        """Test that AO is calculated correctly"""
        ao = self.ao_calc.calculate(self.df)

        # Should have NaN for first slow_period-1 values
        self.assertTrue(ao.iloc[:33].isna().all())

        # Should have values after the slow period
        self.assertFalse(ao.iloc[34:].isna().all())

    def test_ao_uptrend(self):
        """Test AO in strong uptrend"""
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        close = np.arange(100, 150, 1)  # Strong uptrend

        df = pd.DataFrame({
            'High': close + 1,
            'Low': close - 1,
            'Close': close
        }, index=dates)

        ao = self.ao_calc.calculate(df)

        # In uptrend, AO should be mostly positive
        self.assertGreater(ao.iloc[-1], 0)

    def test_ao_downtrend(self):
        """Test AO in strong downtrend"""
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        close = np.arange(150, 100, -1)  # Strong downtrend

        df = pd.DataFrame({
            'High': close + 1,
            'Low': close - 1,
            'Close': close
        }, index=dates)

        ao = self.ao_calc.calculate(df)

        # In downtrend, AO should be mostly negative
        self.assertLess(ao.iloc[-1], 0)

    def test_find_pivots(self):
        """Test pivot detection for AO"""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        close = np.sin(np.linspace(0, 4 * np.pi, 100)) * 10 + 100  # Oscillating

        df = pd.DataFrame({
            'High': close + 1,
            'Low': close - 1,
            'Close': close
        }, index=dates)

        ao = self.ao_calc.calculate(df)

        highs, lows = self.ao_calc.find_pivots(ao, df['Close'], lookback=3)

        # Oscillating data should have pivots
        self.assertGreater(len(highs), 0)
        self.assertGreater(len(lows), 0)


if __name__ == '__main__':
    unittest.main()
