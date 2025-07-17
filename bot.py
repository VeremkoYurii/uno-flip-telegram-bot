import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Отримуємо токен з змінної середовища
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Environment variable BOT_TOKEN is not set")

# URL твого вебхука (постав сюди URL твого Render додатка)
WEBHOOK_URL = "https://uno-flip-telegram-bot.onrender.com/webhook"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Це UNO Flip бот.")

# Відповідь на текстові повідомлення
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

async def main():
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    # Обробники команд і повідомлень
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Запуск webhook сервера
    port = int(os.environ.get("PORT", 8443))  # Render зазвичай задає PORT в середовищі
    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=WEBHOOK_URL,
        path="/webhook"
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
