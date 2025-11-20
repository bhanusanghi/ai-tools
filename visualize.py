#!/usr/bin/env python3
"""
Optional visualization tool for divergences
Requires matplotlib: pip install matplotlib
"""
import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def plot_divergence(ticker: str, timeframe: str = "1d", save: bool = True):
    """
    Plot price and indicators with divergence markers

    Args:
        ticker: Stock ticker
        timeframe: Timeframe to analyze
        save: Save plot to file
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("ERROR: matplotlib is required for visualization")
        print("Install with: pip install matplotlib")
        return

    from src.data_fetchers.price_fetcher import PriceFetcher
    from src.indicators.rsi import RSI
    from src.indicators.awesome_oscillator import AwesomeOscillator
    from src.divergence.detector import DivergenceDetector

    print(f"\nCreating divergence visualization for {ticker} ({timeframe})...")

    # Fetch data
    fetcher = PriceFetcher(days_of_history=180)
    df = fetcher.fetch_data(ticker, timeframe)

    if df is None or df.empty:
        print(f"Failed to fetch data for {ticker}")
        return

    # Calculate indicators
    rsi_calc = RSI()
    rsi = rsi_calc.calculate(df)

    ao_calc = AwesomeOscillator()
    ao = ao_calc.calculate(df)

    # Detect divergences
    detector = DivergenceDetector()
    rsi_divs = detector.detect_divergences(df['Close'], rsi, 'RSI')
    ao_divs = detector.detect_divergences(df['Close'], ao, 'AO')

    # Create figure with 3 subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

    # Plot 1: Price
    ax1.plot(df.index, df['Close'], label='Close Price', linewidth=1.5)
    ax1.set_ylabel('Price ($)', fontsize=10)
    ax1.set_title(f'{ticker} - Price and Divergence Analysis ({timeframe})', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Mark price divergence points
    for div in rsi_divs + ao_divs:
        date1 = pd.to_datetime(div['date_1'])
        date2 = pd.to_datetime(div['date_2'])
        price1 = div['price_1']
        price2 = div['price_2']

        color = 'green' if div['type'] == 'bullish' else 'red'
        ax1.plot([date1, date2], [price1, price2], color=color, linewidth=2, alpha=0.6)
        ax1.scatter([date1, date2], [price1, price2], color=color, s=50, zorder=5)

    # Plot 2: RSI
    ax2.plot(df.index, rsi, label='RSI', color='purple', linewidth=1.5)
    ax2.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='Overbought (70)')
    ax2.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='Oversold (30)')
    ax2.set_ylabel('RSI', fontsize=10)
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    # Mark RSI divergences
    for div in rsi_divs:
        date1 = pd.to_datetime(div['date_1'])
        date2 = pd.to_datetime(div['date_2'])
        rsi1 = div['indicator_1']
        rsi2 = div['indicator_2']

        color = 'green' if div['type'] == 'bullish' else 'red'
        ax2.plot([date1, date2], [rsi1, rsi2], color=color, linewidth=2, alpha=0.6)
        ax2.scatter([date1, date2], [rsi1, rsi2], color=color, s=50, zorder=5)
        ax2.annotate(div['type'].upper(), xy=(date2, rsi2), xytext=(5, 5),
                    textcoords='offset points', fontsize=8, color=color)

    # Plot 3: Awesome Oscillator
    colors = ['green' if x > 0 else 'red' for x in ao]
    ax3.bar(df.index, ao, label='Awesome Oscillator', color=colors, alpha=0.6, width=1)
    ax3.axhline(y=0, color='black', linewidth=0.8)
    ax3.set_ylabel('AO', fontsize=10)
    ax3.set_xlabel('Date', fontsize=10)
    ax3.grid(True, alpha=0.3)
    ax3.legend()

    # Mark AO divergences
    for div in ao_divs:
        date1 = pd.to_datetime(div['date_1'])
        date2 = pd.to_datetime(div['date_2'])
        ao1 = div['indicator_1']
        ao2 = div['indicator_2']

        color = 'green' if div['type'] == 'bullish' else 'red'
        ax3.plot([date1, date2], [ao1, ao2], color=color, linewidth=2, alpha=0.8)
        ax3.scatter([date1, date2], [ao1, ao2], color=color, s=50, zorder=5)
        ax3.annotate(div['type'].upper(), xy=(date2, ao2), xytext=(5, 5),
                    textcoords='offset points', fontsize=8, color=color)

    # Format x-axis
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)

    plt.tight_layout()

    if save:
        output_dir = Path('outputs')
        output_dir.mkdir(exist_ok=True)
        filename = f"{ticker}_{timeframe}_divergence.png"
        filepath = output_dir / filename
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        print(f"✓ Chart saved to: {filepath}")
    else:
        plt.show()

    # Print summary
    print(f"\nDivergence Summary for {ticker}:")
    print(f"  RSI divergences: {len(rsi_divs)}")
    print(f"  AO divergences: {len(ao_divs)}")

    if rsi_divs:
        print("\n  RSI Divergences:")
        for div in rsi_divs:
            print(f"    - {div['type'].upper()} on {div['date']}")

    if ao_divs:
        print("\n  AO Divergences:")
        for div in ao_divs:
            print(f"    - {div['type'].upper()} on {div['date']}")


def plot_multiple_from_csv(csv_path: str, max_plots: int = 5):
    """
    Plot multiple divergences from a CSV file

    Args:
        csv_path: Path to CSV file with scan results
        max_plots: Maximum number of plots to create
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR: matplotlib is required for visualization")
        print("Install with: pip install matplotlib")
        return

    df = pd.read_csv(csv_path)

    if df.empty:
        print("CSV file is empty")
        return

    print(f"\nFound {len(df)} divergences in {csv_path}")

    # Get unique ticker-timeframe combinations
    unique_combos = df.groupby(['ticker', 'timeframe']).size().reset_index()
    unique_combos = unique_combos.head(max_plots)

    print(f"Creating visualizations for top {len(unique_combos)} stocks...\n")

    for _, row in unique_combos.iterrows():
        ticker = row['ticker']
        timeframe = row['timeframe']
        plot_divergence(ticker, timeframe, save=True)

    print(f"\n✓ Created {len(unique_combos)} visualization(s)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Visualize stock divergences')
    parser.add_argument('--ticker', '-t', type=str, help='Stock ticker symbol')
    parser.add_argument('--timeframe', '-tf', type=str, default='1d', help='Timeframe (default: 1d)')
    parser.add_argument('--csv', '-c', type=str, help='Path to CSV file with scan results')
    parser.add_argument('--max-plots', '-m', type=int, default=5, help='Max plots from CSV (default: 5)')
    parser.add_argument('--show', '-s', action='store_true', help='Show plot instead of saving')

    args = parser.parse_args()

    if args.csv:
        # Plot from CSV
        plot_multiple_from_csv(args.csv, args.max_plots)
    elif args.ticker:
        # Plot single ticker
        plot_divergence(args.ticker, args.timeframe, save=not args.show)
    else:
        # Default: plot AAPL as example
        print("No arguments provided. Plotting AAPL as example...")
        print("Usage:")
        print("  python visualize.py --ticker AAPL --timeframe 1d")
        print("  python visualize.py --csv outputs/divergence_scan_*.csv")
        print()
        plot_divergence("AAPL", "1d", save=True)
