import os
import requests

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ========= ENV VARS INLEZEN =========

BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")

CRYPTO_API_URL = os.getenv("CRYPTO_API_URL") # bv: https://astrascout-crypto-api.p.rapidapi.com/price
CRYPTO_API_HOST = os.getenv("CRYPTO_API_HOST") # bv: astrascout-crypto-api.p.rapidapi.com

INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL") # bv: https://astrascout-market-insights-api.p.rapidapi.com/feargreed
INSIGHTS_API_HOST = os.getenv("INSIGHTS_API_HOST") # bv: astrascout-market-insights-api.p.rapidapi.com

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") # ID van je kanaal / chat


# ========= BASIC CHECKS =========

if not BOT_TOKEN:
    raise ValueError("ASTRASCOUT_BOT_TOKEN ontbreekt in Railway variables")

if not RAPID_API_KEY:
    raise ValueError("RAPID_API_KEY ontbreekt in Railway variables")

if not CRYPTO_API_URL or not CRYPTO_API_HOST:
    raise ValueError("CRYPTO_API_URL of CRYPTO_API_HOST ontbreekt in Railway variables")

if not INSIGHTS_API_URL or not INSIGHTS_API_HOST:
    raise ValueError("INSIGHTS_API_URL of INSIGHTS_API_HOST ontbreekt in Railway variables")

if not TELEGRAM_CHAT_ID:
    raise ValueError("TELEGRAM_CHAT_ID ontbreekt in Railway variables")


# ========= HELPERS =========

def rapid_headers(host: str) -> dict:
    """Headers voor alle RapidAPI calls."""
    return {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": host,
    }


# ========= COMMANDS =========

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
        # Voorbeeld: CRYPTO_API_URL = https://astrascout-crypto-api.p.rapidapi.com/price
        resp = requests.get(
            f"{CRYPTO_API_URL}/{symbol}",
            headers=rapid_headers(CRYPTO_API_HOST),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        # Verwachte shape: { "token": "BTC", "price_usd": 90305, "source": "coingecko" }
        price_usd = data.get("price_usd")
        source = data.get("source", "unknown")

        if price_usd is None:
            raise Exception(f"Geen 'price_usd' veld in response: {data}")

        await update.message.reply_text(
            f"💰 {symbol}: ${price_usd}\nBron: {source}"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Kon prijs niet ophalen, probeer later opnieuw.\n"
            f"(debug: {e})"
        )


async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # INSIGHTS_API_URL bv: https://astrascout-market-insights-api.p.rapidapi.com/feargreed
        resp = requests.get(
            INSIGHTS_API_URL,
            headers=rapid_headers(INSIGHTS_API_HOST),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        # Verwacht: { "fear_greed_index": 22, "classification": "Extreme Fear", "source": "alternative.me" }
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


# ========= PERIODIEKE UPDATE NAAR JE KANAAL =========

async def scheduled_update(context: ContextTypes.DEFAULT_TYPE):
    try:
        # BTC prijs via RapidAPI
        price_resp = requests.get(
            f"{CRYPTO_API_URL}/BTC",
            headers=rapid_headers(CRYPTO_API_HOST),
            timeout=10,
        )
        price_resp.raise_for_status()
        price_data = price_resp.json()
        btc_price = price_data.get("price_usd")
        price_source = price_data.get("source", "unknown")

        # Fear & Greed via RapidAPI
        fg_resp = requests.get(
            INSIGHTS_API_URL,
            headers=rapid_headers(INSIGHTS_API_HOST),
            timeout=10,
        )
        fg_resp.raise_for_status()
        fg_data = fg_resp.json()
        fg_score = fg_data.get("fear_greed_index")
        fg_label = fg_data.get("classification")

        message = (
            "📊 *AstraScout Market Update*\n\n"
            f"💰 BTC: ${btc_price} (bron: {price_source})\n"
            f"😨 Fear & Greed: {fg_score} ({fg_label})\n\n"
            "Powered by AstraScout APIs via RapidAPI"
        )

        await context.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as e:
        # Alleen loggen, niet laten crashen
        print("Scheduled job error:", e, flush=True)


# ========= MAIN =========

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))

    # JobQueue (elke 5 minuten een update naar je kanaal)
    job_queue = app.job_queue
    job_queue.run_repeating(
        scheduled_update,
        interval=300, # 5 minuten
        first=10, # eerste run na 10 seconden
    )

    print("✅ AstraScout bot gestart (met RapidAPI + scheduler)")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
