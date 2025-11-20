#!/usr/bin/env python3
"""
Scheduler for running the divergence scanner automatically
"""
import schedule
import time
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scanner import DivergenceScanner
from src.utils.config_loader import Config


def run_scan():
    """Run the divergence scan"""
    print(f"\n{'=' * 60}")
    print(f"Running scheduled scan at {datetime.now()}")
    print(f"{'=' * 60}\n")

    try:
        config = Config('config.yaml')
        scanner = DivergenceScanner(config)
        results = scanner.run()

        if not results.empty:
            output_path = scanner.save_results(results)
            print(f"\nScan complete! Found {len(results)} divergences")
            print(f"Results saved to: {output_path}\n")
        else:
            print("\nScan complete. No divergences found.\n")

    except Exception as e:
        print(f"ERROR during scan: {e}")


def main():
    """Main scheduler loop"""
    # Load config
    try:
        config = Config('config.yaml')
    except FileNotFoundError:
        print("ERROR: config.yaml not found!")
        sys.exit(1)

    # Check if scheduler is enabled
    if not config.get('scheduler.enabled', False):
        print("Scheduler is not enabled in config.yaml")
        print("Set 'scheduler.enabled' to true to use the scheduler")
        sys.exit(1)

    # Get run time
    run_time = config.get('scheduler.run_time', '09:00')

    print(f"\n{'=' * 60}")
    print("Divergence Scanner Scheduler")
    print(f"{'=' * 60}")
    print(f"Scheduled to run daily at: {run_time}")
    print("Press Ctrl+C to stop")
    print(f"{'=' * 60}\n")

    # Schedule the job
    schedule.every().day.at(run_time).do(run_scan)

    # Optional: Run immediately on start
    print("Running initial scan...")
    run_scan()

    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\nScheduler stopped by user.")


if __name__ == "__main__":
    main()
