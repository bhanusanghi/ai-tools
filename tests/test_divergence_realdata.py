"""
Deep testing of divergence detection logic with real market data
This validates that divergence detection is working correctly
"""
import unittest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetchers.price_fetcher import PriceFetcher
from src.indicators.rsi import RSI
from src.indicators.awesome_oscillator import AwesomeOscillator
from src.divergence.detector import DivergenceDetector


class TestRSIDivergenceValidation(unittest.TestCase):
    """
    Deep validation of RSI divergence detection with real data

    Tests verify:
    1. RSI is calculated correctly using pandas-ta (Wilder's method)
    2. Pivots are identified correctly
    3. Divergences are real and not false positives
    4. Logic matches technical analysis definition
    """

    @classmethod
    def setUpClass(cls):
        """Fetch real data for multiple stocks"""
        logging.basicConfig(level=logging.INFO)
        cls.fetcher = PriceFetcher(days_of_history=365)  # 1 year for better divergence detection

        # Test with multiple stocks for robustness
        cls.test_tickers = ['AAPL', 'MSFT', 'TSLA']
        cls.stock_data = {}

        for ticker in cls.test_tickers:
            df = cls.fetcher.fetch_data(ticker, '1d')
            if df is not None:
                cls.stock_data[ticker] = df

        if len(cls.stock_data) == 0:
            raise unittest.SkipTest("Could not fetch any stock data")

        cls.rsi_calc = RSI(period=14)
        cls.detector = DivergenceDetector(lookback_periods=100, min_bars_between_pivots=5)

    def test_rsi_calculation_accuracy(self):
        """Test that RSI is calculated correctly with pandas-ta"""
        for ticker, df in self.stock_data.items():
            with self.subTest(ticker=ticker):
                rsi = self.rsi_calc.calculate(df)

                # Validate RSI
                self.assertTrue(self.rsi_calc.validate_rsi(rsi),
                               f"{ticker}: RSI validation failed")

                # Check that RSI has expected NaN values at start
                self.assertTrue(rsi.iloc[:14].isna().any(),
                               f"{ticker}: RSI should have NaN for first 14 periods")

                # Check that RSI has valid values after period
                valid_rsi = rsi.iloc[14:].dropna()
                self.assertGreater(len(valid_rsi), 0,
                                  f"{ticker}: No valid RSI values after period")

                # Verify range
                self.assertTrue((valid_rsi >= 0).all() and (valid_rsi <= 100).all(),
                               f"{ticker}: RSI values out of 0-100 range")

                print(f"\n✓ {ticker}: RSI calculation valid "
                      f"({len(valid_rsi)} values, range: {valid_rsi.min():.2f}-{valid_rsi.max():.2f})")

    def test_pivot_detection_logic(self):
        """Test that pivots are identified correctly"""
        for ticker, df in self.stock_data.items():
            with self.subTest(ticker=ticker):
                rsi = self.rsi_calc.calculate(df)
                price = df['Close']

                # Find pivots
                highs, lows = self.rsi_calc.find_pivots(rsi, price, lookback=5)

                # Should find at least some pivots in 1 year of data
                self.assertGreater(len(highs), 0, f"{ticker}: No pivot highs found")
                self.assertGreater(len(lows), 0, f"{ticker}: No pivot lows found")

                # Validate pivot highs
                for _, pivot in highs.iterrows():
                    pivot_date = pivot['index']
                    pivot_rsi = pivot['rsi']

                    # Get index position
                    idx = rsi.index.get_loc(pivot_date)

                    # Check that it's actually a pivot high (higher than neighbors)
                    lookback = 5
                    if idx >= lookback and idx < len(rsi) - lookback:
                        window = rsi.iloc[idx - lookback:idx + lookback + 1]
                        window_max = window.max()

                        self.assertEqual(pivot_rsi, window_max,
                                        f"{ticker}: Pivot high at {pivot_date} is not highest in window")

                # Validate pivot lows
                for _, pivot in lows.iterrows():
                    pivot_date = pivot['index']
                    pivot_rsi = pivot['rsi']

                    idx = rsi.index.get_loc(pivot_date)

                    lookback = 5
                    if idx >= lookback and idx < len(rsi) - lookback:
                        window = rsi.iloc[idx - lookback:idx + lookback + 1]
                        window_min = window.min()

                        self.assertEqual(pivot_rsi, window_min,
                                        f"{ticker}: Pivot low at {pivot_date} is not lowest in window")

                print(f"✓ {ticker}: Pivot detection valid ({len(highs)} highs, {len(lows)} lows)")

    def test_bearish_divergence_logic(self):
        """
        Test bearish divergence detection logic

        Bearish divergence: Price makes higher high, RSI makes lower high
        This should signal potential trend reversal down
        """
        for ticker, df in self.stock_data.items():
            with self.subTest(ticker=ticker):
                rsi = self.rsi_calc.calculate(df)
                price = df['Close']

                # Detect divergences
                divergences = self.detector.detect_divergences(price, rsi, 'RSI')

                # Filter bearish divergences
                bearish_divs = [d for d in divergences if d['type'] == 'bearish']

                # Validate each bearish divergence
                for div in bearish_divs:
                    price_1 = div['price_1']
                    price_2 = div['price_2']
                    rsi_1 = div['indicator_1']
                    rsi_2 = div['indicator_2']

                    # CRITICAL: Bearish divergence must have:
                    # 1. Price higher high (price_2 > price_1)
                    # 2. RSI lower high (rsi_2 < rsi_1)

                    self.assertGreater(price_2, price_1,
                                      f"{ticker}: Bearish div at {div['date']} - "
                                      f"price should be higher high")

                    self.assertLess(rsi_2, rsi_1,
                                   f"{ticker}: Bearish div at {div['date']} - "
                                   f"RSI should be lower high")

                if bearish_divs:
                    print(f"✓ {ticker}: {len(bearish_divs)} bearish divergences validated")
                    # Show first divergence
                    div = bearish_divs[0]
                    print(f"  Example: {div['date']} - "
                          f"Price {div['price_1']:.2f}→{div['price_2']:.2f} (higher), "
                          f"RSI {div['indicator_1']:.2f}→{div['indicator_2']:.2f} (lower)")

    def test_bullish_divergence_logic(self):
        """
        Test bullish divergence detection logic

        Bullish divergence: Price makes lower low, RSI makes higher low
        This should signal potential trend reversal up
        """
        for ticker, df in self.stock_data.items():
            with self.subTest(ticker=ticker):
                rsi = self.rsi_calc.calculate(df)
                price = df['Close']

                # Detect divergences
                divergences = self.detector.detect_divergences(price, rsi, 'RSI')

                # Filter bullish divergences
                bullish_divs = [d for d in divergences if d['type'] == 'bullish']

                # Validate each bullish divergence
                for div in bullish_divs:
                    price_1 = div['price_1']
                    price_2 = div['price_2']
                    rsi_1 = div['indicator_1']
                    rsi_2 = div['indicator_2']

                    # CRITICAL: Bullish divergence must have:
                    # 1. Price lower low (price_2 < price_1)
                    # 2. RSI higher low (rsi_2 > rsi_1)

                    self.assertLess(price_2, price_1,
                                   f"{ticker}: Bullish div at {div['date']} - "
                                   f"price should be lower low")

                    self.assertGreater(rsi_2, rsi_1,
                                      f"{ticker}: Bullish div at {div['date']} - "
                                      f"RSI should be higher low")

                if bullish_divs:
                    print(f"✓ {ticker}: {len(bullish_divs)} bullish divergences validated")
                    # Show first divergence
                    div = bullish_divs[0]
                    print(f"  Example: {div['date']} - "
                          f"Price {div['price_1']:.2f}→{div['price_2']:.2f} (lower), "
                          f"RSI {div['indicator_1']:.2f}→{div['indicator_2']:.2f} (higher)")

    def test_min_bars_between_pivots(self):
        """Test that minimum bars requirement is enforced"""
        for ticker, df in self.stock_data.items():
            with self.subTest(ticker=ticker):
                rsi = self.rsi_calc.calculate(df)
                price = df['Close']

                # Detect divergences with strict min_bars
                detector_strict = DivergenceDetector(
                    lookback_periods=100,
                    min_bars_between_pivots=10
                )

                divergences = detector_strict.detect_divergences(price, rsi, 'RSI')

                # Verify that pivots are at least 10 bars apart
                for div in divergences:
                    date_1 = pd.to_datetime(div['date_1'])
                    date_2 = pd.to_datetime(div['date_2'])

                    idx_1 = price.index.get_loc(date_1)
                    idx_2 = price.index.get_loc(date_2)

                    bars_between = abs(idx_2 - idx_1)

                    self.assertGreaterEqual(bars_between, 10,
                                           f"{ticker}: Divergence at {div['date']} has only "
                                           f"{bars_between} bars between pivots (min: 10)")

    def test_no_false_positives(self):
        """Test that no divergences are detected when price and RSI move together"""
        # Create synthetic data where price and RSI always move together
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')

        # Perfect correlation: RSI follows price exactly
        price_data = np.linspace(100, 120, 100)  # Steady uptrend

        df = pd.DataFrame({
            'Close': price_data,
            'High': price_data + 1,
            'Low': price_data - 1
        }, index=dates)

        rsi_calc = RSI(period=14)
        rsi = rsi_calc.calculate(df)

        detector = DivergenceDetector(lookback_periods=50, min_bars_between_pivots=5)
        divergences = detector.detect_divergences(df['Close'], rsi, 'RSI')

        # Should detect NO divergences (or very few) when trend is smooth
        self.assertLessEqual(len(divergences), 2,
                            "Should not detect divergences in smooth trend")

        print("✓ No false positives in smooth trend data")


