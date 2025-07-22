import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the Telegram Token from environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    logger.error("❌ ERROR: TELEGRAM_TOKEN is not set!")
    exit()

async def get_btc_price(update: Update, context):
    """Sends the current Bitcoin price when the command /price is issued."""
    try:
        # Using CoinGecko API as an alternative
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
        response.raise_for_status()
        data = response.json()
        price = data["bitcoin"]["usd"]
        await update.message.reply_text(f"The current price of Bitcoin (USD) is: ${price}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Bitcoin price: {e}")
        await update.message.reply_text("Sorry, I couldn't retrieve the Bitcoin price at the moment. Please try again later.")
    except KeyError:
        logger.error("Unexpected API response format for Bitcoin price.")
        await update.message.reply_text("Sorry, there was an issue parsing the Bitcoin price data. Please try again later.")

async def get_btc_price(update: Update, context):
    """Sends the current Bitcoin price when the command /price is issued."""
    try:
        response = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json")
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        price = data["bpi"]["USD"]["rate"]
        await update.message.reply_text(f"The current price of Bitcoin (USD) is: ${price}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Bitcoin price: {e}")
        await update.message.reply_text("Sorry, I couldn't retrieve the Bitcoin price at the moment. Please try again later.")
    except KeyError:
        logger.error("Unexpected API response format for Bitcoin price.")
        await update.message.reply_text("Sorry, there was an issue parsing the Bitcoin price data. Please try again later.")

async def echo(update: Update, context):
    """Echo the user message."""
    await update.message.reply_text(update.message.text)

async def error_handler(update: object, context):
    """Log the error and send a message to the user."""
    logger.warning(f"Update {update} caused error {context.error}")
    await update.message.reply_text("Sorry, an error occurred while processing your request.")

def main():
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", get_btc_price))

    # On non-command messages, echo the user message (optional, you can remove this)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Error handler
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    # For Railway, you typically don't want to use polling in production.
    # Instead, you'd set up a webhook. However, for simple cases, polling
    # can work if Railway keeps the process alive.
    # Given your Procfile, Railway expects a long-running process.
    logger.info("Bot is starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
