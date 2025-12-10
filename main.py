import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --------- ENV VARS ---------
BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")

CRYPTO_API_URL = os.getenv("CRYPTO_API_URL") # bv. https://astrascout-crypto-api.p.rapidapi.com/price
CRYPTO_API_HOST = os.getenv("CRYPTO_API_HOST") # bv. astrascout-crypto-api.p.rapidapi.com

INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL") # bv. https://astrascout-market-insights-api.p.rapidapi.com/feargreed
INSIGHTS_API_HOST = os.getenv("INSIGHTS_API_HOST") # bv. astrascout-market-insights-api.p.rapidapi.com


# --------- CHECKS ---------
if not BOT_TOKEN:
    raise ValueError("ASTRASCOUT_BOT_TOKEN ontbreekt in Railway variables")

if not RAPID_API_KEY:
    raise ValueError("RAPID_API_KEY ontbreekt in Railway variables")


def rapid_headers(host: str) -> dict:
    """Headers die RapidAPI nodig heeft."""
    return {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": host,
    }


# --------- COMMANDS ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AstraScout Crypto Bot\n\n"
        "Available commands:\n"
        "/price BTC – current price\n"
        "/feargreed – Fear & Greed index"
    )


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gebruik: /price BTC")
        return

    symbol = context.args[0].upper()

    try:
        resp = requests.get(
            f"{CRYPTO_API_URL}/{symbol}",
            headers=rapid_headers(CRYPTO_API_HOST),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        # jouw Rapid-response gebruikt 'price_usd'
        price_usd = data.get("price_usd")

        if price_usd is None:
            raise ValueError(f"Geen 'price_usd' veld in response: {data}")

        source = data.get("source", "unknown")

        await update.message.reply_text(
            f"💰 {symbol}: ${price_usd}\n"
            f"Bron: {source}"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Kon prijs niet ophalen, probeer later opnieuw.\n"
            f"(debug: {e})"
        )


async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resp = requests.get(
            INSIGHTS_API_URL,
            headers=rapid_headers(INSIGHTS_API_HOST),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        score = data.get("fear_greed_index")
        label = data.get("classification")

        await update.message.reply_text(
            "📊 Fear & Greed Index\n"
            f"Score: {score}\n"
            f"Sentiment: {label}"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Kon Fear & Greed niet ophalen, probeer later opnieuw.\n"
            f"(debug: {e})"
        )


# --------- APP SETUP ---------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))

    print("✅ AstraScout bot gestart")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
