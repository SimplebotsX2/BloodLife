import logging
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
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

(
    NAME, AGE, BLOOD_GROUP, CITY, LOCATION, PHONE, SOCIAL, WEIGHT,
    LAST_DONATION, AVAILABILITY, BODY_PROBLEMS, MEDICAL_PROBLEMS, CONFIRM, POLICY
) = range(14)

ADMIN_ID = 7961164240  # Replace with your Telegram ID

DB_FILE = "donors.json"
donors = {}
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        donors = json.load(f)

active_users = set()

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(donors, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    active_users.add(update.effective_user.id)
    keyboard = [
        [KeyboardButton("🩸 I Wanna Be a Donor")],
        [KeyboardButton("🆘 I Need a Donor")],
        [KeyboardButton("👤 My Profile")]
    ]
    await update.message.reply_text(
        "👋 Welcome to BloodHelp Bot!\n❤️ Here you can\n• Register as a blood donor🩸\n• Find donors in your city🧭\n• View and update your profile 👤\n\nPlease choose an option:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "Donor" in text:
        await update.message.reply_text("Please enter your Full Name:", reply_markup=ReplyKeyboardRemove())
        return NAME
    elif "Need a Donor" in text:
        await update.message.reply_text("🔍 Feature coming soon: Search for donors.")
        return ConversationHandler.END
    elif "Profile" in text:
        user_id = str(update.effective_user.id)
        if user_id not in donors:
            await update.message.reply_text("❌ You are not registered yet. Please register first.")
            return ConversationHandler.END
        profile = donors[user_id]
        text = "\n".join([
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
        await update.message.reply_text(
            f"Here is your profile:\n\n{text}\n\nTo update, type /editprofile",
            reply_markup=ReplyKeyboardRemove()
        )
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
        buttons = [[InlineKeyboardButton(bg, callback_data=bg)] for bg in [
            "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Bombay", "INRA", "Lutheran", "Duffy"]]
        await update.message.reply_text("Select your Blood Group:", reply_markup=InlineKeyboardMarkup(buttons))
        return BLOOD_GROUP
    except ValueError:
        await update.message.reply_text("❗ Please enter a valid age between 18 and 60.")
        return AGE

async def get_blood_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['blood_group'] = query.data
    await query.edit_message_text("Enter your City:")
    return CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['city'] = update.message.text.strip()
    await update.message.reply_text(
        "📍 Please share your current location:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📍 Share Location", request_location=True)]], resize_keyboard=True
        )
    )
    return LOCATION

async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    context.user_data['location'] = {'lat': location.latitude, 'lon': location.longitude}
    await update.message.reply_text(
        "📞 Please share your contact number:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📞 Share Contact", request_contact=True)]], resize_keyboard=True
        )
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    context.user_data['phone'] = contact.phone_number
    await update.message.reply_text("Optional: Share your social media link (or type 'skip'):")
    return SOCIAL

async def get_social(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data['social'] = text if text.lower() != 'skip' else ""
    await update.message.reply_text("Enter your weight in KG:")
    return WEIGHT

async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = int(update.message.text.strip())
        if weight < 45:
            raise ValueError
        context.user_data['weight'] = weight
        await update.message.reply_text("Enter your last donation date (YYYY-MM-DD):")
        return LAST_DONATION
    except ValueError:
        await update.message.reply_text("❗ Weight must be at least 45kg.")
        return WEIGHT

async def get_last_donation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['last_donation'] = update.message.text.strip()
    await update.message.reply_text(
        "Are you currently available to donate?",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("✅ Available"), KeyboardButton("❌ Not Available")]
        ], resize_keyboard=True)
    )
    return AVAILABILITY

async def get_availability(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['available'] = update.message.text.startswith("✅")
    await update.message.reply_text("Any body-related problems? (or type 'none')")
    return BODY_PROBLEMS

async def get_body_issues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['body_issues'] = update.message.text.strip()
    await update.message.reply_text("Any medical conditions? (or type 'none')")
    return MEDICAL_PROBLEMS

async def get_medical_issues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['medical_issues'] = update.message.text.strip()
    policy_text = (
        "📜 *Blood Donation Policy*\n\n"
        "By registering as a donor, you agree to the following:\n"
        "1. You are donating voluntarily and are medically fit to donate.\n"
        "2. You are between 18 and 60 years of age and above 45kg in weight.\n"
        "3. You will not provide false or misleading information.\n"
        "4. You understand your data will be shared with potential recipients.\n"
        "5. You can request removal of your data at any time.\n\n"
        "Do you accept the above policy?"
    )
    await update.message.reply_text(
        policy_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ I Accept", callback_data="accept_policy")]
        ]),
        parse_mode="Markdown"
    )
    return POLICY

async def accept_policy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    context.user_data['accepted_policy'] = True
    donors[user_id] = context.user_data.copy()
    save_db()
    await query.edit_message_text("🎉 Congratulations! You have successfully registered as a donor. Thank you for saving lives! 💖")
    return ConversationHandler.END

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
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("download_db", download_db))
app.add_handler(CommandHandler("view_active", view_active))
app.add_handler(CommandHandler("editprofile", edit_profile))
app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(accept_policy, pattern="^accept_policy$"))

print("Bot is running...")
app.run_polling()