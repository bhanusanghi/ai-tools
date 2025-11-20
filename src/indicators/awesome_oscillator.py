"""Awesome Oscillator (AO) calculation"""
import pandas as pd
import numpy as np
from typing import Tuple


class AwesomeOscillator:
    """Calculate Awesome Oscillator"""

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

        Args:
            df: DataFrame with 'High' and 'Low' columns

        Returns:
            Series with AO values
        """
        if 'High' not in df.columns or 'Low' not in df.columns:
            raise ValueError("DataFrame must have 'High' and 'Low' columns")

        # Calculate median price
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

        Args:
            ao: AO series
            price: Price series
            lookback: Number of bars to look on each side for pivot

        Returns:
            Tuple of (pivot_highs, pivot_lows) DataFrames
        """
        # Find local maxima (pivot highs)
        pivot_highs = []
        for i in range(lookback, len(ao) - lookback):
            window = ao.iloc[i - lookback:i + lookback + 1]
            if ao.iloc[i] == window.max():
                pivot_highs.append({
                    'index': ao.index[i],
                    'ao': ao.iloc[i],
                    'price': price.iloc[i]
                })

        # Find local minima (pivot lows)
        pivot_lows = []
        for i in range(lookback, len(ao) - lookback):
            window = ao.iloc[i - lookback:i + lookback + 1]
            if ao.iloc[i] == window.min():
                pivot_lows.append({
                    'index': ao.index[i],
                    'ao': ao.iloc[i],
                    'price': price.iloc[i]
                })

        pivot_highs_df = pd.DataFrame(pivot_highs)
        pivot_lows_df = pd.DataFrame(pivot_lows)

        return pivot_highs_df, pivot_lows_df


# For testing/debugging
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    close = np.random.randn(100).cumsum() + 100

    data = pd.DataFrame({
        'High': close + np.random.rand(100),
        'Low': close - np.random.rand(100),
        'Close': close
    }, index=dates)

    # Calculate AO
    ao_calc = AwesomeOscillator()
    ao = ao_calc.calculate(data)

    print("Awesome Oscillator calculated:")
    print(ao.tail())

    # Find pivots
    highs, lows = ao_calc.find_pivots(ao, data['Close'])
    print(f"\nFound {len(highs)} pivot highs and {len(lows)} pivot lows")
