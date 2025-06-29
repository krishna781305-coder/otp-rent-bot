
import telebot
import requests
import time

# === CONFIG ===
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
FIVESIM_API_KEY = "YOUR_5SIM_API_KEY"
ADMIN_ID = 123456789  # Replace with your Telegram ID

bot = telebot.TeleBot(BOT_TOKEN)
user_balances = {}  # Example: {user_id: balance}

# === COMMAND: /start ===
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Welcome to OTP Rent Bot!\nUse /buy to rent number.\nCheck /balance.")

# === COMMAND: /balance ===
@bot.message_handler(commands=['balance'])
def balance(message):
    user_id = message.from_user.id
    bal = user_balances.get(user_id, 0)
    bot.reply_to(message, f"💰 Your Balance: ₹{bal}")

# === COMMAND: /buy ===
@bot.message_handler(commands=['buy'])
def buy_number(message):
    user_id = message.from_user.id
    balance = user_balances.get(user_id, 0)

    if balance < 5:
        bot.reply_to(message, "❌ Not enough balance. Use /topup")
        return

    # === Request number from 5sim ===
    headers = {
        "Authorization": f"Bearer {FIVESIM_API_KEY}"
    }

    url = "https://5sim.net/v1/user/buy/activation/india/any/telegram"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        bot.reply_to(message, "⚠️ Error getting number.")
        return

    data = response.json()
    phone = data['phone']
    id_ = data['id']
    user_balances[user_id] = balance - 5

    bot.send_message(user_id, f"📱 Your Number: {phone}\nWaiting for OTP...")

    # === Check for OTP ===
    for _ in range(30):
        time.sleep(5)
        check_url = f"https://5sim.net/v1/user/check/{id_}"
        r = requests.get(check_url, headers=headers).json()

        if r.get("sms"):
            otp = r["sms"][0]["code"]
            bot.send_message(user_id, f"✅ OTP Received: {otp}")
            return

    # If no OTP received
    bot.send_message(user_id, "❌ OTP not received. Refunding ₹5.")
    user_balances[user_id] += 5

# === COMMAND: /topup (admin only) ===
@bot.message_handler(commands=['topup'])
def topup(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.reply_to(message, "❌ Only admin can top up.")
        return

    try:
        _, uid, amt = message.text.split()
        uid = int(uid)
        amt = int(amt)
        user_balances[uid] = user_balances.get(uid, 0) + amt
        bot.reply_to(message, f"✅ Added ₹{amt} to user {uid}.")
    except:
        bot.reply_to(message, "❌ Format: /topup user_id amount")

# === RUN ===
bot.polling()
