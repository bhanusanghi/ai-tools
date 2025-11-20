# Quick Start Guide

Get up and running with the Stock Divergence Scanner in 5 minutes!

## Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- yfinance (for fetching stock data)
- pandas, numpy (for data processing)
- ta (for technical indicators)
- pyyaml (for configuration)
- schedule (for automation)
- tqdm (for progress bars)

## Step 2: Configure Your Scan

Open `config.yaml` and customize:

### Minimal Configuration (Recommended for First Run)

```yaml
# Start with just S&P 500 and daily timeframe
indices:
  - "^GSPC"    # S&P 500

timeframes:
  - "1d"       # Daily only

# Keep defaults for indicators
indicators:
  rsi:
    enabled: true
    period: 14
  ao:
    enabled: true
    fast_period: 5
    slow_period: 34
```

### Full Configuration (After Testing)

```yaml
# Scan multiple indices
indices:
  - "^GSPC"    # S&P 500
  - "^NDX"     # NASDAQ 100

# Multiple timeframes
timeframes:
  - "4h"
  - "1d"
  - "3d"
  - "1wk"
```

## Step 3: Run Your First Scan

```bash
python main.py
```

Expected output:
```
============================================================
Stock Divergence Scanner
============================================================

INFO - Fetching stocks from indices: ['^GSPC']
INFO - Found 503 stocks in ^GSPC
INFO - Total unique stocks: 503

============================================================
Scanning timeframe: 1d
============================================================
INFO - Fetching 1d data for 503 stocks...
INFO - Successfully fetched data for 495 stocks
INFO -   AAPL: Found 2 divergence(s)
INFO -   MSFT: Found 1 divergence(s)
...

============================================================
Scan complete! Found 47 divergences
============================================================

Results saved to: outputs/divergence_scan_20231120_093045.csv
```

## Step 4: View Results

Results are saved in the `outputs/` directory as CSV files.

### Open in Excel/Google Sheets

Simply double-click the CSV file or import it into your spreadsheet application.

### View in Terminal

```bash
# View first 10 rows
head -n 10 outputs/divergence_scan_*.csv

# Count divergences by type
grep "bullish" outputs/divergence_scan_*.csv | wc -l
grep "bearish" outputs/divergence_scan_*.csv | wc -l
```

### Example Output Format

| ticker | timeframe | type    | indicator | date       | current_price | price_1 | price_2 |
|--------|-----------|---------|-----------|------------|---------------|---------|---------|
| AAPL   | 1d        | bullish | RSI       | 2024-01-15 | 185.50        | 175.20  | 173.80  |
| MSFT   | 1wk       | bearish | AO        | 2024-01-12 | 380.25        | 375.00  | 382.50  |
| GOOGL  | 1d        | bullish | RSI       | 2024-01-14 | 142.30        | 138.50  | 137.20  |

## Step 5: Automate (Optional)

### Option A: Python Scheduler

Edit `config.yaml`:
```yaml
scheduler:
  enabled: true
  run_time: "09:00"  # 9 AM daily
```

Run the scheduler:
```bash
python scheduler.py
```

### Option B: Cron (Linux/Mac)

```bash
crontab -e
```

Add:
```bash
0 9 * * * cd /path/to/ai-tools && python3 main.py
```

### Option C: Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Stock Divergence Scanner"
4. Trigger: Daily at 9:00 AM
5. Action: Start a program
   - Program: `python.exe`
   - Arguments: `C:\path\to\ai-tools\main.py`
   - Start in: `C:\path\to\ai-tools`

## Troubleshooting

### Issue: "No module named 'yfinance'"

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "config.yaml not found"

**Solution:** Make sure you're running the script from the `ai-tools` directory:
```bash
cd /path/to/ai-tools
python main.py
```

### Issue: Scanner is very slow

**Solution:** Start with fewer stocks/timeframes:
- Use only S&P 500 (remove NASDAQ 100)
- Use only daily timeframe (remove 4h, 3d, 1wk)
- Reduce `days_of_history` in config

### Issue: No divergences found

**Solution:** This is normal! Divergences are relatively rare. Try:
- Increase `lookback_periods` to 100
- Decrease `min_bars_between_pivots` to 3
- Scan more timeframes

## Understanding the Results

### Divergence Types

**Bullish Divergence** (Potential Buy Signal):
- Price makes lower low
- Indicator (RSI/AO) makes higher low
- Suggests downtrend may be weakening

**Bearish Divergence** (Potential Sell Signal):
- Price makes higher high
- Indicator (RSI/AO) makes lower high
- Suggests uptrend may be weakening

### Important Columns

- **ticker**: Stock symbol
- **type**: bullish or bearish
- **indicator**: RSI or AO
- **date**: When divergence occurred
- **current_price**: Latest stock price
- **price_1, price_2**: Price at the two divergence points
- **indicator_1, indicator_2**: Indicator values at divergence points

### Using the Results

1. **Filter by Type**: Look for bullish divergences if you're looking to buy
2. **Cross-reference Timeframes**: Stronger signal if multiple timeframes show divergence
3. **Verify Manually**: Always check the chart yourself on TradingView
4. **Combine with Other Analysis**: Divergences are just one tool, not a complete strategy

## Next Steps

1. Test with a small number of stocks first
2. Gradually add more indices and timeframes
3. Backtest your findings
4. Set up automation once you're comfortable
5. Combine with your TradingView premium subscription for detailed analysis

## Tips for Best Results

- **Run in the morning** before market open (or after close)
- **Focus on quality over quantity** - fewer, high-quality divergences are better
- **Use multiple timeframes** - divergences on higher timeframes (weekly) are more significant
- **Combine indicators** - divergences on both RSI and AO are stronger signals
- **Keep a trading journal** - track which divergences led to profitable trades

## Getting Help

- Check the main [README.md](README.md) for detailed documentation
- Review the configuration options in `config.yaml`
- Check logs in the `logs/` directory for debugging
- Open an issue on GitHub for bugs or feature requests

Happy trading! Remember: This is a tool to assist your analysis, not a crystal ball. Always do your own research and never invest more than you can afford to lose.
