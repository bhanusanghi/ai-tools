#!/usr/bin/env python3
"""
Quick test script for Telegram notifications
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config_loader import Config
from src.notifications.telegram_notifier import TelegramNotifier


def test_telegram_setup():
    """Test Telegram bot setup"""
    print("\n" + "=" * 60)
    print("Telegram Bot Test")
    print("=" * 60 + "\n")

    # Load config
    try:
        config = Config('config.yaml')
    except FileNotFoundError:
        print("❌ ERROR: config.yaml not found!")
        print("Please ensure config.yaml exists in the current directory.")
        return False

    # Get Telegram settings
    enabled = config.get('notifications.telegram.enabled', False)
    bot_token = config.get('notifications.telegram.bot_token', '')
    chat_id = config.get('notifications.telegram.chat_id', '')

    print(f"Telegram enabled: {enabled}")
    print(f"Bot token: {'✓ Set' if bot_token else '✗ Not set'}")
    print(f"Chat ID: {'✓ Set' if chat_id else '✗ Not set'}")
    print()

    if not enabled:
        print("⚠️  Telegram notifications are disabled in config.yaml")
        print("\nTo enable:")
        print("  1. Set notifications.telegram.enabled to true")
        print("  2. Add your bot_token from @BotFather")
        print("  3. Add your chat_id from @userinfobot")
        print("\nSee TELEGRAM_SETUP.md for detailed instructions.")
        return False

    if not bot_token or 'YOUR_BOT_TOKEN' in bot_token:
        print("❌ ERROR: Bot token not configured!")
        print("\nPlease update config.yaml with your bot token.")
        print("See TELEGRAM_SETUP.md for instructions.")
        return False

    if not chat_id or 'YOUR_CHAT_ID' in chat_id:
        print("❌ ERROR: Chat ID not configured!")
        print("\nPlease update config.yaml with your chat ID.")
        print("See TELEGRAM_SETUP.md for instructions.")
        return False

    # Create notifier
    notifier = TelegramNotifier(bot_token, chat_id, enabled)

    # Test connection
    print("Testing bot connection...")
    if not notifier.test_connection():
        print("❌ Connection failed!")
        print("\nPossible issues:")
        print("  - Invalid bot token")
        print("  - Network connectivity problems")
        print("\nPlease check your settings and try again.")
        return False

    print("✓ Connection successful!\n")

    # Send test message
    print("Sending test message...")
    if notifier.send_test_message():
        print("✓ Test message sent!")
        print("\n✅ SUCCESS! Check your Telegram for the test message.")
        print("\nYour Telegram bot is ready to use!")
        print("Run 'python main.py' to start receiving divergence alerts.")
        return True
    else:
        print("❌ Failed to send test message!")
        print("\nPossible issues:")
        print("  - Bot is blocked by you")
        print("  - Incorrect chat ID")
        print("\nTry sending /start to your bot in Telegram first.")
        return False


def test_divergence_notification():
    """Test sending a sample divergence notification"""
    print("\n" + "=" * 60)
    print("Testing Divergence Notification Format")
    print("=" * 60 + "\n")

    config = Config('config.yaml')
    bot_token = config.get('notifications.telegram.bot_token', '')
    chat_id = config.get('notifications.telegram.chat_id', '')
    enabled = config.get('notifications.telegram.enabled', False)

    if not enabled or not bot_token or not chat_id:
        print("⚠️  Telegram not configured. Skipping divergence test.")
        return False

    notifier = TelegramNotifier(bot_token, chat_id, enabled)

    # Create sample divergences
    sample_divergences = [
        {
            'ticker': 'AAPL',
            'timeframe': '1d',
            'type': 'bullish',
            'indicator': 'RSI',
            'date': '2024-01-20',
            'current_price': 185.50,
            'price_1': 180.00,
            'price_2': 178.50,
            'indicator_1': 35.0,
            'indicator_2': 40.0,
        },
        {
            'ticker': 'MSFT',
            'timeframe': '1wk',
            'type': 'bearish',
            'indicator': 'AO',
            'date': '2024-01-19',
            'current_price': 380.25,
            'price_1': 375.00,
            'price_2': 382.50,
            'indicator_1': 2.5,
            'indicator_2': 1.8,
        },
    ]

    print("Sending sample divergence alert...")
    if notifier.send_divergence_alert(sample_divergences):
        print("✓ Sample alert sent!")
        print("\nCheck your Telegram to see how divergence alerts look.")
        return True
    else:
        print("❌ Failed to send sample alert")
        return False


def main():
    """Main test runner"""
    print("\n🤖 Telegram Bot Testing Tool 🤖")

    # Test basic setup
    if not test_telegram_setup():
        print("\n" + "=" * 60)
        print("Setup test failed. Please fix the issues above.")
        print("=" * 60 + "\n")
        return 1

    # Ask if user wants to test divergence notification
    print("\n" + "=" * 60)
    print("Would you like to see a sample divergence alert?")
    response = input("Send sample alert? (y/n): ").strip().lower()

    if response == 'y':
        test_divergence_notification()

    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)
    print("\n📱 Your Telegram bot is ready!")
    print("📊 Run 'python main.py' to start receiving alerts\n")

    return 0


if __name__ == '__main__':
    sys.exit(main())
