"""Fetch price data for stocks"""
import yfinance as yf
import pandas as pd
from typing import Optional, List
import logging
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class PriceFetcher:
    """Fetch historical price data for stocks"""

    def __init__(self, days_of_history: int = 180):
        """
        Initialize price fetcher

        Args:
            days_of_history: Number of days of historical data to fetch
        """
        self.days_of_history = days_of_history

    def fetch_data(
        self,
        ticker: str,
        interval: str = "1d",
        retry_count: int = 3
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical price data for a ticker

        Args:
            ticker: Stock ticker symbol
            interval: Data interval (1d, 1wk, 4h, etc.)
            retry_count: Number of retries on failure

        Returns:
            DataFrame with OHLCV data or None if failed
        """
        for attempt in range(retry_count):
            try:
                # Calculate period based on interval
                period = self._calculate_period(interval)

                # Fetch data
                stock = yf.Ticker(ticker)
                df = stock.history(period=period, interval=interval)

                if df.empty:
                    logger.warning(f"No data returned for {ticker} with interval {interval}")
                    return None

                # Clean column names (remove any extra spaces)
                df.columns = df.columns.str.strip()

                # Ensure we have required columns
                required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                if not all(col in df.columns for col in required_cols):
                    logger.error(f"Missing required columns for {ticker}")
                    return None

                logger.debug(f"Fetched {len(df)} bars for {ticker} ({interval})")
                return df

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{retry_count} failed for {ticker}: {e}")
                if attempt < retry_count - 1:
                    time.sleep(1)  # Wait before retry
                else:
                    logger.error(f"Failed to fetch data for {ticker} after {retry_count} attempts")
                    return None

        return None

    def fetch_multiple(
        self,
        tickers: List[str],
        interval: str = "1d",
        show_progress: bool = True
    ) -> dict:
        """
        Fetch data for multiple tickers

        Args:
            tickers: List of ticker symbols
            interval: Data interval
            show_progress: Show progress bar

        Returns:
            Dictionary mapping ticker to DataFrame
        """
        data = {}
        total = len(tickers)

        if show_progress:
            try:
                from tqdm import tqdm
                ticker_iter = tqdm(tickers, desc=f"Fetching {interval} data")
            except ImportError:
                ticker_iter = tickers
                logger.info(f"Fetching data for {total} tickers...")
        else:
            ticker_iter = tickers

        for ticker in ticker_iter:
            df = self.fetch_data(ticker, interval)
            if df is not None:
                data[ticker] = df
            # Small delay to avoid rate limiting
            time.sleep(0.1)

        logger.info(f"Successfully fetched data for {len(data)}/{total} tickers ({interval})")
        return data

    def _calculate_period(self, interval: str) -> str:
        """
        Calculate appropriate period based on interval

        Args:
            interval: Data interval

        Returns:
            Period string for yfinance
        """
        # For different intervals, we need different lookback periods
        interval_to_period = {
            '1m': '7d',
            '5m': '60d',
            '15m': '60d',
            '30m': '60d',
            '1h': '730d',
            '4h': '730d',  # 2 years for 4h data
            '1d': f'{self.days_of_history}d',
            '3d': f'{self.days_of_history * 2}d',  # Fetch more to ensure enough 3d bars
            '1wk': f'{self.days_of_history * 2}d',
            '1mo': '5y',
        }

        return interval_to_period.get(interval, f'{self.days_of_history}d')

    def resample_to_3d(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Resample daily data to 3-day timeframe

        Args:
            df: DataFrame with daily data

        Returns:
            Resampled DataFrame
        """
        if df.empty:
            return df

        # Resample to 3-day periods
        resampled = pd.DataFrame()
        resampled['Open'] = df['Open'].resample('3D').first()
        resampled['High'] = df['High'].resample('3D').max()
        resampled['Low'] = df['Low'].resample('3D').min()
        resampled['Close'] = df['Close'].resample('3D').last()
        resampled['Volume'] = df['Volume'].resample('3D').sum()

        # Drop rows with NaN values
        resampled = resampled.dropna()

        return resampled


# For testing/debugging
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetcher = PriceFetcher()

    # Test single ticker
    df = fetcher.fetch_data("AAPL", "1d")
    if df is not None:
        print(f"Fetched {len(df)} bars for AAPL")
        print(df.tail())

    # Test 3d resampling
    df_3d = fetcher.resample_to_3d(df)
    print(f"\n3-day resampled: {len(df_3d)} bars")
    print(df_3d.tail())
