import os
import logging
import aiohttp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ─── Logging ─────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── ENV ─────────────────────────────────────────────────
BOT_TOKEN = os.getenv("ASTRASCOUT_BOT_TOKEN")
CRYPTO_API_URL = os.getenv("CRYPTO_API_URL")
INSIGHTS_API_URL = os.getenv("INSIGHTS_API_URL")

if not BOT_TOKEN:
    raise ValueError("ASTRASCOUT_BOT_TOKEN ontbreekt")

# ─── Commands ────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("✅ /start ontvangen")
    await update.message.reply_text(
        "🤖 AstraScout Crypto Bot\n\n"
        "Commands:\n"
        "/price BTC\n"
        "/feargreed"
    )

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/price command: {context.args}")

    if not context.args:
        await update.message.reply_text("Gebruik: /price BTC")
        return

    symbol = context.args[0].upper()
    url = f"{CRYPTO_API_URL}/{symbol}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as r:
                data = await r.json()

        price = data.get("price")
        if not price:
            raise Exception("Geen prijs gevonden")

        await update.message.reply_text(f"💰 {symbol}: ${price}")

    except Exception as e:
        logger.error(f"Prijs fout: {e}")
        await update.message.reply_text("❌ Kon prijs niet ophalen")

async def feargreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("✅ /feargreed ontvangen")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(INSIGHTS_API_URL, timeout=10) as r:
                data = await r.json()

        score = data.get("fear_greed_index")
        label = data.get("label")

        await update.message.reply_text(
            f"📊 Fear & Greed Index\n"
            f"Score: {score}\n"
            f"Sentiment: {label}"
        )

    except Exception as e:
        logger.error(f"FearGreed fout: {e}")
        await update.message.reply_text("❌ Kon Fear & Greed niet ophalen")

# ─── Main ────────────────────────────────────────────────
def main():
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("feargreed", feargreed))

    logger.info("🚀 AstraScout bot gestart")

    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )

if __name__ == "__main__":
    main()
