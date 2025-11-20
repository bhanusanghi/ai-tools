#!/usr/bin/env python3
"""
Stock Divergence Scanner
Main entry point for running the divergence scanner
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scanner import DivergenceScanner
from src.utils.config_loader import Config


def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print("Stock Divergence Scanner")
    print("=" * 60 + "\n")

    # Load configuration
    try:
        config = Config('config.yaml')
    except FileNotFoundError:
        print("ERROR: config.yaml not found!")
        print("Please ensure config.yaml exists in the current directory.")
        sys.exit(1)

    # Create and run scanner
    scanner = DivergenceScanner(config)
    results = scanner.run()

    # Save results
    if not results.empty:
        output_path = scanner.save_results(results)
        print(f"\n{'=' * 60}")
        print(f"SUCCESS! Found {len(results)} divergences")
        print(f"Results saved to: {output_path}")
        print(f"{'=' * 60}\n")

        # Print summary
        print("\nSummary by Type:")
        print(results.groupby('type').size())

        print("\nSummary by Timeframe:")
        print(results.groupby('timeframe').size())

        print("\nSummary by Indicator:")
        print(results.groupby('indicator').size())

        print("\nTop 10 Recent Divergences:")
        print(results[['ticker', 'timeframe', 'type', 'indicator', 'date', 'current_price']].head(10))

    else:
        print("\nNo divergences found in this scan.")

    print("\nScan complete!\n")


if __name__ == "__main__":
    main()
