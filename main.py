import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- Logging (handig voor debuggen) ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Environment variables ---
BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
CRYPTO_API_URL = os.getenv("CRYPTO_API_URL", "").rstrip("/")
INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL", "").rstrip("/")

if not BOT_TOKEN:
    raise ValueError("BOT TOKEN ontbreekt")
if not CRYPTO_API_URL:
    raise ValueError("CRYPTO_API_URL ontbreekt")
if not INSIGHTS_API_URL:
    raise ValueError("INSIGHTS_API_URL ontbreekt")


# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 AstraScout Crypto Bot\n\n"
        "Available commands:\n"
        "/price BTC – current price\n"
        "/feargreed – Fear & Greed index\n\n"
        "Gebruik: /price BTC"
    )
    await update.message.reply_text(text)


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gebruik: /price BTC")
        return

    symbol = context.args[0].upper()
    url = f"{CRYPTO_API_URL}/price/{symbol}"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # 👉 PAS DIT AAN ALS JE JSON ANDERS IS
        # Kijk in je browser wat /price/BTC teruggeeft.
        price_value = data.get("price")

        if price_value is None:
            raise ValueError(f"Geen 'price' veld in response: {data}")

        await update.message.reply_text(f"💰 {symbol}: ${price_value}")
    except Exception as e:
        logger.exception("Fout in /price handler")
        await update.message.reply_text(
            f"❌ Kon prijs niet ophalen, probeer later opnieuw.\n\n"
            f"(debug: {e})"
        )


async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f"{INSIGHTS_API_URL}/feargreed"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # 👉 PAS DIT AAN ALS JE JSON ANDERS IS
        score = data.get("fear_greed_index")
        label = data.get("label")

        if score is None or label is None:
            raise ValueError(f"Onverwachte response: {data}")

        await update.message.reply_text(
            "📊 Fear & Greed Index\n"
            f"Score: {score}\n"
            f"Sentiment: {label}"
        )
    except Exception as e:
        logger.exception("Fout in /feargreed handler")
        await update.message.reply_text(
            f"❌ Kon Fear & Greed niet ophalen, probeer later opnieuw.\n\n"
            f"(debug: {e})"
        )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))

    print("✅ Bot gestart")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
