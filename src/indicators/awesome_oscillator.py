"""Awesome Oscillator (AO) calculation using pandas-ta"""
import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class AwesomeOscillator:
    """Calculate Awesome Oscillator (Bill Williams indicator)"""

    def __init__(self, fast_period: int = 5, slow_period: int = 34):
        """
        Initialize Awesome Oscillator calculator

        Args:
            fast_period: Fast SMA period (default 5)
            slow_period: Slow SMA period (default 34)
        """
        self.fast_period = fast_period
        self.slow_period = slow_period

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate Awesome Oscillator for a DataFrame

        The AO is the difference between a 5-period and 34-period simple moving average
        of the median price (High + Low) / 2

        Formula: SMA(median_price, 5) - SMA(median_price, 34)

        Args:
            df: DataFrame with 'High' and 'Low' columns

        Returns:
            Series with AO values
        """
        if 'High' not in df.columns or 'Low' not in df.columns:
            raise ValueError("DataFrame must have 'High' and 'Low' columns")

        # Use pandas-ta for AO calculation
        ao = ta.ao(df['High'], df['Low'], fast=self.fast_period, slow=self.slow_period)

        if ao is None:
            logger.warning("AO calculation returned None, using manual method")
            ao = self._calculate_ao_manual(df)

        return ao

    def _calculate_ao_manual(self, df: pd.DataFrame) -> pd.Series:
        """
        Manual AO calculation (fallback if pandas-ta fails)

        Args:
            df: DataFrame with 'High' and 'Low' columns

        Returns:
            AO series
        """
        # Calculate median price (HL/2)
        median_price = (df['High'] + df['Low']) / 2

        # Calculate SMAs
        sma_fast = median_price.rolling(window=self.fast_period).mean()
        sma_slow = median_price.rolling(window=self.slow_period).mean()

        # Calculate AO
        ao = sma_fast - sma_slow

        return ao

    def find_pivots(
        self,
        ao: pd.Series,
        price: pd.Series,
        lookback: int = 5
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Find pivot highs and lows in AO and price

        A pivot high is a peak where the value is higher than 'lookback' bars on each side
        A pivot low is a trough where the value is lower than 'lookback' bars on each side

        Args:
            ao: AO series
            price: Price series
            lookback: Number of bars to look on each side for pivot (default 5)

        Returns:
            Tuple of (pivot_highs, pivot_lows) DataFrames with columns:
            - index: datetime index
            - ao: AO value at pivot
            - price: price value at pivot
        """
        # Find local maxima (pivot highs)
        pivot_highs = []
        for i in range(lookback, len(ao) - lookback):
            is_pivot_high = True
            current_ao = ao.iloc[i]

            # Must be higher than all bars in the lookback window on both sides
            for j in range(i - lookback, i + lookback + 1):
                if j != i and ao.iloc[j] >= current_ao:
                    is_pivot_high = False
                    break

            if is_pivot_high and not pd.isna(current_ao):
                pivot_highs.append({
                    'index': ao.index[i],
                    'ao': current_ao,
                    'price': price.iloc[i]
                })

        # Find local minima (pivot lows)
        pivot_lows = []
        for i in range(lookback, len(ao) - lookback):
            is_pivot_low = True
            current_ao = ao.iloc[i]

            # Must be lower than all bars in the lookback window on both sides
            for j in range(i - lookback, i + lookback + 1):
                if j != i and ao.iloc[j] <= current_ao:
                    is_pivot_low = False
                    break

            if is_pivot_low and not pd.isna(current_ao):
                pivot_lows.append({
                    'index': ao.index[i],
                    'ao': current_ao,
                    'price': price.iloc[i]
                })

        pivot_highs_df = pd.DataFrame(pivot_highs)
        pivot_lows_df = pd.DataFrame(pivot_lows)

        logger.debug(f"Found {len(pivot_highs_df)} AO pivot highs and {len(pivot_lows_df)} pivot lows")

        return pivot_highs_df, pivot_lows_df


# For testing/debugging
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add project root to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    logging.basicConfig(level=logging.DEBUG)

    # Test with real data
    print("\n" + "=" * 60)
    print("Testing AO Calculation with pandas-ta")
    print("=" * 60)

    from src.data_fetchers.price_fetcher import PriceFetcher

    # Fetch real data
    fetcher = PriceFetcher(days_of_history=90)
    df = fetcher.fetch_data("AAPL", "1d")

    if df is not None:
        print(f"\nFetched {len(df)} bars for AAPL")

        # Calculate AO using both methods
        ao_calc = AwesomeOscillator(fast_period=5, slow_period=34)

        # Method 1: pandas-ta (recommended)
        ao_pandasta = ao_calc.calculate(df)

        # Method 2: manual calculation
        ao_manual = ao_calc._calculate_ao_manual(df)

        print("\nAO Comparison (last 10 values):")
        print("\nDate              Close     AO(pandas-ta)  AO(manual)    Diff")
        print("-" * 70)

        for i in range(-10, 0):
            date = df.index[i].strftime('%Y-%m-%d')
            close = df['Close'].iloc[i]
            ao_pt = ao_pandasta.iloc[i]
            ao_m = ao_manual.iloc[i]
            diff = abs(ao_pt - ao_m) if not (pd.isna(ao_pt) or pd.isna(ao_m)) else 0

            print(f"{date}  ${close:7.2f}   {ao_pt:7.4f}        {ao_m:7.4f}      {diff:6.4f}")

        # Find pivots
        highs, lows = ao_calc.find_pivots(ao_pandasta, df['Close'], lookback=5)
        print(f"\nFound {len(highs)} pivot highs and {len(lows)} pivot lows")

        if len(highs) > 0:
            print("\nRecent pivot highs:")
            print(highs.tail(3))

        if len(lows) > 0:
            print("\nRecent pivot lows:")
            print(lows.tail(3))

    else:
        print("Failed to fetch data")
