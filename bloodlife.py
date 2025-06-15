import logging
from flask import Flask
from threading import Thread
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes,
    ConversationHandler, CallbackQueryHandler
)
import json
import os

# Flask server to keep bot alive
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "🤖 BloodHelp Bot is alive!"

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)

# Logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
(
    NAME, AGE, BLOOD_GROUP, CITY, LOCATION, PHONE, SOCIAL, WEIGHT,
    LAST_DONATION, AVAILABILITY, BODY_PROBLEMS, MEDICAL_PROBLEMS, POLICY
) = range(13)

ADMIN_ID = 7961164240  # Your Telegram ID
DB_FILE = "donors.json"
donors = {}

# Load existing donors
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        donors = json.load(f)

active_users = set()

# Save DB
def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(donors, f, indent=2)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    active_users.add(update.effective_user.id)
    keyboard = [
        [KeyboardButton("🩸 I Wanna Be a Donor")],
        [KeyboardButton("🆘 I Need a Donor")],
        [KeyboardButton("👤 My Profile")]
    ]
    await update.message.reply_text(
        "👋 Welcome to BloodHelp Bot!\n❤️ You can:\n• Register as a donor\n• Search for donors\n• View/edit your profile\n\nPlease choose an option:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# Menu Handler
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "Donor" in text:
        await update.message.reply_text("Please enter your Full Name:", reply_markup=ReplyKeyboardRemove())
        return NAME
    elif "Need a Donor" in text:
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
        await update.message.reply_text(f"📋 Your Profile:\n\n{details}", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

# Profile Editing
async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in donors:
        await update.message.reply_text("❌ You are not registered yet.")
        return ConversationHandler.END
    context.user_data.update(donors[user_id])
    await update.message.reply_text("Let's update your profile. Enter your Full Name:")
    return NAME

# Form Handlers
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
        blood_buttons = [[InlineKeyboardButton(bg, callback_data=bg)] for bg in
            ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Bombay", "INRA", "Lutheran", "Duffy"]]
        await update.message.reply_text("Select your Blood Group:", reply_markup=InlineKeyboardMarkup(blood_buttons))
        return BLOOD_GROUP
    except:
        await update.message.reply_text("❗ Valid age is 18 to 60.")
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
    await update.message.reply_text("Optional: Share your social media link (or type 'skip'):")
    return SOCIAL

async def get_social(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['social'] = update.message.text.strip() if update.message.text.lower() != 'skip' else ""
    await update.message.reply_text("Enter your weight (minimum 45kg):")
    return WEIGHT

async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = int(update.message.text.strip())
        if weight < 45:
            raise ValueError
        context.user_data['weight'] = weight
        await update.message.reply_text("Last donation date (YYYY-MM-DD):")
        return LAST_DONATION
    except:
        await update.message.reply_text("❗ Weight must be 45kg or more.")
        return WEIGHT

async def get_last_donation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['last_donation'] = update.message.text.strip()
    await update.message.reply_text("Available to donate now?", reply_markup=ReplyKeyboardMarkup([
        [KeyboardButton("✅ Available"), KeyboardButton("❌ Not Available")]
    ], resize_keyboard=True))
    return AVAILABILITY

async def get_availability(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['available'] = update.message.text.startswith("✅")
    await update.message.reply_text("Any body issues? (or type 'none'):")
    return BODY_PROBLEMS

async def get_body_issues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['body_issues'] = update.message.text.strip()
    await update.message.reply_text("Any medical conditions? (or type 'none'):")
    return MEDICAL_PROBLEMS

async def get_medical_issues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['medical_issues'] = update.message.text.strip()
    policy = (
        "*Blood Donation Policy*\n\n"
        "1. You are fit and willing.\n"
        "2. Age: 18-60, Weight: 45+ kg\n"
        "3. Your data may be shared with recipients.\n\n"
        "✅ Do you accept this policy?"
    )
    await update.message.reply_text(
        policy,
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
    await update.callback_query.edit_message_text("🎉 Registered as a donor! Thank you! 💖")
    return ConversationHandler.END

# Admin Commands
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    message = " ".join(context.args)
    for uid in active_users:
        try:
            await context.bot.send_message(uid, f"📢 {message}")
        except:
            continue

async def download_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        with open(DB_FILE, 'rb') as f:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=InputFile(f, filename=DB_FILE))

async def view_active(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text(f"👥 Active Users: {len(active_users)}")

# Start Flask in background
Thread(target=run_flask).start()

# Start Telegram bot
app = ApplicationBuilder().token("8019684115:AAH8Z9X_ZJDswpyTP4LetsPqG0IqWnyNGf8").build()

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

print("Bot running with Flask background...")
app.run_polling()
