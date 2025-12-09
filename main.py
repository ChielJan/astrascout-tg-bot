import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- Logging zodat we straks beter kunnen debuggen ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- Environment variables van Railway ---
BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
CRYPTO_API_URL = os.getenv("CRYPTO_API_URL") # bv. https://web-production-0c26.up.railway.app/price
INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL") # bv. https://astrascout-market-insights-api-production.up.railway.app/feargreed

if not BOT_TOKEN:
    raise RuntimeError("ASTRASCOUT_BOT_TOKEN ontbreekt in environment variables")

# --- Commands ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welkom + helptekst."""
    await update.message.reply_text(
        "🤖 AstraScout Crypto Bot\n\n"
        "Available commands:\n"
        "/price BTC – current price\n"
        "/feargreed – Fear & Greed index"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prijs van een token ophalen via Crypto API."""
    if not CRYPTO_API_URL:
        await update.message.reply_text("❌ Config error: CRYPTO_API_URL ontbreekt")
        return

    if not context.args:
        await update.message.reply_text("Gebruik: /price BTC")
        return

    symbol = context.args[0].upper()
    url = f"{CRYPTO_API_URL}/{symbol}" # base URL uit Railway + /BTC

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        price_value = data.get("price")
        if price_value is None:
            raise ValueError("Geen prijs in API-response")

        await update.message.reply_text(f"💰 {symbol}: ${price_value}")
    except Exception as e:
        logger.exception("Fout bij /price")
        await update.message.reply_text("❌ Kon prijs niet ophalen, probeer later opnieuw.")

async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fear & Greed index ophalen via Insights API."""
    if not INSIGHTS_API_URL:
        await update.message.reply_text("❌ Config error: INSIGHTS_API_URL ontbreekt")
        return

    try:
        resp = requests.get(INSIGHTS_API_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        score = data.get("fear_greed_index")
        label = data.get("label")

        if score is None or label is None:
            raise ValueError("Onverwachte response van Insights API")

        await update.message.reply_text(
            "📊 Fear & Greed Index\n"
            f"Score: {score}\n"
            f"Sentiment: {label}"
        )
    except Exception as e:
        logger.exception("Fout bij /feargreed")
        await update.message.reply_text("❌ Kon Fear & Greed niet ophalen, probeer later opnieuw.")

# --- Main entrypoint ---

def main() -> None:
    """Start de bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("feargreed", feargreed))

    logger.info("✅ AstraScout bot gestart (polling)")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
