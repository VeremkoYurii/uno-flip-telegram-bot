from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters

# === Налаштуй токен і URL:
TOKEN = "8087847293:AAH5X3JU_gtgbFklAqNt_6co5j8lkW-NJrQ"  # 🔁 Замінити на твій токен
URL = "https://uno-flip-telegram-bot.onrender.com"  # 🔁 Замінити на свій домен Render

# === Ініціалізація:
bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

# === Обробка вхідних запитів від Telegram:
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# === Просто перевірка, що бот живий:
@app.route("/")
def index():
    return "UNO Flip Bot is alive!"

# === Обробники команд:
def start(update, context):
    update.message.reply_text("Привіт! Це UNO Flip бот.")

def echo(update, context):
    update.message.reply_text(update.message.text)

# === Dispatcher:
dispatcher = Dispatcher(bot, None, workers=0)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# === Запуск Flask і встановлення Webhook:
if __name__ == "__main__":
    import os
    from threading import Thread

    def run_flask():
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port)

    def set_webhook():
        bot.delete_webhook()
        bot.set_webhook(f"{URL}/{TOKEN}")

    Thread(target=run_flask).start()
    set_webhook()
