# Stock Divergence Scanner - Architecture Documentation

## Overview

The Stock Divergence Scanner is a Python-based tool designed to automatically detect technical analysis divergences (RSI and Awesome Oscillator) across stocks from major indices like S&P 500 and NASDAQ 100.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   main.py    │  │ scheduler.py │  │visualize.py  │      │
│  │  (CLI Run)   │  │(Automation)  │  │  (Charts)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Core Scanner Layer                         │
│                   (src/scanner.py)                           │
│  - Orchestrates entire scan process                          │
│  - Manages workflow and error handling                       │
│  - Generates CSV output                                      │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│Data Fetching │  │  Indicators  │  │  Divergence  │
│    Layer     │  │    Layer     │  │  Detection   │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│Index Fetcher │  │     RSI      │  │   Detector   │
│Price Fetcher │  │      AO      │  │   (Logic)    │
└──────────────┘  └──────────────┘  └──────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                  External Data Sources                       │
│  - yfinance (Yahoo Finance) - Free, no API key              │
│  - Wikipedia (Index constituents) - Web scraping            │
│  - Alpha Vantage (Optional) - For 4h data                   │
└─────────────────────────────────────────────────────────────┘
```

## Module Breakdown

### 1. Data Fetchers (`src/data_fetchers/`)

#### IndexFetcher (`index_fetcher.py`)
**Purpose:** Fetch constituent stocks from various indices

**Key Methods:**
- `get_stocks(indices)`: Main entry point to get stock list
- `_fetch_sp500()`: Fetch S&P 500 from Wikipedia
- `_fetch_nasdaq100()`: Fetch NASDAQ 100 from Wikipedia
- `_fetch_dow30()`: Fetch Dow Jones 30 from Wikipedia

**Data Source:** Wikipedia tables (via pandas.read_html)

**Output:** List of stock ticker symbols

#### PriceFetcher (`price_fetcher.py`)
**Purpose:** Fetch historical OHLCV data for stocks

**Key Methods:**
- `fetch_data(ticker, interval)`: Fetch data for single ticker
- `fetch_multiple(tickers, interval)`: Fetch data for multiple tickers
- `resample_to_3d(df)`: Resample daily data to 3-day timeframe

**Data Source:** yfinance library (Yahoo Finance API)

**Supported Intervals:**
- 4h (4-hour intraday)
- 1d (daily)
- 3d (resampled from daily)
- 1wk (weekly)

**Output:** pandas DataFrame with columns: Open, High, Low, Close, Volume

### 2. Indicators (`src/indicators/`)

#### RSI (`rsi.py`)
**Purpose:** Calculate Relative Strength Index

**Algorithm:**
```
1. Calculate price changes (delta)
2. Separate gains and losses
3. Calculate average gain and loss over period (default 14)
4. RS = average_gain / average_loss
5. RSI = 100 - (100 / (1 + RS))
```

**Key Methods:**
- `calculate(df)`: Calculate RSI values
- `find_pivots(rsi, price)`: Find local highs and lows

**Output:** pandas Series with RSI values (0-100)

#### Awesome Oscillator (`awesome_oscillator.py`)
**Purpose:** Calculate Awesome Oscillator (Bill Williams)

**Algorithm:**
```
1. Calculate median price = (High + Low) / 2
2. Calculate 5-period SMA of median price
3. Calculate 34-period SMA of median price
4. AO = SMA(5) - SMA(34)
```

**Key Methods:**
- `calculate(df)`: Calculate AO values
- `find_pivots(ao, price)`: Find local highs and lows

**Output:** pandas Series with AO values

### 3. Divergence Detection (`src/divergence/`)

#### DivergenceDetector (`detector.py`)
**Purpose:** Detect divergences between price and indicators

**Divergence Types:**

**Bullish Divergence (Buy Signal):**
- Price makes lower low
- Indicator makes higher low
- Suggests downtrend weakening

**Bearish Divergence (Sell Signal):**
- Price makes higher high
- Indicator makes lower high
- Suggests uptrend weakening

**Algorithm:**
```
1. Find pivot points in price series
2. Find pivot points in indicator series
3. Compare consecutive pivots:
   - For bearish: price higher high + indicator lower high
   - For bullish: price lower low + indicator higher low
