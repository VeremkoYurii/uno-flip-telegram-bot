import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Увімкнення логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Токен бота
TOKEN = os.getenv("BOT_TOKEN")  # Бажано зберігати токен як секрет або змінну середовища

# Вебхук URL (заміни на свій actual Render URL)
WEBHOOK_URL = "https://your-app-name.onrender.com/webhook"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Це UNO Flip бот.")

# Відповідь на будь-яке повідомлення
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

# Основна функція
async def main():
    application = ApplicationBuilder().token(TOKEN).build()

    # Обробники
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Налаштування вебхука
    await application.bot.delete_webhook()
    await application.start()
    await application.bot.set_webhook(WEBHOOK_URL)
    await application.updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),  # Render автоматично задає PORT
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
