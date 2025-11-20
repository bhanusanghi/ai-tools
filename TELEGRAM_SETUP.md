# Telegram Bot Setup Guide

Get real-time divergence alerts sent directly to your Telegram!

## Overview

The Stock Divergence Scanner can send notifications to your Telegram account:
- **Divergence Alerts**: Get notified when divergences are detected
- **Scan Summaries**: Receive scan completion reports
- **Error Alerts**: Be informed of any scanning errors

## Setup Steps

### Step 1: Create a Telegram Bot

1. **Open Telegram** and search for `@BotFather`

2. **Start a chat** with BotFather and send:
   ```
   /newbot
   ```

3. **Choose a name** for your bot (e.g., "Stock Divergence Scanner")

4. **Choose a username** for your bot (must end in 'bot', e.g., "my_divergence_bot")

5. **Copy the bot token** that BotFather gives you. It looks like:
   ```
   123456789:ABCdefGhIJKlmNoPQRstuVWXyz1234567890
   ```

6. **Save this token** - you'll need it for configuration

### Step 2: Get Your Chat ID

**Method 1: Using a Bot (Easiest)**

1. Search for `@userinfobot` on Telegram
2. Start a chat and send any message
3. The bot will reply with your chat ID (a number like `123456789`)
4. Copy this number

**Method 2: Manual Method**

