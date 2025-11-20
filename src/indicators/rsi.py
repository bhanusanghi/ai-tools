"""RSI (Relative Strength Index) calculation"""
import pandas as pd
import numpy as np
from typing import Tuple


class RSI:
    """Calculate Relative Strength Index"""

    def __init__(self, period: int = 14):
        """
        Initialize RSI calculator

        Args:
            period: RSI period (default 14)
        """
        self.period = period

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate RSI for a DataFrame

        Args:
            df: DataFrame with 'Close' column

        Returns:
            Series with RSI values
        """
        if 'Close' not in df.columns:
            raise ValueError("DataFrame must have 'Close' column")

        close = df['Close']

        # Calculate price changes
        delta = close.diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate average gain and loss
        avg_gain = gain.rolling(window=self.period, min_periods=self.period).mean()
        avg_loss = loss.rolling(window=self.period, min_periods=self.period).mean()

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

        Args:
            rsi: RSI series
            price: Price series
            lookback: Number of bars to look on each side for pivot

        Returns:
            Tuple of (pivot_highs, pivot_lows) DataFrames
        """
        # Find local maxima (pivot highs)
        pivot_highs = []
        for i in range(lookback, len(rsi) - lookback):
            window = rsi.iloc[i - lookback:i + lookback + 1]
            if rsi.iloc[i] == window.max():
                pivot_highs.append({
                    'index': rsi.index[i],
                    'rsi': rsi.iloc[i],
                    'price': price.iloc[i]
                })

        # Find local minima (pivot lows)
        pivot_lows = []
        for i in range(lookback, len(rsi) - lookback):
            window = rsi.iloc[i - lookback:i + lookback + 1]
            if rsi.iloc[i] == window.min():
                pivot_lows.append({
                    'index': rsi.index[i],
                    'rsi': rsi.iloc[i],
                    'price': price.iloc[i]
                })

        pivot_highs_df = pd.DataFrame(pivot_highs)
        pivot_lows_df = pd.DataFrame(pivot_lows)

        return pivot_highs_df, pivot_lows_df


# For testing/debugging
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    data = pd.DataFrame({
        'Close': np.random.randn(100).cumsum() + 100
    }, index=dates)

    # Calculate RSI
    rsi_calc = RSI(period=14)
    rsi = rsi_calc.calculate(data)

    print("RSI calculated:")
    print(rsi.tail())

    # Find pivots
    highs, lows = rsi_calc.find_pivots(rsi, data['Close'])
    print(f"\nFound {len(highs)} pivot highs and {len(lows)} pivot lows")
