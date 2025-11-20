"""Main divergence scanner"""
import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
from typing import List, Dict
import time

from src.data_fetchers.index_fetcher import IndexFetcher
from src.data_fetchers.price_fetcher import PriceFetcher
from src.indicators.rsi import RSI
from src.indicators.awesome_oscillator import AwesomeOscillator
from src.divergence.detector import DivergenceDetector
from src.utils.config_loader import Config
from src.utils.logger import setup_logger
from src.notifications.telegram_notifier import TelegramNotifier

logger = logging.getLogger(__name__)


class DivergenceScanner:
    """Main scanner for detecting divergences across multiple stocks"""

    def __init__(self, config: Config):
        """
        Initialize scanner

        Args:
            config: Configuration object
        """
        self.config = config

        # Setup logging
        log_level = config.get('logging.level', 'INFO')
        log_dir = config.get_log_path()
        self.logger = setup_logger('divergence_scanner', log_dir, log_level)

        # Initialize components
        self.index_fetcher = IndexFetcher()
        self.price_fetcher = PriceFetcher(
            days_of_history=config.get('data.days_of_history', 180)
        )

        # Initialize indicators
        rsi_period = config.get('indicators.rsi.period', 14)
        ao_fast = config.get('indicators.ao.fast_period', 5)
        ao_slow = config.get('indicators.ao.slow_period', 34)

        self.rsi_calculator = RSI(period=rsi_period)
        self.ao_calculator = AwesomeOscillator(fast_period=ao_fast, slow_period=ao_slow)

        # Initialize divergence detector
        lookback = config.get('divergence.lookback_periods', 50)
        min_bars = config.get('divergence.min_bars_between_pivots', 5)
        self.divergence_detector = DivergenceDetector(
            lookback_periods=lookback,
            min_bars_between_pivots=min_bars
        )

        # Initialize Telegram notifier
        telegram_enabled = config.get('notifications.telegram.enabled', False)
        bot_token = config.get('notifications.telegram.bot_token', '')
        chat_id = config.get('notifications.telegram.chat_id', '')
        self.telegram_notifier = TelegramNotifier(bot_token, chat_id, telegram_enabled)

        # Test connection on startup if enabled
        if telegram_enabled and bot_token and chat_id:
            self.telegram_notifier.test_connection()

        self.results = []

    def run(self) -> pd.DataFrame:
        """
        Run the complete scan

        Returns:
            DataFrame with all detected divergences
        """
        start_time = time.time()

        self.logger.info("=" * 60)
        self.logger.info("Starting Divergence Scanner")
        self.logger.info("=" * 60)

        try:
            # Step 1: Get stock list
            indices = self.config.get_indices()
            self.logger.info(f"Fetching stocks from indices: {indices}")
            stocks = self.index_fetcher.get_stocks(indices)

            if not stocks:
                self.logger.error("No stocks found. Exiting.")
                if self.config.get('notifications.telegram.notify_on_errors', False):
                    self.telegram_notifier.send_error_alert("No stocks found in indices")
                return pd.DataFrame()

            self.logger.info(f"Total stocks to scan: {len(stocks)}")

            # Step 2: Scan each timeframe
            timeframes = self.config.get_timeframes()
            all_divergences = []

            for timeframe in timeframes:
                self.logger.info(f"\n{'=' * 60}")
                self.logger.info(f"Scanning timeframe: {timeframe}")
                self.logger.info(f"{'=' * 60}")

                divergences = self._scan_timeframe(stocks, timeframe)
                all_divergences.extend(divergences)

            # Step 3: Create results DataFrame
            scan_duration = time.time() - start_time

            if all_divergences:
                results_df = pd.DataFrame(all_divergences)
                self.logger.info(f"\n{'=' * 60}")
                self.logger.info(f"Scan complete! Found {len(results_df)} divergences")
                self.logger.info(f"{'=' * 60}")

                # Send Telegram notifications
                self._send_notifications(results_df, len(stocks), scan_duration)

                return results_df
            else:
                self.logger.info("No divergences found.")

                # Send scan summary even if no divergences
                if self.config.get('notifications.telegram.notify_on_scan_complete', False):
                    self.telegram_notifier.send_scan_summary(
                        len(stocks), 0, timeframes, scan_duration
                    )

                return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"Error during scan: {e}")
            if self.config.get('notifications.telegram.notify_on_errors', False):
                self.telegram_notifier.send_error_alert(f"Scan error: {str(e)}")
            raise

    def _scan_timeframe(self, stocks: List[str], timeframe: str) -> List[Dict]:
        """
        Scan a specific timeframe for all stocks

        Args:
            stocks: List of stock tickers
            timeframe: Timeframe to scan

        Returns:
            List of divergence dictionaries
        """
        divergences = []

        # Fetch data for all stocks
        self.logger.info(f"Fetching {timeframe} data for {len(stocks)} stocks...")
        stock_data = self.price_fetcher.fetch_multiple(stocks, interval=timeframe)

        self.logger.info(f"Successfully fetched data for {len(stock_data)} stocks")

        # Handle 3d timeframe (requires resampling)
        if timeframe == '3d':
            self.logger.info("Resampling to 3-day timeframe...")
            stock_data = {
                ticker: self.price_fetcher.resample_to_3d(df)
                for ticker, df in stock_data.items()
            }

        # Scan each stock
        rsi_enabled = self.config.get('indicators.rsi.enabled', True)
        ao_enabled = self.config.get('indicators.ao.enabled', True)

        for ticker, df in stock_data.items():
            try:
                # Skip if insufficient data
                if len(df) < 50:
                    continue

                stock_divergences = []

                # RSI divergences
                if rsi_enabled:
                    rsi = self.rsi_calculator.calculate(df)
                    rsi_divs = self.divergence_detector.detect_divergences(
                        df['Close'], rsi, 'RSI'
                    )
                    stock_divergences.extend(rsi_divs)

                # AO divergences
                if ao_enabled:
                    ao = self.ao_calculator.calculate(df)
                    ao_divs = self.divergence_detector.detect_divergences(
                        df['Close'], ao, 'AO'
                    )
                    stock_divergences.extend(ao_divs)

                # Add metadata to divergences
                for div in stock_divergences:
                    div['ticker'] = ticker
                    div['timeframe'] = timeframe
                    div['current_price'] = df['Close'].iloc[-1]
                    div['scan_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                divergences.extend(stock_divergences)

                if stock_divergences:
                    self.logger.info(
                        f"  {ticker}: Found {len(stock_divergences)} divergence(s)"
                    )

            except Exception as e:
                self.logger.error(f"  Error processing {ticker}: {e}")
                continue

        return divergences

    def _send_notifications(
        self,
        results_df: pd.DataFrame,
        total_stocks: int,
        scan_duration: float
    ) -> None:
        """
        Send Telegram notifications based on results

        Args:
            results_df: Results DataFrame
            total_stocks: Total number of stocks scanned
            scan_duration: Scan duration in seconds
        """
        if not self.telegram_notifier.enabled:
            return

        timeframes = self.config.get_timeframes()
        total_divergences = len(results_df)
        min_divs = self.config.get('notifications.telegram.min_divergences_to_notify', 1)

        # Send divergence alert if threshold met
        if (self.config.get('notifications.telegram.notify_on_divergences', True) and
            total_divergences >= min_divs):

            # Convert DataFrame to list of dicts
            divergences = results_df.to_dict('records')
            self.telegram_notifier.send_divergence_alert(divergences)

        # Send scan complete summary
        if self.config.get('notifications.telegram.notify_on_scan_complete', True):
            self.telegram_notifier.send_scan_summary(
                total_stocks,
                total_divergences,
                timeframes,
                scan_duration
            )

    def save_results(self, results_df: pd.DataFrame) -> Path:
        """
        Save results to CSV

        Args:
            results_df: Results DataFrame

        Returns:
            Path to saved file
        """
        if results_df.empty:
            self.logger.warning("No results to save")
            return None

        # Prepare output path
        output_dir = self.config.get_output_path()
        prefix = self.config.get('output.filename_prefix', 'divergence_scan')
        include_timestamp = self.config.get('output.include_timestamp', True)

        if include_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{prefix}_{timestamp}.csv"
        else:
            filename = f"{prefix}.csv"

        output_path = output_dir / filename

        # Select and order columns
        columns = [
            'ticker', 'timeframe', 'type', 'indicator', 'date',
            'current_price', 'price_1', 'price_2',
            'indicator_1', 'indicator_2', 'date_1', 'date_2',
            'scan_date'
        ]

        # Only include columns that exist
        available_columns = [col for col in columns if col in results_df.columns]
        results_df = results_df[available_columns]

        # Sort by date and ticker
        results_df = results_df.sort_values(['date', 'ticker'], ascending=[False, True])

        # Save to CSV
        results_df.to_csv(output_path, index=False)
        self.logger.info(f"\nResults saved to: {output_path}")

        return output_path


# For testing/debugging
if __name__ == "__main__":
    config = Config('config.yaml')
    scanner = DivergenceScanner(config)
    results = scanner.run()

    if not results.empty:
        output_path = scanner.save_results(results)
        print(f"\nResults saved to: {output_path}")
        print("\nSample results:")
        print(results.head())