1. Send a message to your bot (the one you just created)
2. Open this URL in your browser (replace `YOUR_BOT_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
3. Look for `"chat":{"id":123456789` in the response
4. Copy the ID number

### Step 3: Configure the Scanner

1. **Open `config.yaml`** in your scanner directory

2. **Find the notifications section** and update it:

```yaml
notifications:
  telegram:
    enabled: true  # Enable notifications
    bot_token: "123456789:ABCdefGhIJKlmNoPQRstuVWXyz1234567890"  # Your bot token
    chat_id: "123456789"  # Your chat ID

    # Notification preferences
    notify_on_scan_complete: true  # Send summary when scan completes
    notify_on_divergences: true    # Send alert when divergences found
    notify_on_errors: true         # Send alert on errors
    min_divergences_to_notify: 1   # Minimum divergences to trigger notification
```

3. **Save the file**

### Step 4: Test Your Setup

Run the test script:

```bash
python src/notifications/telegram_notifier.py YOUR_BOT_TOKEN YOUR_CHAT_ID
```

Or test directly in Python:

```python
python -c "
from src.notifications.telegram_notifier import TelegramNotifier
notifier = TelegramNotifier('YOUR_BOT_TOKEN', 'YOUR_CHAT_ID', True)
notifier.send_test_message()
"
```

If successful, you should receive a test message on Telegram!

### Step 5: Run a Scan

Now run your scanner as usual:

```bash
python main.py
```

You'll receive Telegram notifications automatically!

## Notification Types

### 1. Divergence Alert

Sent when divergences are detected:

```
📊 Divergence Alert 📊
🕐 2024-01-20 09:15
🔍 Found 12 divergence(s) in 5 stock(s)
──────────────────────────────

💹 AAPL
🟢 BULLISH RSI (1d)
   Date: 2024-01-19
   Price: $185.50

🔴 BEARISH AO (1wk)
   Date: 2024-01-18
   Price: $186.20

💹 MSFT
🟢 BULLISH RSI (1d)
   Date: 2024-01-19
   Price: $380.25

──────────────────────────────
💡 Review these on TradingView
```

### 2. Scan Summary

Sent when scan completes:

```
✅ Scan Complete ✅

🕐 2024-01-20 09:20
📊 Stocks scanned: 503
🔍 Divergences found: 12
⏱️ Timeframes: 1d, 1wk
⚡ Duration: 345.2s
```

### 3. Error Alert

Sent when errors occur:

```
⚠️ Scanner Error ⚠️

No stocks found in indices

🕐 2024-01-20 09:15
```

## Configuration Options

### Notification Preferences

```yaml
notifications:
  telegram:
    # When to send notifications
    notify_on_scan_complete: true  # Always notify after scan
    notify_on_divergences: true    # Notify when divergences found
    notify_on_errors: true         # Notify on errors

    # Threshold for divergence alerts
    min_divergences_to_notify: 1   # Only notify if >= this many divergences
                                   # Set to 5 to reduce noise
```

### Examples

**Silent mode** (only errors):
```yaml
notify_on_scan_complete: false
notify_on_divergences: false
notify_on_errors: true
min_divergences_to_notify: 1
```

**High-quality only** (5+ divergences):
```yaml
notify_on_scan_complete: true
notify_on_divergences: true
notify_on_errors: true
min_divergences_to_notify: 5  # Only notify if 5+ divergences found
```

**Maximum alerts** (everything):
```yaml
notify_on_scan_complete: true
notify_on_divergences: true
notify_on_errors: true
min_divergences_to_notify: 1  # Notify for any divergences
```

## Troubleshooting

### "Failed to send Telegram message"

**Possible causes:**
1. **Wrong bot token** - Double-check your token from BotFather
2. **Wrong chat ID** - Verify your chat ID
3. **Bot not started** - Send `/start` to your bot in Telegram
4. **No internet connection** - Check your network

**Solution:**
```bash
# Test connection
python src/notifications/telegram_notifier.py YOUR_BOT_TOKEN YOUR_CHAT_ID
```

### "Telegram notifications disabled"

Check your `config.yaml`:
```yaml
notifications:
  telegram:
    enabled: true  # Must be true!
```

### Not receiving messages

1. **Check if bot is blocked**: Open Telegram, find your bot, click "Start" or "Restart"
2. **Verify chat ID**: Make sure you're using the correct chat ID
3. **Check logs**: Look in `logs/` directory for error messages

### Messages are too long / truncated

The scanner automatically truncates long messages (Telegram limit: 4096 characters).

**Solutions:**
- Increase `min_divergences_to_notify` to reduce results
- Check the CSV file for full results
- Only scan specific timeframes (reduce volume)

## Advanced Usage

### Send Custom Notifications

```python
from src.notifications.telegram_notifier import TelegramNotifier

# Create notifier
notifier = TelegramNotifier("YOUR_BOT_TOKEN", "YOUR_CHAT_ID", True)

# Send custom message
notifier.send_message("🚀 Custom alert: AAPL breaking out!")

# Send divergence alert manually
divergences = [
    {
        'ticker': 'AAPL',
        'type': 'bullish',
        'indicator': 'RSI',
        'timeframe': '1d',
        'date': '2024-01-20',
        'current_price': 185.50
    }
]
notifier.send_divergence_alert(divergences)
```

### Multiple Recipients

To send to multiple Telegram accounts, you can:

1. **Create a Telegram group**:
   - Create a group in Telegram
   - Add your bot to the group
   - Get the group chat ID (negative number, e.g., `-123456789`)
   - Use the group chat ID in config

2. **Run multiple scanners**:
   - Create separate config files for each recipient
   - Run scanner with different configs

### Integration with Scheduler

Notifications work automatically with the scheduler:

```bash
# Set up in config.yaml
scheduler:
  enabled: true
  run_time: "09:00"

notifications:
  telegram:
    enabled: true

# Run scheduler
python scheduler.py
```

You'll receive notifications every morning at 9 AM automatically!

## Security Best Practices

1. **Keep your bot token secret** - Never share it publicly
2. **Use environment variables** (optional):
   ```bash
   export TELEGRAM_BOT_TOKEN="your_token"
   export TELEGRAM_CHAT_ID="your_chat_id"
   ```
3. **Disable bot if compromised** - Talk to @BotFather to revoke token
4. **Use private chat** - Don't add bot to public groups
5. **Gitignore config.yaml** - Don't commit tokens to Git

## FAQ

**Q: Can I use this with Telegram groups?**
A: Yes! Add your bot to a group and use the group's chat ID (it will be negative).

**Q: Can multiple people receive notifications?**
A: Yes, either use a group or run separate scanners for each person.

**Q: Are there rate limits?**
A: Telegram has rate limits (~30 messages/second), but the scanner sends very few messages.

**Q: Can I customize the message format?**
A: Yes! Edit `src/notifications/telegram_notifier.py` - look for `_format_divergence_message()`.

**Q: Does this cost money?**
A: No, Telegram bots are completely free!

**Q: Can I turn off notifications temporarily?**
A: Yes, set `enabled: false` in config.yaml or just ignore the messages.

## Next Steps

1. ✅ Set up your Telegram bot
2. ✅ Configure notifications in `config.yaml`
3. ✅ Test with `python main.py`
4. 🚀 Automate with scheduler for daily alerts!

## Support

If you encounter issues:
1. Check the [main README](README.md) for general scanner help
2. Review Telegram bot logs in `logs/` directory
3. Test connection with the test script
4. Open an issue on GitHub with error details

Happy trading! 📈
