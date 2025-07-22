import os
import asyncio
import logging
import requests
import time

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
    # The Application.builder() will raise an error anyway if TOKEN is None.

async def start(update: Update, context):
    """Sends a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I'm a bot that can give you cryptocurrency prices. "
        "Try typing /prices."
    )
    logger.info(f"User {user.full_name} ({user.id}) started the bot.")

async def get_crypto_prices(update: Update, context):
    """Sends the current prices for multiple cryptocurrencies when the command /prices is issued."""
    logger.info("Received /prices command. Fetching cryptocurrency prices...")
    
    # Define the cryptocurrencies and their CoinGecko IDs
    cryptos = {
        "Bitcoin": "bitcoin",
        "Aptos": "aptos",
        "PancakeSwap (CAKE)": "pancakeswap-token",
        "The Sandbox (SAND)": "the-sandbox",
        "Immutable X (IMX)": "immutable-x"
    }
    
    # Create a comma-separated string of IDs for the API request
    coin_ids = ",".join(cryptos.values())
    
    max_retries = 5
    initial_wait_time = 2

    for attempt in range(max_retries):
        try:
            # Using CoinGecko API to get prices for multiple coins
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_ids}&vs_currencies=usd"
            response = requests.get(url)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            price_messages = []
            for name, cg_id in cryptos.items():
                if cg_id in data and "usd" in data[cg_id]:
                    price = data[cg_id]["usd"]
                    formatted_price = f"{price:,.2f}"
                    price_messages.append(f"{name}: ${formatted_price}")
                else:
                    price_messages.append(f"{name}: Price not available")

            # Join all price messages into one string
            full_message = "Current Cryptocurrency Prices (USD):\n" + "\n".join(price_messages)

            await update.message.reply_text(full_message)
            logger.info(f"Sent cryptocurrency prices:\n{full_message}")
            return # Exit the function after successful retrieval

        except HTTPError as e:
            if e.response.status_code == 429:
                wait_time = initial_wait_time * (2 ** attempt) # Exponential backoff
                logger.warning(f"Rate limit hit (429) on attempt {attempt + 1}. Retrying in {wait_time} seconds...")
                if attempt < max_retries - 1:
                    await update.message.reply_text(f"Whoa, too many requests! Please wait a moment. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time) # Asynchronous sleep
            else:
                logger.error(f"HTTP Error fetching crypto prices from CoinGecko: {e}")
                await update.message.reply_text(f"Sorry, I couldn't retrieve the crypto prices due to an API error ({e.response.status_code}). Please try again later.")
                return
        except requests.exceptions.RequestException as e:
            logger.error(f"Network Error fetching crypto prices from CoinGecko: {e}")
            await update.message.reply_text("Sorry, I couldn't retrieve the crypto prices at the moment due to a network issue. Please try again later.")
            return
        except KeyError as e:
            logger.error(f"Unexpected API response format from CoinGecko: Missing key {e}")
            await update.message.reply_text("Sorry, there was an issue parsing the crypto price data. Please try again later.")
            return
        except Exception as e:
            logger.error(f"An unexpected error occurred in get_crypto_prices: {e}", exc_info=True)
            await update.message.reply_text("An unexpected error occurred. Please try again.")
            return

    # If all retries fail
    logger.error(f"Failed to fetch crypto prices after {max_retries} attempts due to persistent issues.")
    await update.message.reply_text("I'm having trouble getting the cryptocurrency prices right now. Please try again in a few minutes.")


async def echo(update: Update, context):
    """Echo the user message. This handler responds to any non-command text."""
    logger.info(f"Received message from {update.effective_user.full_name} ({update.effective_user.id}): {update.message.text}")
    await update.message.reply_text(update.message.text)

async def error_handler(update: object, context):
    """Log the error and send a message to the user."""
    logger.error(f"Exception while handling an update:", exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Oops! Something went wrong on my end. Please try again later."
        )

def main():
    """Start the bot."""
    if not TOKEN:
        logger.critical("TELEGRAM_TOKEN is not set. Cannot start the bot. Exiting.")
        return

    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    # Changed from /price to /prices
    application.add_handler(CommandHandler("prices", get_crypto_prices)) 

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_error_handler(error_handler)

    logger.info("Bot is starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Bot polling stopped.")


if __name__ == "__main__":
    main()
