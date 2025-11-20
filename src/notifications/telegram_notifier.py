"""
Telegram Bot Notification System
Sends divergence alerts via Telegram
"""
import requests
import logging
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime


logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Send notifications via Telegram Bot"""

    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True):
        """
        Initialize Telegram notifier

        Args:
            bot_token: Telegram bot token from BotFather
            chat_id: Your Telegram chat ID
            enabled: Whether notifications are enabled
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a text message via Telegram

        Args:
            message: Message text (supports Markdown)
            parse_mode: Parsing mode (Markdown or HTML)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled")
            return False

        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram bot token or chat ID not configured")
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            logger.debug(f"Telegram message sent successfully")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def send_divergence_alert(self, divergences: List[Dict]) -> bool:
        """
        Send formatted divergence alert

        Args:
            divergences: List of divergence dictionaries

        Returns:
            True if successful
        """
        if not divergences:
            return False

        # Group by ticker for cleaner formatting
        ticker_groups = {}
        for div in divergences:
            ticker = div['ticker']
            if ticker not in ticker_groups:
                ticker_groups[ticker] = []
            ticker_groups[ticker].append(div)

        # Format message
        message = self._format_divergence_message(ticker_groups)

        return self.send_message(message)

    def _format_divergence_message(self, ticker_groups: Dict[str, List[Dict]]) -> str:
        """
        Format divergences into a readable Telegram message

        Args:
            ticker_groups: Dictionary of ticker -> list of divergences

        Returns:
            Formatted message string
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        total_divs = sum(len(divs) for divs in ticker_groups.values())

        # Header
        message = f"📊 *Divergence Alert* 📊\n"
        message += f"🕐 {timestamp}\n"
        message += f"🔍 Found {total_divs} divergence(s) in {len(ticker_groups)} stock(s)\n"
        message += "─" * 30 + "\n\n"

        # List each ticker
        for ticker, divs in sorted(ticker_groups.items())[:10]:  # Limit to 10 stocks per message
            message += f"💹 *{ticker}*\n"

            # Group divergences by type and indicator
            for div in divs[:5]:  # Limit to 5 divergences per stock
                div_type = div['type']
                indicator = div['indicator']
                timeframe = div['timeframe']
                date = div['date']
                current_price = div.get('current_price', 0)

                # Emoji based on type
                emoji = "🟢" if div_type == 'bullish' else "🔴"

                message += f"{emoji} {div_type.upper()} {indicator} ({timeframe})\n"
                message += f"   Date: {date}\n"
                message += f"   Price: ${current_price:.2f}\n"

            message += "\n"

        # Footer
        message += "─" * 30 + "\n"
        message += "💡 _Review these on TradingView_\n"

        # Truncate if too long (Telegram limit is 4096 characters)
        if len(message) > 4000:
            message = message[:3900] + "\n\n... (truncated)\n\nCheck CSV for full results."

        return message

    def send_scan_summary(
        self,
        total_stocks: int,
        total_divergences: int,
        timeframes: List[str],
        scan_duration: float
    ) -> bool:
        """
        Send scan completion summary

        Args:
            total_stocks: Number of stocks scanned
            total_divergences: Number of divergences found
            timeframes: List of timeframes scanned
            scan_duration: Duration in seconds

        Returns:
            True if successful
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        message = f"✅ *Scan Complete* ✅\n\n"
        message += f"🕐 {timestamp}\n"
        message += f"📊 Stocks scanned: {total_stocks}\n"
        message += f"🔍 Divergences found: {total_divergences}\n"
        message += f"⏱️ Timeframes: {', '.join(timeframes)}\n"
        message += f"⚡ Duration: {scan_duration:.1f}s\n"

        return self.send_message(message)

    def send_error_alert(self, error_message: str) -> bool:
        """
        Send error notification

        Args:
            error_message: Error message

        Returns:
            True if successful
        """
        message = f"⚠️ *Scanner Error* ⚠️\n\n"
        message += f"{error_message}\n\n"
        message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        return self.send_message(message)

    def test_connection(self) -> bool:
        """
        Test Telegram bot connection

        Returns:
            True if connection successful
        """
        if not self.enabled:
            logger.info("Telegram notifications disabled")
            return False

        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                logger.info(f"✓ Telegram bot connected: @{bot_info.get('username')}")
                return True
            else:
                logger.error("Telegram bot connection failed")
                return False

        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False

    def send_test_message(self) -> bool:
        """
        Send a test message to verify setup

        Returns:
            True if successful
        """
        message = "🧪 *Test Message* 🧪\n\n"
        message += "Your Stock Divergence Scanner is successfully connected to Telegram!\n\n"
        message += "You will receive notifications when divergences are detected.\n\n"
        message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        return self.send_message(message)


# Utility function for quick sending
def send_telegram_notification(
    bot_token: str,
    chat_id: str,
    divergences: List[Dict]
) -> bool:
    """
    Quick utility to send divergence notification

    Args:
        bot_token: Telegram bot token
        chat_id: Chat ID
        divergences: List of divergences

    Returns:
        True if successful
    """
    notifier = TelegramNotifier(bot_token, chat_id)
    return notifier.send_divergence_alert(divergences)


# For testing/debugging
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python telegram_notifier.py <bot_token> <chat_id>")
        print("\nThis will send a test message to verify your Telegram setup.")
        sys.exit(1)

    bot_token = sys.argv[1]
    chat_id = sys.argv[2]

    logging.basicConfig(level=logging.INFO)

    notifier = TelegramNotifier(bot_token, chat_id)

    print("\nTesting Telegram connection...")
    if notifier.test_connection():
        print("✓ Connection successful!")

        print("\nSending test message...")
        if notifier.send_test_message():
            print("✓ Test message sent! Check your Telegram.")
        else:
            print("✗ Failed to send test message.")
    else:
        print("✗ Connection failed. Please check your bot token and chat ID.")
