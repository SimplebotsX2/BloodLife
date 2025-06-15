# 📨 BloodHelp Bot

**BloodHelp Bot** is a Telegram bot built with Python that helps people register as blood donors and allows recipients to request help easily. It stores donor details securely and allows users to manage their profiles.

## 🌟 Features

- 👤 Donor registration with full details
- 🦘 Request blood (coming soon)
- 📍 Location and contact collection
- ↺ Edit and view donor profile
- ✅ Age, weight, and health checks
- 📜 Policy acceptance before becoming a donor
- 📂 Admin commands:
  - `/broadcast` - Send a message to all active users
  - `/download_db` - Download donor database
  - `/view_active` - See count of active users

---

## 🛠️ Tech Stack

- Python 3.10+
- `python-telegram-bot` v20+
- JSON file storage (no database setup required)

---

## 📦 Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/bloodhelp-bot.git
   cd bloodhelp-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the bot**
   - Open the main Python file
   - Replace `YOUR_BOT_TOKEN_HERE` with your bot token
   - Set your Telegram user ID in `ADMIN_ID`

4. **Run the bot**
   ```bash
   python bot.py
   ```

---

## 📂 Project Structure

```
bloodhelp-bot/
├── donors.json              # Donor data storage
├── bot.py                   # Main bot logic
├── requirements.txt         # Python dependencies
└── README.md                # You are here!
```

---

## 🤖 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Launch the main menu |
| `/editprofile` | Edit your donor profile |
| `/broadcast <msg>` | (Admin) Send message to all users |
| `/download_db` | (Admin) Download donor data |
| `/view_active` | (Admin) Count active users |

---

## 🛡️ Disclaimer

This bot is for educational and humanitarian purposes only. Always verify donors manually before proceeding with any donation.

---

## 💖 Contributing

Want to improve this bot? Feel free to fork and send a pull request. Feature suggestions are welcome!

---

## 📬 Contact

- Telegram: [@happinessking52](https://t.me/happinessking52)
- Instagram: [Bass_lub_7](https://instagram.com/Bass_lub_7)

