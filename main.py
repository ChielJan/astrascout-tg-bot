import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")

CRYPTO_API_URL = os.getenv("CRYPTO_API_URL")
CRYPTO_API_HOST = os.getenv("CRYPTO_API_HOST")

INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL")
INSIGHTS_API_HOST = os.getenv("INSIGHTS_API_HOST")

if not BOT_TOKEN:
    raise ValueError("BOT TOKEN ontbreekt")

if not RAPID_API_KEY:
    raise ValueError("RAPID_API_KEY ontbreekt")

def rapid_headers(host):
    return {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": host
    }

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

    try:
        r = requests.get(
            f"{CRYPTO_API_URL}/{symbol}",
            headers=rapid_headers(CRYPTO_API_HOST),
            timeout=10
        )
        r.raise_for_status()
        data = r.json()

        price = data.get("price_usd")

        if not price:
            raise Exception(f"Geen prijs in response: {data}")

        await update.message.reply_text(
            f"💰 {symbol}: ${price}\nBron: {data.get('source', 'unknown')}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Kon prijs niet ophalen\n(debug: {e})")

async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(
            INSIGHTS_API_URL,
            headers=rapid_headers(INSIGHTS_API_HOST),
            timeout=10
        )
        r.raise_for_status()
        data = r.json()

        await update.message.reply_text(
            "📊 Fear & Greed Index\n"
            f"Score: {data.get('fear_greed_index')}\n"
            f"Sentiment: {data.get('classification')}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Kon Fear & Greed niet ophalen\n(debug: {e})")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))

    app.run_polling()

if __name__ == "__main__":
    main()
