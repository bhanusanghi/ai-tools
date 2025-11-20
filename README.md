# Stock Divergence Scanner

Automated scanner to detect RSI and Awesome Oscillator (AO) divergences across major stock indices including S&P 500 and NASDAQ 100.

## Features

- **Multi-Timeframe Analysis**: Scan 4h, 1d, 3d, and 1wk timeframes (configurable)
- **Multiple Indices**: Support for S&P 500, NASDAQ 100, Dow Jones, and more
- **Technical Indicators**:
  - RSI (Relative Strength Index) divergences
  - Awesome Oscillator (AO) divergences
- **Divergence Types**:
  - Bullish divergences (price lower low, indicator higher low)
  - Bearish divergences (price higher high, indicator lower high)
- **Free Data Sources**: Uses free APIs (yfinance) - no API keys required
- **Automated Scheduling**: Optional daily automated scans
- **CSV Output**: Export results to CSV for further analysis

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd ai-tools

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Edit `config.yaml` to customize your scan:

```yaml
# Select indices to scan
indices:
  - "^GSPC"    # S&P 500
  - "^NDX"     # NASDAQ 100

# Choose timeframes
timeframes:
  - "4h"
  - "1d"
  - "1wk"

# Configure indicators
indicators:
  rsi:
    enabled: true
    period: 14
  ao:
    enabled: true
```

### 3. Run the Scanner

```bash
python main.py
```

Results will be saved to the `outputs/` directory as CSV files.

## Project Structure

```
ai-tools/
├── main.py                 # Main entry point
├── scheduler.py            # Automated scheduler
├── config.yaml            # Configuration file
├── requirements.txt       # Python dependencies
├── src/
│   ├── scanner.py         # Main scanner logic
│   ├── data_fetchers/     # Data fetching modules
│   │   ├── index_fetcher.py    # Fetch index constituents
│   │   └── price_fetcher.py    # Fetch price data
│   ├── indicators/        # Technical indicators
│   │   ├── rsi.py              # RSI calculation
│   │   └── awesome_oscillator.py  # AO calculation
│   ├── divergence/        # Divergence detection
│   │   └── detector.py         # Divergence detection logic
│   └── utils/             # Utilities
│       ├── config_loader.py    # Configuration loader
│       └── logger.py           # Logging setup
├── outputs/               # Output CSV files
└── logs/                  # Log files
```

## Usage

### Basic Scan

Run a one-time scan:

```bash
python main.py
```

### Automated Daily Scans

1. Enable scheduler in `config.yaml`:

```yaml
scheduler:
  enabled: true
  run_time: "09:00"  # 9 AM daily
```

2. Run the scheduler:

```bash
python scheduler.py
```

The scanner will run automatically at the specified time each day.

### Using Cron (Linux/Mac)

Alternatively, set up a cron job:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 9 AM)
0 9 * * * cd /path/to/ai-tools && /usr/bin/python3 main.py
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create a new task
3. Set trigger to daily at your preferred time
4. Set action to run: `python.exe C:\path\to\ai-tools\main.py`

## Output Format

The CSV output contains the following columns:

- `ticker`: Stock ticker symbol
- `timeframe`: Timeframe where divergence was detected
- `type`: Divergence type (bullish/bearish)
- `indicator`: Indicator used (RSI/AO)
- `date`: Date of the divergence
- `current_price`: Current stock price
- `price_1`, `price_2`: Price at divergence points
- `indicator_1`, `indicator_2`: Indicator values at divergence points
- `date_1`, `date_2`: Dates of divergence points
- `scan_date`: When the scan was performed

## Configuration Options

### Indices

Supported indices:
- `^GSPC` - S&P 500
- `^NDX` - NASDAQ 100
- `^DJI` - Dow Jones Industrial Average
- `^RUT` - Russell 2000 (limited support)

### Timeframes

Supported timeframes:
- `4h` - 4-hour (requires more data, may be slower)
- `1d` - Daily
- `3d` - 3-day (resampled from daily)
- `1wk` - Weekly

### Indicators

**RSI Settings:**
- `period`: RSI period (default: 14)
- `overbought`: Overbought level (default: 70)
- `oversold`: Oversold level (default: 30)

**Awesome Oscillator Settings:**
- `fast_period`: Fast SMA period (default: 5)
- `slow_period`: Slow SMA period (default: 34)

### Divergence Detection

- `lookback_periods`: How many periods to look back (default: 50)
- `min_bars_between_pivots`: Minimum bars between pivot points (default: 5)

## API Usage

### Free APIs

The scanner uses **yfinance** which is free and requires no API key. However, it has some limitations:

- Rate limiting (add delays between requests)
- 4-hour data may be less reliable
- Historical data may have gaps

### Optional: Alpha Vantage (for 4h data)

If you need more reliable 4-hour data:

1. Get a free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Update `config.yaml`:

```yaml
data:
  use_alpha_vantage: true
  alpha_vantage_key: "YOUR_API_KEY"
```

Note: Free tier has 500 calls/day limit.

## Troubleshooting

### No data returned for stocks

- Check your internet connection
- Some stocks may not have data for all timeframes
- Try increasing `days_of_history` in config

### Scanner is slow

- Reduce the number of stocks by limiting indices
- Reduce the number of timeframes
- The first run is slower as it fetches data

### Missing dependencies

```bash
pip install -r requirements.txt --upgrade
```

## Advanced Usage

### Custom Stock List

Instead of using indices, you can modify `src/data_fetchers/index_fetcher.py` to return a custom list:

```python
def get_custom_stocks():
    return ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
```

### Export to Other Formats

The scanner returns a pandas DataFrame, which can be exported to various formats:

```python
# In main.py
results.to_excel('divergences.xlsx', index=False)
results.to_json('divergences.json', orient='records')
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Disclaimer

This tool is for educational and informational purposes only. It is not financial advice. Always do your own research before making investment decisions.

## Support

For issues and questions, please open an issue on GitHub.
