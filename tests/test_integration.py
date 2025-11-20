"""
Integration tests with real-time data
These tests actually fetch data from APIs and test the complete pipeline
"""
import unittest
import pandas as pd
import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_fetchers.index_fetcher import IndexFetcher
from src.data_fetchers.price_fetcher import PriceFetcher
from src.indicators.rsi import RSI
from src.indicators.awesome_oscillator import AwesomeOscillator
from src.divergence.detector import DivergenceDetector
from src.scanner import DivergenceScanner
from src.utils.config_loader import Config


class TestRealDataFetching(unittest.TestCase):
    """Test data fetching with real APIs"""

    def test_fetch_single_stock(self):
        """Test fetching data for a single well-known stock"""
        fetcher = PriceFetcher(days_of_history=60)
        df = fetcher.fetch_data("AAPL", "1d")

        self.assertIsNotNone(df, "Should fetch data for AAPL")
        self.assertFalse(df.empty, "Data should not be empty")

        # Verify required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            self.assertIn(col, df.columns, f"Should have {col} column")

        # Verify data makes sense
        self.assertGreater(len(df), 30, "Should have at least 30 days of data")
        self.assertTrue((df['Close'] > 0).all(), "Prices should be positive")
        self.assertTrue((df['Volume'] >= 0).all(), "Volume should be non-negative")

        print(f"\n✓ Fetched {len(df)} bars for AAPL")
        print(f"  Latest close: ${df['Close'].iloc[-1]:.2f}")

    def test_fetch_multiple_stocks(self):
        """Test fetching data for multiple stocks"""
        fetcher = PriceFetcher(days_of_history=60)
        tickers = ["AAPL", "MSFT", "GOOGL"]

        data = fetcher.fetch_multiple(tickers, "1d", show_progress=False)

        # Should successfully fetch most stocks
        self.assertGreater(len(data), 0, "Should fetch at least one stock")

        for ticker, df in data.items():
            self.assertFalse(df.empty, f"{ticker} data should not be empty")
            self.assertGreater(len(df), 30, f"{ticker} should have sufficient data")

        print(f"\n✓ Fetched data for {len(data)}/{len(tickers)} stocks")

    def test_fetch_index_constituents(self):
        """Test fetching index constituents (S&P 500)"""
        fetcher = IndexFetcher()

        # This hits Wikipedia API
        stocks = fetcher.get_stocks(['^GSPC'])

        self.assertIsNotNone(stocks, "Should fetch stock list")
        self.assertGreater(len(stocks), 400, "S&P 500 should have ~500 stocks")

        # Verify we got actual ticker symbols
        for ticker in stocks[:5]:
            self.assertTrue(isinstance(ticker, str), "Ticker should be string")
            self.assertGreater(len(ticker), 0, "Ticker should not be empty")

        print(f"\n✓ Fetched {len(stocks)} S&P 500 constituents")
        print(f"  Sample tickers: {stocks[:5]}")

    def test_3d_resampling(self):
        """Test resampling to 3-day timeframe"""
        fetcher = PriceFetcher(days_of_history=90)
        df = fetcher.fetch_data("AAPL", "1d")

        self.assertIsNotNone(df, "Should fetch daily data")

        # Resample to 3d
        df_3d = fetcher.resample_to_3d(df)

        self.assertFalse(df_3d.empty, "3d data should not be empty")
        self.assertLess(len(df_3d), len(df), "3d data should have fewer bars than daily")

        # Verify OHLCV
        self.assertIn('Close', df_3d.columns)
        self.assertTrue((df_3d['Close'] > 0).all())

        print(f"\n✓ Resampled from {len(df)} daily bars to {len(df_3d)} 3-day bars")