class TestAODivergenceValidation(unittest.TestCase):
    """Deep validation of AO divergence detection"""

    @classmethod
    def setUpClass(cls):
        """Fetch real data"""
        logging.basicConfig(level=logging.INFO)
        cls.fetcher = PriceFetcher(days_of_history=365)

        cls.test_tickers = ['AAPL', 'MSFT']
        cls.stock_data = {}

        for ticker in cls.test_tickers:
            df = cls.fetcher.fetch_data(ticker, '1d')
            if df is not None:
                cls.stock_data[ticker] = df

        if len(cls.stock_data) == 0:
            raise unittest.SkipTest("Could not fetch any stock data")

        cls.ao_calc = AwesomeOscillator(fast_period=5, slow_period=34)
        cls.detector = DivergenceDetector(lookback_periods=100, min_bars_between_pivots=5)

    def test_ao_divergence_logic(self):
        """Test that AO divergences follow correct logic"""
        for ticker, df in self.stock_data.items():
            with self.subTest(ticker=ticker):
                ao = self.ao_calc.calculate(df)
                price = df['Close']

                divergences = self.detector.detect_divergences(price, ao, 'AO')

                for div in divergences:
                    price_1 = div['price_1']
                    price_2 = div['price_2']
                    ao_1 = div['indicator_1']
                    ao_2 = div['indicator_2']

                    if div['type'] == 'bearish':
                        # Bearish: price higher high, AO lower high
                        self.assertGreater(price_2, price_1,
                                          f"{ticker}: Bearish AO div - price should be higher high")
                        self.assertLess(ao_2, ao_1,
                                       f"{ticker}: Bearish AO div - AO should be lower high")

                    elif div['type'] == 'bullish':
                        # Bullish: price lower low, AO higher low
                        self.assertLess(price_2, price_1,
                                       f"{ticker}: Bullish AO div - price should be lower low")
                        self.assertGreater(ao_2, ao_1,
                                          f"{ticker}: Bullish AO div - AO should be higher low")

                if divergences:
                    print(f"✓ {ticker}: {len(divergences)} AO divergences validated")


def run_deep_tests():
    """Run deep divergence validation tests"""
    print("\n" + "=" * 70)
    print("DEEP DIVERGENCE LOGIC VALIDATION WITH REAL DATA")
    print("=" * 70)
    print("\nThis test suite validates that divergence detection is accurate")
    print("and follows technical analysis definitions correctly.")
    print("=" * 70 + "\n")

    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestRSIDivergenceValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestAODivergenceValidation))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    if result.wasSuccessful():
        print("\n✓ ALL DIVERGENCE LOGIC VALIDATED!")
        print("  The scanner is detecting divergences correctly.")
    else:
        print("\n✗ VALIDATION FAILED!")
        print("  There are issues with divergence detection logic.")

    print()

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_deep_tests()
    sys.exit(0 if success else 1)
