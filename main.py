import os
import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# --------------------------------------------------
# Config & environment
# --------------------------------------------------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
CRYPTO_API_BASE = os.getenv("CRYPTO_API_URL", "").rstrip("/")
INSIGHTS_API_BASE = os.getenv("INSIGHTS_API_URL", "").rstrip("/")

if not BOT_TOKEN:
    raise RuntimeError("Environment variable ASTRASCOUT_BOT_TOKEN ontbreekt")
if not CRYPTO_API_BASE:
    raise RuntimeError("Environment variable CRYPTO_API_URL ontbreekt")
if not INSIGHTS_API_BASE:
    raise RuntimeError("Environment variable INSIGHTS_API_URL ontbreekt")


# --------------------------------------------------
# Command handlers
# --------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /start command """
    text = (
        "🤖 AstraScout Crypto Bot\n\n"
        "Commands:\n"
        "/price BTC – huidige prijs\n"
        "/feargreed – Fear & Greed index"
    )
    await update.message.reply_text(text)


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /price <SYMBOL> """
    if not context.args:
        await update.message.reply_text("Gebruik: /price BTC")
        return

    symbol = context.args[0].upper()
    url = f"{CRYPTO_API_BASE}/price/{symbol}"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        price = data.get("price")
        if price is None:
            raise ValueError("Geen 'price' veld in response")

        await update.message.reply_text(f"💰 {symbol}: ${price}")
    except Exception as e:
        logger.exception("Fout bij ophalen prijs voor %s: %s", symbol, e)
        await update.message.reply_text("❌ Kon prijs niet ophalen, probeer later opnieuw.")


async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /feargreed """
    url = f"{INSIGHTS_API_BASE}/feargreed"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        score = data.get("fear_greed_index")
        label = data.get("label")

        if score is None or label is None:
            raise ValueError("Onverwacht response-formaat")

        text = (
            "📊 Fear & Greed Index\n"
            f"Score: {score}\n"
            f"Sentiment: {label}"
        )
        await update.message.reply_text(text)
    except Exception as e:
        logger.exception("Fout bij ophalen Fear & Greed: %s", e)
        await update.message.reply_text("❌ Kon Fear & Greed niet ophalen, probeer later opnieuw.")


# --------------------------------------------------
# Main entrypoint
# --------------------------------------------------

def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))

    logger.info("✅ AstraScout Telegram bot gestart")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
