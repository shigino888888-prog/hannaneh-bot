import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT", "تو یک دستیار هوش مصنوعی هستی.")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("متغیر محیطی TELEGRAM_BOT_TOKEN تنظیم نشده است.")
if not GROQ_API_KEY:
    raise RuntimeError("متغیر محیطی GROQ_API_KEY تنظیم نشده است.")

groq_client = Groq(api_key=GROQ_API_KEY)
user_history = {}
MAX_HISTORY_MESSAGES = 30

def get_or_create_history(user_id: int) -> list:
    if user_id not in user_history:
        user_history[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return user_history[user_id]

def trim_history(history: list) -> list:
    system_message = history[0]
    conversation = history[1:]
    if len(conversation) > MAX_HISTORY_MESSAGES:
        conversation = conversation[-MAX_HISTORY_MESSAGES:]
    return [system_message] + conversation

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_or_create_history(user_id)
    await update.message.reply_text("سلام! من حنانه هستم. چطور می‌تونم کمکت کنم؟")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاک کردن تاریخچه گفتگوی کاربر."""
    user_id = update.effective_user.id
    user_history[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    await update.message.reply_text("تاریخچه گفتگو پاک شد. می‌تونیم از اول شروع کنیم!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    history = get_or_create_history(user_id)
    history.append({"role": "user", "content": user_text})
    history = trim_history(history)
    user_history[user_id] = history
    try:
        response = groq_client.chat.completions.create(messages=history, model="llama-3.3-70b-versatile")
        bot_reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": bot_reply})
        user_history[user_id] = trim_history(history)
        await update.message.reply_text(bot_reply)
    except Exception as e:
        logger.error(f"Error while calling Groq API: {e}")
        await update.message.reply_text("مشکلی در پاسخگویی پیش آمد. لطفاً دوباره تلاش کنید.")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("ربات حنانه در حال اجرا است...")
    app.run_polling()

if __name__ == "__main__":
    main()
