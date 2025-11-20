"""
Unit tests for divergence detection
"""
import unittest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.divergence.detector import DivergenceDetector


class TestDivergenceDetector(unittest.TestCase):
    """Test divergence detection logic"""

    def setUp(self):
        """Set up test data"""
        self.detector = DivergenceDetector(
            lookback_periods=50,
            min_bars_between_pivots=5
        )

    def test_bearish_divergence(self):
        """Test detection of bearish divergence"""
        # Create clear bearish divergence:
        # Price: higher high
        # Indicator: lower high
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')

        # Price makes higher highs
        price_data = [100] * 20 + [105] * 10 + [102] * 20 + [108] * 10 + [103] * 40
        price = pd.Series(price_data, index=dates)

        # Indicator makes lower highs
        indicator_data = [50] * 20 + [60] * 10 + [52] * 20 + [55] * 10 + [50] * 40
        indicator = pd.Series(indicator_data, index=dates)

        divergences = self.detector.detect_divergences(price, indicator, 'TEST')

        # Should detect at least one bearish divergence
        bearish_divs = [d for d in divergences if d['type'] == 'bearish']
        self.assertGreater(len(bearish_divs), 0, "Should detect bearish divergence")

    def test_bullish_divergence(self):
        """Test detection of bullish divergence"""
        # Create clear bullish divergence:
        # Price: lower low
        # Indicator: higher low
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')

        # Price makes lower lows
        price_data = [100] * 20 + [95] * 10 + [98] * 20 + [92] * 10 + [97] * 40
        price = pd.Series(price_data, index=dates)

        # Indicator makes higher lows
        indicator_data = [50] * 20 + [40] * 10 + [48] * 20 + [45] * 10 + [50] * 40
        indicator = pd.Series(indicator_data, index=dates)

        divergences = self.detector.detect_divergences(price, indicator, 'TEST')

        # Should detect at least one bullish divergence
        bullish_divs = [d for d in divergences if d['type'] == 'bullish']
        self.assertGreater(len(bullish_divs), 0, "Should detect bullish divergence")

    def test_no_divergence(self):
        """Test with no divergence present"""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')

        # Both price and indicator move in same direction
        trend = np.linspace(100, 120, 100)
        price = pd.Series(trend, index=dates)
        indicator = pd.Series(trend / 2, index=dates)

        divergences = self.detector.detect_divergences(price, indicator, 'TEST')

        # Should detect few or no divergences
        self.assertEqual(len(divergences), 0, "Should not detect divergence when none exists")

    def test_find_pivots(self):
        """Test pivot finding"""
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')

        # Create data with clear peaks and troughs
        data = [100, 102, 105, 103, 101,  # Peak at 105
                99, 97, 95, 97, 99,       # Trough at 95
                101, 103, 106, 104, 102,  # Peak at 106
                100, 98, 94, 96, 98] + [100] * 30

        series = pd.Series(data, index=dates)

        highs, lows = self.detector._find_pivots(series, window=2)

        # Should find pivots
        self.assertGreater(len(highs), 0, "Should find pivot highs")
        self.assertGreater(len(lows), 0, "Should find pivot lows")

        # Verify pivot values
        if len(highs) > 0:
            # Pivot highs should include 105 and 106
            pivot_values = highs['value'].tolist()
            self.assertIn(105, pivot_values, "Should detect peak at 105")

        if len(lows) > 0:
            # Pivot lows should include 95
            pivot_values = lows['value'].tolist()
            self.assertTrue(any(v <= 96 for v in pivot_values), "Should detect trough near 95")

    def test_min_bars_between_pivots(self):
        """Test that minimum bars requirement is enforced"""
        detector = DivergenceDetector(
            lookback_periods=50,
            min_bars_between_pivots=10  # Require 10 bars minimum
        )

        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')

        # Create pivots that are too close together
        price_data = [100, 105, 100, 106, 100] * 20
        price = pd.Series(price_data, index=dates)

        indicator_data = [50, 60, 50, 55, 50] * 20
        indicator = pd.Series(indicator_data, index=dates)

        divergences = detector.detect_divergences(price, indicator, 'TEST')

        # Should detect fewer divergences due to min_bars requirement
        # (Some pivots are too close together)
        self.assertLessEqual(len(divergences), 5)


if __name__ == '__main__':
    unittest.main()
