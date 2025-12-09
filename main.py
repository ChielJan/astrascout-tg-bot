import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
CRYPTO_API_URL = os.getenv("CRYPTO_API_URL")
INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL")

if not BOT_TOKEN:
    raise ValueError("BOT TOKEN ontbreekt")

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
    url = f"{CRYPTO_API_URL}/{symbol}"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()

        price = data.get("price_usd")
        source = data.get("source", "unknown")

        if price is None:
            raise ValueError(f"Geen prijs in response: {data}")

        await update.message.reply_text(
            f"💰 {symbol}: ${price}\n"
            f"Bron: {source}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Kon prijs niet ophalen\n{e}")

async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(INSIGHTS_API_URL, timeout=10)
        data = r.json()

        score = data.get("fear_greed_index")
        classification = data.get("classification")

        if score is None or classification is None:
            raise ValueError(f"Onverwachte response: {data}")

        await update.message.reply_text(
            "📊 Fear & Greed Index\n"
            f"Score: {score}\n"
            f"Sentiment: {classification}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Kon Fear & Greed niet ophalen\n{e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))

    print("✅ Bot gestart")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
