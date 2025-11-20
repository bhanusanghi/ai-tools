#!/usr/bin/env python3
"""
Test script to verify installation and dependencies
Run this to make sure everything is set up correctly
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test if all required packages are installed"""
    print("\n=== Testing Imports ===")

    imports = {
        'yfinance': 'yfinance',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'yaml': 'pyyaml',
        'ta': 'ta',
        'schedule': 'schedule',
        'requests': 'requests',
    }

    all_ok = True
    for module, package in imports.items():
        try:
            __import__(module)
            print(f"✓ {module} ({package})")
        except ImportError:
            print(f"✗ {module} ({package}) - MISSING")
            print(f"  Install with: pip install {package}")
            all_ok = False

    return all_ok


def test_project_structure():
    """Test if project structure is correct"""
    print("\n=== Testing Project Structure ===")

    required_dirs = [
        'src',
        'src/data_fetchers',
        'src/indicators',
        'src/divergence',
        'src/utils',
        'outputs',
        'logs',
    ]

    required_files = [
        'config.yaml',
        'requirements.txt',
        'main.py',
        'scheduler.py',
        'src/scanner.py',
        'src/data_fetchers/index_fetcher.py',
        'src/data_fetchers/price_fetcher.py',
        'src/indicators/rsi.py',
        'src/indicators/awesome_oscillator.py',
        'src/divergence/detector.py',
        'src/utils/config_loader.py',
        'src/utils/logger.py',
    ]

    all_ok = True

    # Check directories
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print(f"✓ {dir_path}/")
        else:
            print(f"✗ {dir_path}/ - MISSING")
            all_ok = False

    # Check files
    for file_path in required_files:
        path = Path(file_path)
        if path.exists() and path.is_file():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_ok = False

    return all_ok


def test_config():
    """Test if configuration is valid"""
    print("\n=== Testing Configuration ===")

    try:
        from src.utils.config_loader import Config
        config = Config('config.yaml')
        print("✓ config.yaml loaded successfully")

        # Test required config keys
        required_keys = [
            'indices',
            'timeframes',
            'indicators.rsi.enabled',
            'indicators.ao.enabled',
            'divergence.lookback_periods',
            'output.directory',
        ]

        for key in required_keys:
            value = config.get(key)
            if value is not None:
                print(f"✓ {key}: {value}")
            else:
                print(f"✗ {key} - MISSING")
                return False

        return True

    except Exception as e:
        print(f"✗ Error loading config: {e}")
        return False


def test_data_fetching():
    """Test if data fetching works"""
    print("\n=== Testing Data Fetching ===")

    try:
        from src.data_fetchers.price_fetcher import PriceFetcher

        print("Testing price data fetching for AAPL...")
        fetcher = PriceFetcher(days_of_history=30)
        df = fetcher.fetch_data("AAPL", "1d")

        if df is not None and not df.empty:
            print(f"✓ Successfully fetched {len(df)} bars for AAPL")
            print(f"  Latest close: ${df['Close'].iloc[-1]:.2f}")
            return True
        else:
            print("✗ Failed to fetch data")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_indicators():
    """Test if indicators calculation works"""
    print("\n=== Testing Indicators ===")

    try:
        from src.data_fetchers.price_fetcher import PriceFetcher
        from src.indicators.rsi import RSI
        from src.indicators.awesome_oscillator import AwesomeOscillator

        # Fetch data
        fetcher = PriceFetcher(days_of_history=60)
        df = fetcher.fetch_data("AAPL", "1d")

        if df is None:
            print("✗ Could not fetch data for testing")
            return False

        # Test RSI
        rsi_calc = RSI()
        rsi = rsi_calc.calculate(df)
        if not rsi.empty and not rsi.isna().all():
            print(f"✓ RSI calculation works (latest: {rsi.iloc[-1]:.2f})")
        else:
            print("✗ RSI calculation failed")
            return False

        # Test AO
        ao_calc = AwesomeOscillator()
        ao = ao_calc.calculate(df)
        if not ao.empty and not ao.isna().all():
            print(f"✓ AO calculation works (latest: {ao.iloc[-1]:.4f})")
        else:
            print("✗ AO calculation failed")
            return False

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_divergence_detection():
    """Test if divergence detection works"""
    print("\n=== Testing Divergence Detection ===")

    try:
        from src.data_fetchers.price_fetcher import PriceFetcher
        from src.indicators.rsi import RSI
        from src.divergence.detector import DivergenceDetector

        # Fetch data
        fetcher = PriceFetcher(days_of_history=180)
        df = fetcher.fetch_data("AAPL", "1d")

        if df is None:
            print("✗ Could not fetch data for testing")
            return False

        # Calculate RSI
        rsi_calc = RSI()
        rsi = rsi_calc.calculate(df)

        # Detect divergences
        detector = DivergenceDetector()
        divergences = detector.detect_divergences(df['Close'], rsi, 'RSI')

        print(f"✓ Divergence detection works (found {len(divergences)} divergences)")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Stock Divergence Scanner - Installation Test")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Project Structure", test_project_structure),
        ("Configuration", test_config),
        ("Data Fetching", test_data_fetching),
        ("Indicators", test_indicators),
        ("Divergence Detection", test_divergence_detection),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Unexpected error in {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ All tests passed! Your installation is ready.")
        print("\nNext steps:")
        print("  1. Review config.yaml and customize settings")
        print("  2. Run: python main.py")
        print("  3. Check outputs/ directory for results")
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Install missing packages: pip install -r requirements.txt")
        print("  - Ensure all files are present")
        print("  - Check config.yaml is valid")
        print("  - Verify internet connection for data fetching")

    print("\n")

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