class TestRealIndicatorCalculations(unittest.TestCase):
    """Test indicator calculations with real data"""

    @classmethod
    def setUpClass(cls):
        """Fetch data once for all tests"""
        fetcher = PriceFetcher(days_of_history=180)
        cls.df = fetcher.fetch_data("AAPL", "1d")
        if cls.df is None:
            raise unittest.SkipTest("Could not fetch data for testing")

    def test_rsi_on_real_data(self):
        """Test RSI calculation on real stock data"""
        rsi_calc = RSI(period=14)
        rsi = rsi_calc.calculate(self.df)

        self.assertFalse(rsi.empty, "RSI should be calculated")

        # Verify RSI is in valid range
        rsi_valid = rsi.dropna()
        self.assertTrue((rsi_valid >= 0).all(), "RSI should be >= 0")
        self.assertTrue((rsi_valid <= 100).all(), "RSI should be <= 100")

        # Should have reasonable values (not all extreme)
        self.assertTrue(rsi_valid.mean() > 20, "Average RSI should be reasonable")
        self.assertTrue(rsi_valid.mean() < 80, "Average RSI should be reasonable")

        print(f"\n✓ RSI calculated on {len(self.df)} bars")
        print(f"  Latest RSI: {rsi.iloc[-1]:.2f}")
        print(f"  RSI range: {rsi_valid.min():.2f} - {rsi_valid.max():.2f}")

    def test_ao_on_real_data(self):
        """Test AO calculation on real stock data"""
        ao_calc = AwesomeOscillator(fast_period=5, slow_period=34)
        ao = ao_calc.calculate(self.df)

        self.assertFalse(ao.empty, "AO should be calculated")

        ao_valid = ao.dropna()
        self.assertGreater(len(ao_valid), 0, "Should have valid AO values")

        print(f"\n✓ AO calculated on {len(self.df)} bars")
        print(f"  Latest AO: {ao.iloc[-1]:.4f}")
        print(f"  AO range: {ao_valid.min():.4f} - {ao_valid.max():.4f}")

    def test_pivot_detection_on_real_data(self):
        """Test pivot detection on real stock data"""
        rsi_calc = RSI(period=14)
        rsi = rsi_calc.calculate(self.df)

        highs, lows = rsi_calc.find_pivots(rsi, self.df['Close'], lookback=5)

        # Should find some pivots in 180 days of data
        self.assertGreater(len(highs), 0, "Should find pivot highs")
        self.assertGreater(len(lows), 0, "Should find pivot lows")

        print(f"\n✓ Found {len(highs)} pivot highs and {len(lows)} pivot lows")


class TestRealDivergenceDetection(unittest.TestCase):
    """Test divergence detection on real data"""

    @classmethod
    def setUpClass(cls):
        """Fetch data once for all tests"""
        fetcher = PriceFetcher(days_of_history=180)
        cls.df = fetcher.fetch_data("AAPL", "1d")
        if cls.df is None:
            raise unittest.SkipTest("Could not fetch data for testing")

    def test_rsi_divergence_detection(self):
        """Test RSI divergence detection on real data"""
        rsi_calc = RSI(period=14)
        rsi = rsi_calc.calculate(self.df)

        detector = DivergenceDetector(lookback_periods=100, min_bars_between_pivots=5)
        divergences = detector.detect_divergences(self.df['Close'], rsi, 'RSI')

        # May or may not find divergences (depends on recent market)
        print(f"\n✓ RSI divergence detection completed")
        print(f"  Found {len(divergences)} divergences")

        if divergences:
            for div in divergences[:3]:  # Show first 3
                print(f"  - {div['type'].upper()} on {div['date']}")

    def test_ao_divergence_detection(self):
        """Test AO divergence detection on real data"""
        ao_calc = AwesomeOscillator(fast_period=5, slow_period=34)
        ao = ao_calc.calculate(self.df)

        detector = DivergenceDetector(lookback_periods=100, min_bars_between_pivots=5)
        divergences = detector.detect_divergences(self.df['Close'], ao, 'AO')

        print(f"\n✓ AO divergence detection completed")
        print(f"  Found {len(divergences)} divergences")

        if divergences:
            for div in divergences[:3]:  # Show first 3
                print(f"  - {div['type'].upper()} on {div['date']}")


