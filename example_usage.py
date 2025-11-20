#!/usr/bin/env python3
"""
Example usage of the divergence scanner
This shows how to use the scanner programmatically
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scanner import DivergenceScanner
from src.utils.config_loader import Config


def example_basic_scan():
    """Example: Basic scan with default configuration"""
    print("\n=== Example 1: Basic Scan ===\n")

    config = Config('config.yaml')
    scanner = DivergenceScanner(config)
    results = scanner.run()

    if not results.empty:
        print(f"\nFound {len(results)} divergences")
        print("\nFirst 5 results:")
        print(results.head())

        # Save results
        output_path = scanner.save_results(results)
        print(f"\nSaved to: {output_path}")
    else:
        print("No divergences found")


def example_custom_config():
    """Example: Scan with custom configuration"""
    print("\n=== Example 2: Custom Configuration ===\n")

    # You can also modify config programmatically
    config = Config('config.yaml')

    # Override some settings
    config.config['timeframes'] = ['1d']  # Only daily
    config.config['indices'] = ['^GSPC']  # Only S&P 500

    scanner = DivergenceScanner(config)
    results = scanner.run()

    print(f"\nFound {len(results)} divergences")


def example_filter_results():
    """Example: Filter and analyze results"""
    print("\n=== Example 3: Filter and Analyze Results ===\n")

    config = Config('config.yaml')
    scanner = DivergenceScanner(config)
    results = scanner.run()

    if results.empty:
        print("No divergences found")
        return

    # Filter bullish divergences only
    bullish = results[results['type'] == 'bullish']
    print(f"\nBullish divergences: {len(bullish)}")

    # Filter bearish divergences only
    bearish = results[results['type'] == 'bearish']
    print(f"Bearish divergences: {len(bearish)}")

    # Filter by indicator
    rsi_divs = results[results['indicator'] == 'RSI']
    print(f"\nRSI divergences: {len(rsi_divs)}")

    ao_divs = results[results['indicator'] == 'AO']
    print(f"AO divergences: {len(ao_divs)}")

    # Filter by timeframe
    daily_divs = results[results['timeframe'] == '1d']
    print(f"\nDaily divergences: {len(daily_divs)}")

    # Get top 10 most recent
    recent = results.sort_values('date', ascending=False).head(10)
    print("\nTop 10 most recent divergences:")
    print(recent[['ticker', 'type', 'indicator', 'timeframe', 'date']])

    # Save filtered results
    bullish.to_csv('outputs/bullish_only.csv', index=False)
    print("\nSaved bullish divergences to: outputs/bullish_only.csv")


def example_single_stock():
    """Example: Analyze a single stock"""
    print("\n=== Example 4: Single Stock Analysis ===\n")

    from src.data_fetchers.price_fetcher import PriceFetcher
    from src.indicators.rsi import RSI
    from src.indicators.awesome_oscillator import AwesomeOscillator
    from src.divergence.detector import DivergenceDetector

    # Fetch data for a single stock
    ticker = "AAPL"
    print(f"Analyzing {ticker}...")

    fetcher = PriceFetcher()
    df = fetcher.fetch_data(ticker, "1d")

    if df is None:
        print(f"Failed to fetch data for {ticker}")
        return

    print(f"Fetched {len(df)} bars")

    # Calculate indicators
    rsi_calc = RSI()
    rsi = rsi_calc.calculate(df)

    ao_calc = AwesomeOscillator()
    ao = ao_calc.calculate(df)

    # Detect divergences
    detector = DivergenceDetector()

    rsi_divs = detector.detect_divergences(df['Close'], rsi, 'RSI')
    ao_divs = detector.detect_divergences(df['Close'], ao, 'AO')

    print(f"\n{ticker} RSI divergences: {len(rsi_divs)}")
    print(f"{ticker} AO divergences: {len(ao_divs)}")

    # Print details
    if rsi_divs:
        print("\nRSI Divergences:")
        for div in rsi_divs:
            print(f"  {div['type'].upper()} on {div['date']}")


def example_export_formats():
    """Example: Export results in different formats"""
    print("\n=== Example 5: Export to Different Formats ===\n")

    config = Config('config.yaml')
    scanner = DivergenceScanner(config)
    results = scanner.run()

    if results.empty:
        print("No divergences found")
        return

    # CSV (default)
    results.to_csv('outputs/divergences.csv', index=False)
    print("Saved CSV: outputs/divergences.csv")

    # JSON
    results.to_json('outputs/divergences.json', orient='records', indent=2)
    print("Saved JSON: outputs/divergences.json")

    # Excel (requires openpyxl: pip install openpyxl)
    try:
        results.to_excel('outputs/divergences.xlsx', index=False)
        print("Saved Excel: outputs/divergences.xlsx")
    except ImportError:
        print("Excel export requires: pip install openpyxl")

    # HTML table
    results.to_html('outputs/divergences.html', index=False)
    print("Saved HTML: outputs/divergences.html")


def example_statistics():
    """Example: Calculate statistics from results"""
    print("\n=== Example 6: Statistics and Summary ===\n")

    config = Config('config.yaml')
    scanner = DivergenceScanner(config)
    results = scanner.run()

    if results.empty:
        print("No divergences found")
        return

    print("Summary Statistics:")
    print("=" * 50)

    # Count by type
    print("\nBy Divergence Type:")
    print(results['type'].value_counts())

    # Count by indicator
    print("\nBy Indicator:")
    print(results['indicator'].value_counts())

    # Count by timeframe
    print("\nBy Timeframe:")
    print(results['timeframe'].value_counts())

    # Top stocks with most divergences
    print("\nTop 10 Stocks with Most Divergences:")
    print(results['ticker'].value_counts().head(10))

    # Recent divergences (last 7 days)
    import pandas as pd
    results['date'] = pd.to_datetime(results['date'])
    last_week = pd.Timestamp.now() - pd.Timedelta(days=7)
    recent = results[results['date'] >= last_week]
    print(f"\nDivergences in last 7 days: {len(recent)}")


if __name__ == "__main__":
    # Run all examples
    examples = [
        ("Basic Scan", example_basic_scan),
        ("Custom Config", example_custom_config),
        ("Filter Results", example_filter_results),
        ("Single Stock", example_single_stock),
        ("Export Formats", example_export_formats),
        ("Statistics", example_statistics),
    ]

    print("\n" + "=" * 60)
    print("Stock Divergence Scanner - Example Usage")
    print("=" * 60)

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nRunning all examples... (this may take a while)")
    print("=" * 60)

    # Run each example
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\nError in {name}: {e}")

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60 + "\n")
