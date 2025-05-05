from fastapi import FastAPI, Request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext
import os
import requests
from dotenv import load_dotenv
load_dotenv()

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
LLM_API_KEY = os.getenv("LLM_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL") 

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN tidak ditemukan di environment.")
if not LLM_API_KEY:
    raise ValueError("LLM_API_KEY tidak ditemukan di environment.")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL tidak ditemukan di environment.")

bot = Bot(token=BOT_TOKEN)
app = FastAPI()

# Dispatcher to handle updates
dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

# Start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Halo! Saya bot LLM Telkom.")

# Message handler
def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text

    headers = {
        "x-api-key": LLM_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "model": os.getenv("LLM_API_MODEL"),
        "messages": [
            {"role": "system", "content": ""},
            {"role": "user", "content": user_message}
        ]
    }

    try:
        response = requests.post(
            os.getenv("LLM_API_URL"),
            json=payload,
            headers=headers
        )
        llm_reply = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        llm_reply = f"Terjadi kesalahan: {str(e)}"

    update.message.reply_text(llm_reply)

# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# Health check endpoint
@app.get("/")
def root():
    return {"status": "ok"}

# Telegram webhook receiver
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)
    dispatcher.process_update(update)
    return {"status": "processed"}

# Endpoint to set webhook via API call
@app.get("/set-webhook")
def set_webhook():
    set_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    response = requests.get(set_url, params={"url": WEBHOOK_URL})
    result = response.json()
    return {
        "webhook_set": result.get("ok", False),
        "description": result.get("description", "No description"),
        "url": WEBHOOK_URL
    }
