import os
import requests
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# 🔐 Environment variabelen
BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")

CRYPTO_API_URL = os.getenv("CRYPTO_API_URL") # bijv. https://astrascout-crypto-api.../price
CRYPTO_API_HOST = os.getenv("CRYPTO_API_HOST") # host uit RapidAPI docs

INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL") # bijv. https://astrascout-market-insights.../feargreed
INSIGHTS_API_HOST = os.getenv("INSIGHTS_API_HOST")

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") # je kanaal-ID of chat-ID

# ✅ Sanity checks
if not BOT_TOKEN:
    raise ValueError("ASTRASCOUT_BOT_TOKEN ontbreekt")
if not RAPID_API_KEY:
    raise ValueError("RAPID_API_KEY ontbreekt")
if not CRYPTO_API_URL or not CRYPTO_API_HOST:
    raise ValueError("CRYPTO_API_URL of CRYPTO_API_HOST ontbreekt")
if not INSIGHTS_API_URL or not INSIGHTS_API_HOST:
    raise ValueError("INSIGHTS_API_URL of INSIGHTS_API_HOST ontbreekt")
if not TELEGRAM_CHAT_ID:
    print("⚠️ TELEGRAM_CHAT_ID niet gezet; scheduled updates werken dan niet.")

def rapid_headers(host: str) -> dict:
    return {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": host,
    }

# ───────────── Commands ─────────────

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
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()

        # Jouw API gebruikt price_usd (price als fallback just in case)
        price_val = data.get("price_usd") or data.get("price")
        source = data.get("source", "unknown")

        if price_val is None:
            raise ValueError(f"Geen prijs in response: {data}")

        await update.message.reply_text(
            f"💰 {symbol}: ${price_val}\nSource: {source}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Kon prijs niet ophalen.\n(debug: {e})")

async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(
            INSIGHTS_API_URL,
            headers=rapid_headers(INSIGHTS_API_HOST),
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()

        score = data.get("fear_greed_index") or data.get("score")
        label = data.get("classification") or data.get("label")

        await update.message.reply_text(
            "📊 Fear & Greed Index\n"
            f"Score: {score}\n"
            f"Sentiment: {label}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Kon Fear & Greed niet ophalen.\n(debug: {e})")

# ───────────── Scheduled job ─────────────

async def scheduled_update(context: ContextTypes.DEFAULT_TYPE):
    try:
        # BTC prijs via RapidAPI
        r_price = requests.get(
            f"{CRYPTO_API_URL}/BTC",
            headers=rapid_headers(CRYPTO_API_HOST),
            timeout=10,
        )
        r_price.raise_for_status()
        p_data = r_price.json()
        btc_price = p_data.get("price_usd") or p_data.get("price")

        # Fear & Greed via RapidAPI
        r_fg = requests.get(
            INSIGHTS_API_URL,
            headers=rapid_headers(INSIGHTS_API_HOST),
            timeout=10,
        )
        r_fg.raise_for_status()
        fg_data = r_fg.json()
        fg_score = fg_data.get("fear_greed_index") or fg_data.get("score")
        fg_label = fg_data.get("classification") or fg_data.get("label")

        message = (
            "📊 *AstraScout Market Update*\n\n"
            f"💰 BTC Price: ${btc_price}\n"
            f"😨 Fear & Greed: {fg_score} ({fg_label})\n\n"
            "Powered by AstraScout APIs"
        )

        if not TELEGRAM_CHAT_ID:
            print("⚠️ TELEGRAM_CHAT_ID niet gezet, kan geen scheduled message sturen.")
            return

        await context.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        print("Scheduled job error:", e)

# ───────────── Main ─────────────

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))

    # JobQueue voor auto-update elke 5 minuten
    if app.job_queue:
        app.job_queue.run_repeating(
            scheduled_update,
            interval=300, # 5 minuten
            first=10, # eerste run na 10 seconden
        )
        print("✅ JobQueue geactiveerd (5-minuten updates).")
    else:
        print("⚠️ Geen JobQueue beschikbaar – heb je wel python-telegram-bot[job-queue] geïnstalleerd?")

    print("✅ AstraScoutCryptoBot gestart.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
