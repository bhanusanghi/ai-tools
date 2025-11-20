"""Divergence detection logic"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DivergenceDetector:
    """Detect divergences between price and indicators"""

    def __init__(
        self,
        lookback_periods: int = 50,
        min_bars_between_pivots: int = 5
    ):
        """
        Initialize divergence detector

        Args:
            lookback_periods: How many periods to look back for divergence
            min_bars_between_pivots: Minimum bars between pivot points
        """
        self.lookback_periods = lookback_periods
        self.min_bars_between_pivots = min_bars_between_pivots

    def detect_divergences(
        self,
        price: pd.Series,
        indicator: pd.Series,
        indicator_name: str = "Indicator"
    ) -> List[Dict]:
        """
        Detect divergences between price and indicator

        Args:
            price: Price series (typically Close)
            indicator: Indicator series (RSI, AO, etc.)
            indicator_name: Name of the indicator for reporting

        Returns:
            List of divergence dictionaries
        """
        divergences = []

        # Find pivot points
        price_highs, price_lows = self._find_pivots(price)
        ind_highs, ind_lows = self._find_pivots(indicator)

        # Detect bearish divergences (price makes higher high, indicator makes lower high)
        bearish_divs = self._detect_bearish_divergence(
            price_highs, ind_highs, price, indicator, indicator_name
        )
        divergences.extend(bearish_divs)

        # Detect bullish divergences (price makes lower low, indicator makes higher low)
        bullish_divs = self._detect_bullish_divergence(
            price_lows, ind_lows, price, indicator, indicator_name
        )
        divergences.extend(bullish_divs)

        return divergences

    def _find_pivots(self, series: pd.Series, window: int = 5) -> tuple:
        """
        Find pivot highs and lows in a series

        Args:
            series: Data series
            window: Window size for pivot detection

        Returns:
            Tuple of (pivot_highs_df, pivot_lows_df)
        """
        pivot_highs = []
        pivot_lows = []

        for i in range(window, len(series) - window):
            # Check for pivot high
            is_high = True
            for j in range(i - window, i + window + 1):
                if j != i and series.iloc[j] >= series.iloc[i]:
                    is_high = False
                    break

            if is_high:
                pivot_highs.append({
                    'index': series.index[i],
                    'position': i,
                    'value': series.iloc[i]
                })

            # Check for pivot low
            is_low = True
            for j in range(i - window, i + window + 1):
                if j != i and series.iloc[j] <= series.iloc[i]:
                    is_low = False
                    break

            if is_low:
                pivot_lows.append({
                    'index': series.index[i],
                    'position': i,
                    'value': series.iloc[i]
                })

        return pd.DataFrame(pivot_highs), pd.DataFrame(pivot_lows)

    def _detect_bearish_divergence(
        self,
        price_highs: pd.DataFrame,
        ind_highs: pd.DataFrame,
        price: pd.Series,
        indicator: pd.Series,
        indicator_name: str
    ) -> List[Dict]:
        """
        Detect bearish divergences

        Bearish divergence occurs when:
        - Price makes a higher high
        - Indicator makes a lower high
        """
        divergences = []

        if price_highs.empty or ind_highs.empty or len(price_highs) < 2 or len(ind_highs) < 2:
            return divergences

        # Get recent pivots within lookback period
        recent_cutoff = price.index[-1] - pd.Timedelta(days=self.lookback_periods)
        recent_price_highs = price_highs[price_highs['index'] >= recent_cutoff]

        # Compare consecutive pivot highs
        for i in range(len(recent_price_highs) - 1):
            for j in range(i + 1, len(recent_price_highs)):
                pivot1 = recent_price_highs.iloc[i]
                pivot2 = recent_price_highs.iloc[j]

                # Check if enough bars between pivots
                bars_between = abs(pivot2['position'] - pivot1['position'])
                if bars_between < self.min_bars_between_pivots:
                    continue

                # Price makes higher high
                if pivot2['value'] > pivot1['value']:
                    # Find corresponding indicator pivots
                    ind_pivot1 = self._find_nearest_pivot(pivot1['index'], ind_highs)
                    ind_pivot2 = self._find_nearest_pivot(pivot2['index'], ind_highs)

                    # Indicator makes lower high (divergence!)
                    if ind_pivot1 is not None and ind_pivot2 is not None:
                        if ind_pivot2['value'] < ind_pivot1['value']:
                            divergences.append({
                                'type': 'bearish',
                                'indicator': indicator_name,
                                'date': pivot2['index'],
                                'price_1': pivot1['value'],
                                'price_2': pivot2['value'],
                                'indicator_1': ind_pivot1['value'],
                                'indicator_2': ind_pivot2['value'],
                                'date_1': pivot1['index'],
                                'date_2': pivot2['index']
                            })

        return divergences

    def _detect_bullish_divergence(
        self,
        price_lows: pd.DataFrame,
        ind_lows: pd.DataFrame,
        price: pd.Series,
        indicator: pd.Series,
        indicator_name: str
    ) -> List[Dict]:
        """
        Detect bullish divergences

        Bullish divergence occurs when:
        - Price makes a lower low
        - Indicator makes a higher low
        """
        divergences = []

        if price_lows.empty or ind_lows.empty or len(price_lows) < 2 or len(ind_lows) < 2:
            return divergences

        # Get recent pivots within lookback period
        recent_cutoff = price.index[-1] - pd.Timedelta(days=self.lookback_periods)
        recent_price_lows = price_lows[price_lows['index'] >= recent_cutoff]

        # Compare consecutive pivot lows
        for i in range(len(recent_price_lows) - 1):
            for j in range(i + 1, len(recent_price_lows)):
                pivot1 = recent_price_lows.iloc[i]
                pivot2 = recent_price_lows.iloc[j]

                # Check if enough bars between pivots
                bars_between = abs(pivot2['position'] - pivot1['position'])
                if bars_between < self.min_bars_between_pivots:
                    continue

                # Price makes lower low
                if pivot2['value'] < pivot1['value']:
                    # Find corresponding indicator pivots
                    ind_pivot1 = self._find_nearest_pivot(pivot1['index'], ind_lows)
                    ind_pivot2 = self._find_nearest_pivot(pivot2['index'], ind_lows)

                    # Indicator makes higher low (divergence!)
                    if ind_pivot1 is not None and ind_pivot2 is not None:
                        if ind_pivot2['value'] > ind_pivot1['value']:
                            divergences.append({
                                'type': 'bullish',
                                'indicator': indicator_name,
                                'date': pivot2['index'],
                                'price_1': pivot1['value'],
                                'price_2': pivot2['value'],
                                'indicator_1': ind_pivot1['value'],
                                'indicator_2': ind_pivot2['value'],
                                'date_1': pivot1['index'],
                                'date_2': pivot2['index']
                            })

        return divergences

    def _find_nearest_pivot(
        self,
        target_date: pd.Timestamp,
        pivots: pd.DataFrame,
        max_distance_days: int = 10
    ) -> Optional[Dict]:
        """
        Find the nearest pivot to a target date

        Args:
            target_date: Target date
            pivots: DataFrame of pivots
            max_distance_days: Maximum days distance to consider

        Returns:
            Pivot dict or None
        """
        if pivots.empty:
            return None

        # Calculate time differences
        time_diffs = abs(pivots['index'] - target_date)

        # Find minimum
        min_idx = time_diffs.argmin()
        min_diff = time_diffs.iloc[min_idx]

        # Check if within acceptable distance
        if min_diff <= pd.Timedelta(days=max_distance_days):
            return pivots.iloc[min_idx].to_dict()

        return None


# For testing/debugging
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create sample data with divergence
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    np.random.seed(42)

    # Create price with higher highs
    price_data = np.random.randn(100).cumsum() + 100

    # Create indicator with lower highs (bearish divergence)
    indicator_data = np.random.randn(100).cumsum() + 50

    price = pd.Series(price_data, index=dates)
    indicator = pd.Series(indicator_data, index=dates)

    # Detect divergences
    detector = DivergenceDetector()
    divergences = detector.detect_divergences(price, indicator, "TestIndicator")

    print(f"Found {len(divergences)} divergences")
    for div in divergences:
        print(f"{div['type'].upper()} divergence on {div['date']}")
