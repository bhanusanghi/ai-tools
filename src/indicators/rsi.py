"""RSI (Relative Strength Index) calculation using pandas-ta"""
import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class RSI:
    """Calculate Relative Strength Index using proper Wilder's smoothing"""

    def __init__(self, period: int = 14):
        """
        Initialize RSI calculator

        Args:
            period: RSI period (default 14)
        """
        self.period = period

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate RSI for a DataFrame using pandas-ta (Wilder's method)

        IMPORTANT: This uses the correct Wilder's smoothing method, not simple moving average.
        Wilder's RSI uses exponential smoothing with alpha = 1/period

        Args:
            df: DataFrame with 'Close' column

        Returns:
            Series with RSI values (0-100)
        """
        if 'Close' not in df.columns:
            raise ValueError("DataFrame must have 'Close' column")

        # Use pandas-ta for accurate RSI calculation (Wilder's method)
        rsi = ta.rsi(df['Close'], length=self.period)

        if rsi is None:
            logger.warning("RSI calculation returned None, using fallback method")
            rsi = self._calculate_rsi_manual(df['Close'])

        return rsi

    def _calculate_rsi_manual(self, close: pd.Series) -> pd.Series:
        """
        Manual RSI calculation using Wilder's smoothing method
        This is a fallback if pandas-ta fails

        Wilder's RSI formula:
        1. Calculate price changes (delta)
        2. Separate gains and losses
        3. Use exponential smoothing (Wilder's): avg = (prev_avg * (n-1) + current) / n
        4. RS = avg_gain / avg_loss
        5. RSI = 100 - (100 / (1 + RS))

        Args:
            close: Close price series

        Returns:
            RSI series
        """
        # Calculate price changes
        delta = close.diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        # Initialize first average using simple mean
        avg_gain = pd.Series(index=close.index, dtype='float64')
        avg_loss = pd.Series(index=close.index, dtype='float64')

        # First average is simple mean of first 'period' values
        avg_gain.iloc[self.period] = gain.iloc[1:self.period + 1].mean()
        avg_loss.iloc[self.period] = loss.iloc[1:self.period + 1].mean()

        # Apply Wilder's smoothing for subsequent values
        for i in range(self.period + 1, len(close)):
            avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (self.period - 1) + gain.iloc[i]) / self.period
            avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (self.period - 1) + loss.iloc[i]) / self.period

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def find_pivots(
        self,
        rsi: pd.Series,
        price: pd.Series,
        lookback: int = 5
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Find pivot highs and lows in RSI and price

        A pivot high is a peak where the value is higher than 'lookback' bars on each side
        A pivot low is a trough where the value is lower than 'lookback' bars on each side

        Args:
            rsi: RSI series
            price: Price series
            lookback: Number of bars to look on each side for pivot (default 5)

        Returns:
            Tuple of (pivot_highs, pivot_lows) DataFrames with columns:
            - index: datetime index
            - rsi: RSI value at pivot
            - price: price value at pivot
        """
        # Find local maxima (pivot highs)
        pivot_highs = []
        for i in range(lookback, len(rsi) - lookback):
            # Check if current RSI is the highest in the window
            is_pivot_high = True
            current_rsi = rsi.iloc[i]

            # Must be higher than all bars in the lookback window on both sides
            for j in range(i - lookback, i + lookback + 1):
                if j != i and rsi.iloc[j] >= current_rsi:
                    is_pivot_high = False
                    break

            if is_pivot_high and not pd.isna(current_rsi):
                pivot_highs.append({
                    'index': rsi.index[i],
                    'rsi': current_rsi,
                    'price': price.iloc[i]
                })

        # Find local minima (pivot lows)
        pivot_lows = []
        for i in range(lookback, len(rsi) - lookback):
            # Check if current RSI is the lowest in the window
            is_pivot_low = True
            current_rsi = rsi.iloc[i]

            # Must be lower than all bars in the lookback window on both sides
            for j in range(i - lookback, i + lookback + 1):
                if j != i and rsi.iloc[j] <= current_rsi:
                    is_pivot_low = False
                    break

            if is_pivot_low and not pd.isna(current_rsi):
                pivot_lows.append({
                    'index': rsi.index[i],
                    'rsi': current_rsi,
                    'price': price.iloc[i]
                })

        pivot_highs_df = pd.DataFrame(pivot_highs)
        pivot_lows_df = pd.DataFrame(pivot_lows)

        logger.debug(f"Found {len(pivot_highs_df)} RSI pivot highs and {len(pivot_lows_df)} pivot lows")

        return pivot_highs_df, pivot_lows_df

    def validate_rsi(self, rsi: pd.Series) -> bool:
        """
        Validate that RSI values are correct

        Args:
            rsi: RSI series to validate

        Returns:
            True if valid, False otherwise
        """
        if rsi is None or rsi.empty:
            logger.error("RSI is None or empty")
            return False

        # Check range (should be 0-100)
        valid_rsi = rsi.dropna()
        if len(valid_rsi) == 0:
            logger.error("All RSI values are NaN")
            return False

        if not ((valid_rsi >= 0).all() and (valid_rsi <= 100).all()):
            logger.error(f"RSI values out of range: min={valid_rsi.min()}, max={valid_rsi.max()}")
            return False

        # Should have NaN for first 'period' values
        if not rsi.iloc[:self.period].isna().any():
            logger.warning("RSI doesn't have expected NaN values at the start")

        logger.debug(f"RSI validation passed: {len(valid_rsi)} valid values")
        return True


# For testing/debugging
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add project root to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    logging.basicConfig(level=logging.DEBUG)

    # Test with real data
    print("\n" + "=" * 60)
    print("Testing RSI Calculation with pandas-ta")
    print("=" * 60)

    from src.data_fetchers.price_fetcher import PriceFetcher

    # Fetch real data
    fetcher = PriceFetcher(days_of_history=90)
    df = fetcher.fetch_data("AAPL", "1d")

    if df is not None:
        print(f"\nFetched {len(df)} bars for AAPL")

        # Calculate RSI using both methods
        rsi_calc = RSI(period=14)

        # Method 1: pandas-ta (recommended)
        rsi_pandasta = rsi_calc.calculate(df)

        # Method 2: manual calculation
        rsi_manual = rsi_calc._calculate_rsi_manual(df['Close'])

        print("\nRSI Comparison (last 10 values):")
        print("\nDate              Close     RSI(pandas-ta)  RSI(manual)   Diff")
        print("-" * 70)

        for i in range(-10, 0):
            date = df.index[i].strftime('%Y-%m-%d')
            close = df['Close'].iloc[i]
            rsi_pt = rsi_pandasta.iloc[i]
            rsi_m = rsi_manual.iloc[i]
            diff = abs(rsi_pt - rsi_m) if not (pd.isna(rsi_pt) or pd.isna(rsi_m)) else 0

            print(f"{date}  ${close:7.2f}   {rsi_pt:6.2f}         {rsi_m:6.2f}       {diff:5.2f}")

        # Validate
        if rsi_calc.validate_rsi(rsi_pandasta):
            print("\n✓ RSI validation passed!")

        # Find pivots
        highs, lows = rsi_calc.find_pivots(rsi_pandasta, df['Close'], lookback=5)
        print(f"\nFound {len(highs)} pivot highs and {len(lows)} pivot lows")

        if len(highs) > 0:
            print("\nRecent pivot highs:")
            print(highs.tail(3))

        if len(lows) > 0:
            print("\nRecent pivot lows:")
            print(lows.tail(3))

    else:
        print("Failed to fetch data")
