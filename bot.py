import os
import asyncio
import logging
import requests
import time # Import time for use with the backoff delay

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from requests.exceptions import HTTPError

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
    # The Application.builder() will raise an error anyway if TOKEN is None.

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
    max_retries = 5 # Increased retries slightly
    initial_wait_time = 2 # Start with 2 seconds wait for 429

    for attempt in range(max_retries):
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
            return # Exit the function after successful retrieval

        except HTTPError as e:
            if e.response.status_code == 429:
                wait_time = initial_wait_time * (2 ** attempt) # Exponential backoff
                logger.warning(f"Rate limit hit (429) on attempt {attempt + 1}. Retrying in {wait_time} seconds...")
                if attempt < max_retries - 1: # Only tell the user we're retrying if we actually will
                    await update.message.reply_text(f"Whoa, too many requests! Please wait a moment. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time) # Asynchronous sleep
            else:
                logger.error(f"HTTP Error fetching Bitcoin price from CoinGecko: {e}")
                await update.message.reply_text(f"Sorry, I couldn't retrieve the Bitcoin price due to an API error ({e.response.status_code}). Please try again later.")
                return # Exit on other HTTP errors
        except requests.exceptions.RequestException as e:
            # Catches network errors (e.g., NameResolutionError, ConnectionError, Timeout)
            logger.error(f"Network Error fetching Bitcoin price from CoinGecko: {e}")
            await update.message.reply_text("Sorry, I couldn't retrieve the Bitcoin price at the moment due to a network issue. Please try again later.")
            return
        except KeyError:
            logger.error("Unexpected API response format from CoinGecko for Bitcoin price.")
            await update.message.reply_text("Sorry, there was an issue parsing the Bitcoin price data. Please try again later.")
            return
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"An unexpected error occurred in get_btc_price: {e}", exc_info=True)
            await update.message.reply_text("An unexpected error occurred. Please try again.")
            return

    # If all retries fail
    logger.error(f"Failed to fetch Bitcoin price after {max_retries} attempts due to persistent rate limiting.")
    await update.message.reply_text("I'm having trouble getting the Bitcoin price right now due to too many requests. Please try again in a few minutes.")


async def echo(update: Update, context):
    """Echo the user message. This handler responds to any non-command text."""
    logger.info(f"Received message from {update.effective_user.full_name} ({update.effective_user.id}): {update.message.text}")
    await update.message.reply_text(update.message.text)

async def error_handler(update: object, context):
    """Log the error and send a message to the user."""
    logger.error(f"Exception while handling an update:", exc_info=context.error)
    # Only try to reply if there's an effective message to reply to
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Oops! Something went wrong on my end. Please try again later."
        )

def main():
    """Start the bot."""
    if not TOKEN:
        logger.critical("TELEGRAM_TOKEN is not set. Cannot start the bot. Exiting.")
        return # Exit main if token is missing, Railway will show a critical error and restart if configured

    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", get_btc_price))

    # On non-command text messages, echo the user message
    # (filters.TEXT & ~filters.COMMAND ensures it only catches text that isn't a command)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Register the error handler
    application.add_error_handler(error_handler)

    # Start the bot using polling. For Railway, this means the process needs to stay alive.
    logger.info("Bot is starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Bot polling stopped.")


if __name__ == "__main__":
    main()