4. Match price pivots with nearest indicator pivots
5. Validate minimum distance between pivots
```

**Key Methods:**
- `detect_divergences(price, indicator)`: Main detection logic
- `_find_pivots(series)`: Find pivot highs and lows
- `_detect_bearish_divergence()`: Detect bearish divergences
- `_detect_bullish_divergence()`: Detect bullish divergences

**Configuration:**
- `lookback_periods`: How far back to look (default: 50)
- `min_bars_between_pivots`: Minimum distance between pivots (default: 5)

### 4. Utilities (`src/utils/`)

#### ConfigLoader (`config_loader.py`)
**Purpose:** Load and manage YAML configuration

**Key Methods:**
- `get(key)`: Get config value with dot notation
- `get_timeframes()`: Get list of timeframes
- `get_indices()`: Get list of indices
- `get_output_path()`: Get output directory path

#### Logger (`logger.py`)
**Purpose:** Set up logging infrastructure

**Features:**
- Dual output (console + file)
- Configurable log levels
- Daily log files
- Structured formatting

### 5. Core Scanner (`src/scanner.py`)

#### DivergenceScanner
**Purpose:** Main orchestrator that ties everything together

**Workflow:**
```
1. Load configuration
2. Fetch stock list from indices
3. For each timeframe:
   a. Fetch price data for all stocks
   b. For each stock:
      - Calculate RSI (if enabled)
      - Calculate AO (if enabled)
      - Detect RSI divergences
      - Detect AO divergences
   c. Aggregate results
4. Generate CSV output
5. Log summary statistics
```

**Key Methods:**
- `run()`: Execute complete scan
- `_scan_timeframe(stocks, timeframe)`: Scan specific timeframe
- `save_results(results_df)`: Save to CSV

## Data Flow

### Complete Scan Flow

```
main.py
  │
  ├─→ Load config.yaml
  │
  ├─→ Create DivergenceScanner
  │
  └─→ scanner.run()
        │
        ├─→ IndexFetcher.get_stocks()
        │     │
        │     ├─→ Wikipedia scraping (S&P 500, NASDAQ 100)
        │     └─→ Returns: ['AAPL', 'MSFT', ...]
        │
        ├─→ For each timeframe:
        │     │
        │     ├─→ PriceFetcher.fetch_multiple()
        │     │     │
        │     │     ├─→ yfinance API calls
        │     │     └─→ Returns: {ticker: DataFrame}
        │     │
        │     ├─→ For each stock:
        │     │     │
        │     │     ├─→ RSI.calculate()
        │     │     │     └─→ Returns: RSI series
        │     │     │
        │     │     ├─→ AO.calculate()
        │     │     │     └─→ Returns: AO series
        │     │     │
        │     │     ├─→ DivergenceDetector.detect_divergences()
        │     │     │     │
        │     │     │     ├─→ Find price pivots
        │     │     │     ├─→ Find indicator pivots
        │     │     │     ├─→ Match and compare pivots
        │     │     │     └─→ Returns: List[Divergence]
        │     │     │
        │     │     └─→ Aggregate divergences
        │     │
        │     └─→ Combine all divergences
        │
        ├─→ Create DataFrame from all divergences
        │
        └─→ save_results()
              │
              └─→ outputs/divergence_scan_TIMESTAMP.csv
```

## Configuration System

### Config Schema

```yaml
indices:              # List of index symbols
  - "^GSPC"          # S&P 500
  - "^NDX"           # NASDAQ 100

timeframes:          # List of timeframes to scan
  - "4h"
  - "1d"
  - "1wk"

indicators:
  rsi:
    enabled: true    # Enable RSI divergences
    period: 14       # RSI calculation period
  ao:
    enabled: true    # Enable AO divergences
    fast_period: 5   # Fast SMA period
    slow_period: 34  # Slow SMA period

divergence:
  lookback_periods: 50           # How far back to look
  min_bars_between_pivots: 5    # Min distance between pivots
  detect_bullish: true           # Detect bullish divergences
  detect_bearish: true           # Detect bearish divergences

data:
  days_of_history: 180          # Days of historical data

output:
  directory: "outputs"           # Output directory
  filename_prefix: "divergence_scan"
  include_timestamp: true        # Add timestamp to filename

logging:
  level: "INFO"                  # Log level
  directory: "logs"              # Log directory
