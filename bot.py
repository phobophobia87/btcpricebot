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
    # It's better to let Railway crash if the token isn't set,
    # as it's a critical dependency for the bot to run.
    # exit()  # Removed, as Application.builder() will raise an error anyway.

async def start(update: Update, context):
    """Sends a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I'm a bot that can give you Bitcoin prices. "
        "Try typing /price."
    )
    logger.info(f"User {user.full_name} ({user.id}) started the bot.")

async def get_btc_price(update: Update, context):
    """Sends the current Bitcoin price when the command /price is issued using CoinGecko API."""
    logger.info("Received /price command. Fetching Bitcoin price...")
    try:
        # Using CoinGecko API
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        # Expected format: {'bitcoin': {'usd': 65000}}
        price = data["bitcoin"]["usd"]
        formatted_price = f"{price:,.2f}" # Formats with commas and 2 decimal places

        await update.message.reply_text(f"The current price of Bitcoin (USD) is: ${formatted_price}")
        logger.info(f"Sent Bitcoin price: ${formatted_price}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Bitcoin price from CoinGecko: {e}")
        await update.message.reply_text("Sorry, I couldn't retrieve the Bitcoin price at the moment. Please try again later.")
    except KeyError:
        logger.error("Unexpected API response format from CoinGecko for Bitcoin price.")
        await update.message.reply_text("Sorry, there was an issue parsing the Bitcoin price data. Please try again later.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_btc_price: {e}")
        await update.message.reply_text("An unexpected error occurred. Please try again.")


async def echo(update: Update, context):
    """Echo the user message."""
    logger.info(f"Received message from {update.effective_user.full_name}: {update.message.text}")
    await update.message.reply_text(update.message.text)

async def error_handler(update: object, context):
    """Log the error and send a message to the user."""
    logger.error(f"Exception while handling an update:", exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

def main():
    """Start the bot."""
    if not TOKEN:
        # Re-check token here in main before attempting to build Application
        logger.critical("TELEGRAM_TOKEN is not set. Exiting.")
        return # Exit main if token is missing

    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", get_btc_price))

    # On non-command messages, echo the user message (optional, you can remove this)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Error handler
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot is starting polling...")
    # Using allowed_updates=Update.ALL_TYPES for broader compatibility,
    # though for this bot, only MESSAGE updates are strictly needed.
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Bot polling stopped.")


if __name__ == "__main__":
    main()
