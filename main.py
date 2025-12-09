import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --------------------
# ENV VARS OPHALEN
# --------------------
BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

CRYPTO_API_URL = os.getenv("CRYPTO_API_URL") # bv. https://astrascout-crypto-api.p.rapidapi.com/price
CRYPTO_API_HOST = os.getenv("CRYPTO_API_HOST") # bv. astrascout-crypto-api.p.rapidapi.com

INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL") # bv. https://astrascout-market-insights-api.p.rapidapi.com/feargreed
INSIGHTS_API_HOST = os.getenv("INSIGHTS_API_HOST") # bv. astrascout-market-insights-api.p.rapidapi.com

# --------------------
# BASIC CHECKS
# --------------------
if not BOT_TOKEN:
    raise ValueError("ASTRASCOUT_BOT_TOKEN ontbreekt in Railway variables")

if not RAPIDAPI_KEY:
    raise ValueError("RAPIDAPI_KEY ontbreekt in Railway variables")

if not CRYPTO_API_URL or not CRYPTO_API_HOST:
    raise ValueError("CRYPTO_API_URL of CRYPTO_API_HOST ontbreekt in Railway variables")

if not INSIGHTS_API_URL or not INSIGHTS_API_HOST:
    raise ValueError("INSIGHTS_API_URL of INSIGHTS_API_HOST ontbreekt in Railway variables")


# --------------------
# COMMANDS
# --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /start command """
    await update.message.reply_text(
        "🤖 AstraScout Crypto Bot\n\n"
        "Commands:\n"
        "/price BTC - prijs voor een token\n"
        "/feargreed - Fear & Greed Index"
    )


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /price <symbol> via RapidAPI price endpoint """
    if not context.args:
        await update.message.reply_text("Gebruik: /price BTC")
        return

    symbol = context.args[0].upper()

    # CRYPTO_API_URL = .../price
    url = f"{CRYPTO_API_URL}/{symbol}"

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": CRYPTO_API_HOST,
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()

        # afhankelijk van jouw API: 'price' of 'price_usd'
        price = data.get("price") or data.get("price_usd")

        if price is None:
            await update.message.reply_text("❌ Geen prijs gevonden voor dat symbool.")
            return

        await update.message.reply_text(f"💰 {symbol}: ${price}")
    except Exception as e:
        # log naar Railway logs
        print(f"Error in /price: {e}")
        await update.message.reply_text("❌ Kon prijs niet ophalen (RapidAPI).")


async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /feargreed via RapidAPI insights endpoint """
    url = INSIGHTS_API_URL

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": INSIGHTS_API_HOST,
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()

        # afhankelijk van jouw response structuur:
        # in jouw eigen API was dit: fear_greed_index + classification
        score = data.get("fear_greed_index")
        label = data.get("classification")

        if score is None and isinstance(data, dict) and "fear_greed" in data:
            # falls back als /market/insights-achtige structuur gebruikt wordt
            inner = data.get("fear_greed", {})
            score = inner.get("fear_greed_index")
            label = inner.get("classification")

        if score is None:
            await update.message.reply_text("❌ Geen Fear & Greed data gevonden.")
            return

        await update.message.reply_text(
            f"📊 Fear & Greed Index\n"
            f"Score: {score}\n"
            f"Sentiment: {label}"
        )
    except Exception as e:
        print(f"Error in /feargreed: {e}")
        await update.message.reply_text("❌ Kon Fear & Greed niet ophalen (RapidAPI).")


# --------------------
# MAIN
# --------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))

    print("✅ AstraScoutCryptobot gestart via RapidAPI")
    app.run_polling() # geen extra opties → dit werkte bij jou al

if __name__ == "__main__":
    main()
