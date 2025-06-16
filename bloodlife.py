import os
import json
from datetime import datetime
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

import asyncio

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_IDS = [123456789]  # Replace with real admin IDs
DATA_FILE = "donors.json"
WEBHOOK_PATH = f"/{BOT_TOKEN}"
WEBHOOK_URL = f"https://bloodlife-7e7l.onrender.com{WEBHOOK_PATH}"

# ---------- Data Utils ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def is_admin(user_id):
    return user_id in ADMIN_IDS

# ---------- Bot Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("🩸 Register as Donor")],
        [KeyboardButton("🔍 Search Donors")],
        [KeyboardButton("📄 My Profile")],
        [KeyboardButton("📢 Admin Panel")] if is_admin(update.effective_user.id) else []
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    welcome_text = (
        "👋 Welcome to *BloodLife Bot*!\n\n"
        "🩸 *Save lives* by becoming a donor or find nearby blood donors in need.\n\n"
        "📌 Use the menu below to begin."
    )

    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def register_donor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    blood_buttons = [
        [InlineKeyboardButton("A+", callback_data="blood_A+"), InlineKeyboardButton("A-", callback_data="blood_A-")],
        [InlineKeyboardButton("B+", callback_data="blood_B+"), InlineKeyboardButton("B-", callback_data="blood_B-")],
        [InlineKeyboardButton("AB+", callback_data="blood_AB+"), InlineKeyboardButton("AB-", callback_data="blood_AB-")],
        [InlineKeyboardButton("O+", callback_data="blood_O+"), InlineKeyboardButton("O-", callback_data="blood_O-")]
    ]
    await update.message.reply_text(
        "🩸 Choose your blood group:",
        reply_markup=InlineKeyboardMarkup(blood_buttons)
    )

async def blood_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    blood_group = query.data.split("_")[1]
    user_id = str(query.from_user.id)

    data = load_data()
    if user_id not in data:
        data[user_id] = {}

    data[user_id]["blood_group"] = blood_group
    data[user_id]["name"] = query.from_user.full_name
    data[user_id]["registered_at"] = datetime.now().isoformat()
    data[user_id]["available"] = True

    save_data(data)

    await query.edit_message_text(
        f"✅ Blood group *{blood_group}* saved!\n\n"
        f"Your registration is almost done. Type your *city name* to complete.",
        parse_mode="Markdown"
    )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    message = update.message.text

    data = load_data()
    if user_id in data and "city" not in data[user_id]:
        data[user_id]["city"] = message
        save_data(data)
        await update.message.reply_text("✅ Registration completed!")
        return

    if message == "🩸 Register as Donor":
        await register_donor(update, context)

    elif message == "🔍 Search Donors":
        await update.message.reply_text(
            "📍 Please send your location so we can find nearby donors.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📍 Send Location", request_location=True)]],
                resize_keyboard=True
            )
        )

    elif message == "📄 My Profile":
        profile = data.get(user_id)
        if not profile:
            await update.message.reply_text("❌ No profile found. Please register first.")
            return
        text = (
            f"👤 *Name:* {profile.get('name')}\n"
            f"🩸 *Blood Group:* {profile.get('blood_group')}\n"
            f"🏙 *City:* {profile.get('city', 'N/A')}\n"
            f"✅ *Available:* {'Yes' if profile.get('available') else 'No'}"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    elif message == "📢 Admin Panel" and is_admin(update.effective_user.id):
        count = len(load_data())
        await update.message.reply_text(f"👑 Admin Panel\n\nTotal Donors: {count}")

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_location = update.message.location
    data = load_data()
    results = [v for v in data.values() if v.get("available")]

    if results:
        reply = "🩸 Available Donors:\n\n"
        for donor in results:
            reply += f"👤 {donor.get('name')} - {donor.get('blood_group')} - {donor.get('city')}\n"
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("❌ No donors found nearby.")

# ---------- Flask Setup ----------
flask_app = Flask(__name__)
bot_app = None  # Telegram app will be initialized in async context

@flask_app.route('/')
def index():
    return '🩸 BloodLife Bot is running!'

@flask_app.route(WEBHOOK_PATH, methods=['POST'])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot_app.bot)
        await bot_app.update_queue.put(update)
        return "OK"

# ---------- Init Bot ----------
async def init_bot():
    global bot_app
    bot_app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(blood_selection))
    bot_app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    await bot_app.bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook set to: {WEBHOOK_URL}")

# ---------- Main ----------
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_bot())

    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)
