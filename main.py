import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ------- Logging (handig om in Railway-logs te zien wat er gebeurt) -------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ------- Environment vars uit Railway -------
BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
CRYPTO_API_URL = os.getenv("CRYPTO_API_URL", "").rstrip("/")
INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL", "").rstrip("/")

if not BOT_TOKEN:
    raise ValueError("BOT TOKEN ontbreekt (ASTRASCOUT_BOT_TOKEN niet gezet in Railway)")

# ------- Commands -------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AstraScout Crypto Bot\n\n"
        "Commands:\n"
        "/price BTC\n"
        "/feargreed"
    )


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gebruik: /price BTC")
        return

    symbol = context.args[0].upper()

    # CRYPTO_API_URL moet in Railway de base URL zijn tot /price
    # bijv. https://web-production-0c26.up.railway.app/price
    url = f"{CRYPTO_API_URL}/{symbol}"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        price = data.get("price")
        if price is None:
            raise ValueError("Geen prijs gevonden in API-response")

        await update.message.reply_text(f"💰 {symbol}: ${price}")
    except Exception as e:
        logger.exception("Fout bij /price:")
        await update.message.reply_text("❌ Kon prijs niet ophalen, probeer later opnieuw.")


async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # INSIGHTS_API_URL