```

## Output Format

### CSV Columns

| Column | Type | Description |
|--------|------|-------------|
| ticker | string | Stock ticker symbol |
| timeframe | string | Timeframe (4h, 1d, 3d, 1wk) |
| type | string | Divergence type (bullish/bearish) |
| indicator | string | Indicator used (RSI/AO) |
| date | datetime | Date of divergence |
| current_price | float | Current stock price |
| price_1 | float | Price at first pivot |
| price_2 | float | Price at second pivot |
| indicator_1 | float | Indicator value at first pivot |
| indicator_2 | float | Indicator value at second pivot |
| date_1 | datetime | Date of first pivot |
| date_2 | datetime | Date of second pivot |
| scan_date | datetime | When scan was performed |

## Performance Considerations

### Optimization Strategies

1. **Parallel Data Fetching**
   - Uses batch fetching with small delays
   - Progress bars for user feedback
   - Retry logic for failed requests

2. **Caching**
   - No explicit caching (future enhancement)
   - Could cache index constituents (update weekly)
   - Could cache price data (update daily)

3. **Rate Limiting**
   - 0.1s delay between stock fetches
   - Prevents API rate limiting
   - Can be adjusted based on data source

### Scalability

**Current Scale:**
- ~500 stocks (S&P 500)
- ~4 timeframes
- ~2 indicators
- ~2000 API calls per full scan
- ~10-15 minutes per full scan

**Bottlenecks:**
1. API rate limits (yfinance)
2. Network latency
3. Divergence detection computation

**Scaling Strategies:**
1. Use multiprocessing for parallel stock processing
2. Implement caching layer
3. Use paid APIs with higher rate limits
4. Process only stocks with recent volume spikes

## Error Handling

### Levels of Error Handling

1. **Data Fetching Errors**
   - Retry mechanism (3 attempts)
   - Skip failed stocks
   - Log warnings
   - Continue with available data

2. **Calculation Errors**
   - Try-catch around each stock
   - Log error with ticker
   - Continue with next stock

3. **Configuration Errors**
   - Fail fast on startup
   - Validate config schema
   - Provide clear error messages

### Logging Strategy

- **DEBUG**: Detailed calculation steps
- **INFO**: Progress updates, results summary
- **WARNING**: Skipped stocks, missing data
- **ERROR**: Fatal errors, configuration issues

## Extension Points

### Adding New Indicators

1. Create new file in `src/indicators/`
2. Implement `calculate(df)` method
3. Add to scanner in `_scan_timeframe()`
4. Add config options in `config.yaml`

### Adding New Data Sources

1. Create new fetcher in `src/data_fetchers/`
2. Implement same interface as `PriceFetcher`
3. Update scanner to use new fetcher
4. Add API key configuration if needed

### Adding New Export Formats

1. Modify `save_results()` in scanner.py
2. Use pandas export methods:
   - `to_excel()` for Excel
   - `to_json()` for JSON
   - `to_sql()` for databases

## Security Considerations

1. **API Keys**
   - Stored in config.yaml (gitignored option available)
   - Never hardcoded
   - Environment variables supported

2. **Data Privacy**
   - Only public market data
   - No personal information
   - Logs don't contain sensitive data

3. **Dependencies**
   - All dependencies from trusted sources
   - Regular updates recommended
   - No known vulnerabilities

## Future Enhancements

### Planned Features

1. **Additional Indicators**
   - MACD divergences
   - Stochastic divergences
   - Volume divergences

2. **Better Performance**
   - Multiprocessing support
   - Redis/file-based caching
   - Database storage option

3. **Advanced Filtering**
   - Volume filters
   - Price range filters
   - Sector/industry filters

4. **Notifications**
   - Email alerts
   - Slack/Discord webhooks
   - SMS notifications

5. **Web Interface**
   - Dashboard for results
   - Interactive charts
   - Historical scan tracking

6. **Backtesting**
   - Historical accuracy tracking
   - Performance metrics
   - Strategy optimization

## Contributing Guidelines

### Code Style
- Follow PEP 8
- Use type hints
- Write docstrings
- Keep functions focused

### Testing
- Unit tests for each module
- Integration tests for scanner
- Mock external API calls

### Documentation
- Update README for user-facing changes
- Update ARCHITECTURE.md for design changes
- Add inline comments for complex logic

## License

MIT License - See LICENSE file for details
