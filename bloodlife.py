import logging
import json
import os
import requests
from flask import Flask, request
from threading import Thread
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton, InputFile
)
from telegram.ext import (
    ApplicationBuilder, Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)

# Flask setup
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "🤖 BloodHelp Bot is alive!"

# Environment
BOT_TOKEN = "8019684115:AAH8Z9X_ZJDswpyTP4LetsPqG0IqWnyNGf8"
WEBHOOK_URL = "https://bloodlife-osn0.onrender.com/webhook"
DB_FILE = "donors.json"
ADMIN_ID = 7961164240

# App
app = ApplicationBuilder().token(BOT_TOKEN).build()


# Logging
logging.basicConfig(level=logging.INFO)

# States
(
    NAME, AGE, BLOOD_GROUP, CITY, LOCATION, PHONE, SOCIAL, WEIGHT,
    LAST_DONATION, AVAILABILITY, BODY_PROBLEMS, MEDICAL_PROBLEMS, POLICY
) = range(13)

donors = {}
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        donors = json.load(f)

active_users = set()

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(donors, f, indent=2)

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    active_users.add(update.effective_user.id)
    keyboard = [
        [KeyboardButton("🩸 I Wanna Be a Donor")],
        [KeyboardButton("🆘 I Need a Donor")],
        [KeyboardButton("👤 My Profile")]
    ]
    await update.message.reply_text(
        "👋 Welcome to BloodHelp Bot!\n❤️ You can:\n• Register as a donor\n• Search for donors\n• View/edit your profile",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "Donor" in text:
        await update.message.reply_text("Please enter your Full Name:", reply_markup=ReplyKeyboardRemove())
        return NAME
    elif "Need" in text:
        await update.message.reply_text("🔍 Feature coming soon.")
        return ConversationHandler.END
    elif "Profile" in text:
        user_id = str(update.effective_user.id)
        if user_id not in donors:
            await update.message.reply_text("❌ You are not registered yet.")
            return ConversationHandler.END
        profile = donors[user_id]
        details = "\n".join([
            f"👤 Name: {profile.get('name')}",
            f"🎂 Age: {profile.get('age')}",
            f"🩸 Blood Group: {profile.get('blood_group')}",
            f"🏙️ City: {profile.get('city')}",
            f"📞 Phone: {profile.get('phone')}",
            f"💪 Weight: {profile.get('weight')}kg",
            f"🕓 Last Donation: {profile.get('last_donation')}",
            f"📍 Available: {'Yes' if profile.get('available') else 'No'}",
            f"📱 Social: {profile.get('social')}",
            f"⚠️ Body Issues: {profile.get('body_issues')}",
            f"🏥 Medical Issues: {profile.get('medical_issues')}"
        ])
        await update.message.reply_text(f"📋 Your Profile:\n\n{details}")
        return ConversationHandler.END

async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in donors:
        await update.message.reply_text("❌ You are not registered yet.")
        return ConversationHandler.END
    context.user_data.update(donors[user_id])
    await update.message.reply_text("Let's update your profile. Enter your Full Name:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text("Enter your Age (18-60):")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text.strip())
        if not (18 <= age <= 60):
            raise ValueError
        context.user_data['age'] = age
        buttons = [[InlineKeyboardButton(bg, callback_data=bg)] for bg in ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]]
        await update.message.reply_text("Select your Blood Group:", reply_markup=InlineKeyboardMarkup(buttons))
        return BLOOD_GROUP
    except:
        await update.message.reply_text("❗ Age must be between 18 and 60.")
        return AGE

async def get_blood_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data['blood_group'] = update.callback_query.data
    await update.callback_query.edit_message_text("Enter your City:")
    return CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['city'] = update.message.text.strip()
    await update.message.reply_text("📍 Share your location:", reply_markup=ReplyKeyboardMarkup([
        [KeyboardButton("📍 Share Location", request_location=True)]
    ], resize_keyboard=True))
    return LOCATION

async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    context.user_data['location'] = {'lat': location.latitude, 'lon': location.longitude}
    await update.message.reply_text("📞 Share your phone number:", reply_markup=ReplyKeyboardMarkup([
        [KeyboardButton("📞 Share Contact", request_contact=True)]
    ], resize_keyboard=True))
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    context.user_data['phone'] = contact.phone_number
    await update.message.reply_text("Social link? (or type 'skip'):")
    return SOCIAL

async def get_social(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['social'] = update.message.text if update.message.text.lower() != 'skip' else ""
    await update.message.reply_text("Weight (min 45kg):")
    return WEIGHT

async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        w = int(update.message.text.strip())
        if w < 45: raise ValueError
        context.user_data['weight'] = w
        await update.message.reply_text("Last donation date (YYYY-MM-DD):")
        return LAST_DONATION
    except:
        await update.message.reply_text("❗ Must be 45kg or more.")
        return WEIGHT

async def get_last_donation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['last_donation'] = update.message.text
    await update.message.reply_text("Available to donate now?", reply_markup=ReplyKeyboardMarkup([
        [KeyboardButton("✅ Available"), KeyboardButton("❌ Not Available")]
    ], resize_keyboard=True))
    return AVAILABILITY

async def get_availability(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['available'] = update.message.text.startswith("✅")
    await update.message.reply_text("Any body issues? (or 'none'):")
    return BODY_PROBLEMS

async def get_body_issues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['body_issues'] = update.message.text.strip()
    await update.message.reply_text("Any medical issues? (or 'none'):")
    return MEDICAL_PROBLEMS

async def get_medical_issues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['medical_issues'] = update.message.text.strip()
    await update.message.reply_text(
        "*Blood Donation Policy*\n\n"
        "1. Fit and healthy\n2. Age 18-60\n3. Data may be shared with seekers\n\n"
        "✅ Do you accept this?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ I Accept", callback_data="accept_policy")]])
    )
    return POLICY

async def accept_policy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    user_id = str(update.effective_user.id)
    context.user_data['accepted_policy'] = True
    donors[user_id] = context.user_data.copy()
    save_db()
    await update.callback_query.edit_message_text("🎉 You are registered as a donor!")
    return ConversationHandler.END

# Admin
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = " ".join(context.args)
    for uid in active_users:
        try:
            await context.bot.send_message(uid, f"📢 {msg}")
        except: pass

async def download_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_document(document=InputFile(DB_FILE))

async def view_active(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text(f"Active users: {len(active_users)}")

# Telegram Route
@flask_app.route("/webhook", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), app.bot)
    app.update_queue.put_nowait(update)
    return "OK"

# Register handlers
conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
        BLOOD_GROUP: [CallbackQueryHandler(get_blood_group)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
        LOCATION: [MessageHandler(filters.LOCATION, get_location)],
        PHONE: [MessageHandler(filters.CONTACT, get_phone)],
        SOCIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_social)],
        WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weight)],
        LAST_DONATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_last_donation)],
        AVAILABILITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_availability)],
        BODY_PROBLEMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_body_issues)],
        MEDICAL_PROBLEMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_medical_issues)],
        POLICY: [CallbackQueryHandler(accept_policy, pattern="^accept_policy$")]
    },
    fallbacks=[]
)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("editprofile", edit_profile))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("download_db", download_db))
app.add_handler(CommandHandler("view_active", view_active))
app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(accept_policy, pattern="^accept_policy$"))

# Run everything
Thread(target=lambda: flask_app.run(host="0.0.0.0", port=8080)).start()

# Set webhook
resp = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}")
print("Webhook set response:", resp.json())

# Final init
app.initialize()
app.post_init()