class TestFullScannerIntegration(unittest.TestCase):
    """Test complete scanner with limited scope"""

    def test_small_scale_scan(self):
        """Test scanner with a small number of stocks"""
        # Create a minimal config
        config = Config('config.yaml')

        # Override to scan only a few stocks quickly
        config.config['indices'] = ['^GSPC']
        config.config['timeframes'] = ['1d']
        config.config['data']['days_of_history'] = 90

        # Create scanner
        scanner = DivergenceScanner(config)

        # Instead of full scan, just test a few tickers
        test_tickers = ['AAPL', 'MSFT', 'GOOGL']

        print(f"\n✓ Testing scanner with {len(test_tickers)} stocks...")

        # Fetch data
        data = scanner.price_fetcher.fetch_multiple(test_tickers, '1d', show_progress=False)

        self.assertGreater(len(data), 0, "Should fetch at least one stock")

        # Process one stock through full pipeline
        for ticker, df in list(data.items())[:1]:  # Just test one
            # Calculate RSI
            rsi = scanner.rsi_calculator.calculate(df)
            self.assertFalse(rsi.empty, "RSI should be calculated")

            # Detect divergences
            divs = scanner.divergence_detector.detect_divergences(df['Close'], rsi, 'RSI')

            print(f"  {ticker}: {len(divs)} divergence(s) found")

        print("✓ Scanner integration test passed")

    def test_config_loading(self):
        """Test that config loads correctly"""
        config = Config('config.yaml')

        self.assertIsNotNone(config.get_timeframes(), "Should load timeframes")
        self.assertIsNotNone(config.get_indices(), "Should load indices")
        self.assertIsNotNone(config.get('indicators.rsi.period'), "Should load RSI period")

        print("\n✓ Configuration loaded successfully")
        print(f"  Timeframes: {config.get_timeframes()}")
        print(f"  Indices: {config.get_indices()}")


class TestErrorHandling(unittest.TestCase):
    """Test error handling with invalid inputs"""

    def test_invalid_ticker(self):
        """Test handling of invalid ticker"""
        fetcher = PriceFetcher(days_of_history=60)
        df = fetcher.fetch_data("INVALID_TICKER_XYZ", "1d")

        # Should return None or empty DataFrame, not crash
        if df is not None:
            self.assertTrue(df.empty or len(df) == 0, "Should return empty data for invalid ticker")
        print("\n✓ Invalid ticker handled gracefully")

    def test_insufficient_data(self):
        """Test indicators with insufficient data"""
        # Create very short dataset
        df = pd.DataFrame({
            'Close': [100, 101, 102],
            'High': [101, 102, 103],
            'Low': [99, 100, 101]
        })

        rsi_calc = RSI(period=14)
        rsi = rsi_calc.calculate(df)

        # Should not crash, but RSI will be all NaN
        self.assertTrue(rsi.isna().all(), "RSI should be NaN with insufficient data")

        print("\n✓ Insufficient data handled gracefully")


def run_integration_tests():
    """Run integration tests with better output"""
    print("\n" + "=" * 60)
    print("Running Integration Tests with Real-Time Data")
    print("=" * 60)
    print("\nNote: These tests fetch real data from APIs.")
    print("Some tests may be slow due to network requests.")
    print("=" * 60 + "\n")

    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRealDataFetching))
    suite.addTests(loader.loadTestsFromTestCase(TestRealIndicatorCalculations))
    suite.addTests(loader.loadTestsFromTestCase(TestRealDivergenceDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestFullScannerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))

    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    print("Integration Test Summary")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 60 + "\n")

    return result.wasSuccessful()


if __name__ == '__main__':
    # Run integration tests
    success = run_integration_tests()
    sys.exit(0 if success else 1)
