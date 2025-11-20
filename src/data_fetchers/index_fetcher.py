"""Fetch constituent stocks from various indices"""
import pandas as pd
import requests
from typing import List
import logging

logger = logging.getLogger(__name__)


class IndexFetcher:
    """Fetch stocks from various indices"""

    # Mapping of index symbols to their constituent sources
    INDEX_SOURCES = {
        "^GSPC": "sp500",      # S&P 500
        "^NDX": "nasdaq100",   # NASDAQ 100
        "^DJI": "dow30",       # Dow Jones 30
        "^RUT": "russell2000"  # Russell 2000 (partial)
    }

    def get_stocks(self, indices: List[str]) -> List[str]:
        """
        Get list of stocks from specified indices

        Args:
            indices: List of index symbols (e.g., ['^GSPC', '^NDX'])

        Returns:
            List of unique stock tickers
        """
        all_stocks = set()

        for index in indices:
            logger.info(f"Fetching constituents for {index}")
            try:
                stocks = self._fetch_index_constituents(index)
                all_stocks.update(stocks)
                logger.info(f"Found {len(stocks)} stocks in {index}")
            except Exception as e:
                logger.error(f"Failed to fetch constituents for {index}: {e}")

        stock_list = sorted(list(all_stocks))
        logger.info(f"Total unique stocks: {len(stock_list)}")
        return stock_list

    def _fetch_index_constituents(self, index: str) -> List[str]:
        """
        Fetch constituents for a specific index

        Args:
            index: Index symbol

        Returns:
            List of stock tickers
        """
        index_type = self.INDEX_SOURCES.get(index)

        if index_type == "sp500":
            return self._fetch_sp500()
        elif index_type == "nasdaq100":
            return self._fetch_nasdaq100()
        elif index_type == "dow30":
            return self._fetch_dow30()
        elif index_type == "russell2000":
            logger.warning("Russell 2000 constituents not fully supported, using subset")
            return []
        else:
            logger.warning(f"Unknown index: {index}")
            return []

    def _fetch_sp500(self) -> List[str]:
        """Fetch S&P 500 constituents from Wikipedia"""
        try:
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(url)
            df = tables[0]
            tickers = df['Symbol'].str.replace('.', '-').tolist()
            return tickers
        except Exception as e:
            logger.error(f"Failed to fetch S&P 500 constituents: {e}")
            return []

    def _fetch_nasdaq100(self) -> List[str]:
        """Fetch NASDAQ 100 constituents from Wikipedia"""
        try:
            url = "https://en.wikipedia.org/wiki/Nasdaq-100"
            tables = pd.read_html(url)
            # The constituents table is usually the 4th table
            df = tables[4]
            tickers = df['Ticker'].str.replace('.', '-').tolist()
            return tickers
        except Exception as e:
            logger.error(f"Failed to fetch NASDAQ 100 constituents: {e}")
            # Fallback: try alternative table index
            try:
                df = tables[3]
                tickers = df['Ticker'].str.replace('.', '-').tolist()
                return tickers
            except:
                return []

    def _fetch_dow30(self) -> List[str]:
        """Fetch Dow Jones 30 constituents from Wikipedia"""
        try:
            url = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
            tables = pd.read_html(url)
            df = tables[1]  # Usually the second table
            tickers = df['Symbol'].str.replace('.', '-').tolist()
            return tickers
        except Exception as e:
            logger.error(f"Failed to fetch Dow 30 constituents: {e}")
            return []


# For testing/debugging
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetcher = IndexFetcher()
    stocks = fetcher.get_stocks(['^GSPC'])
    print(f"Found {len(stocks)} stocks")
    print(stocks[:10])
