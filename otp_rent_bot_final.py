
import telebot
import requests
import time

# === CONFIG ===
BOT_TOKEN = "7680687552:AAHjupJ56p4EBuayfqb24ch781gdR46UtuY"
FIVESIM_API_KEY = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODI3MzA1NjcsImlhdCI6MTc1MTE5NDU2NywicmF5IjoiYWM0YWE1OTIxMGFjYmQyODUxNDc3OGUwZjM2MmU2MmMiLCJzdWIiOjMzMjI3NDV9.LYsbuaL1zMfMm6Afyny5Jhrgx8jF40wwGkXG7s6f-PtGlIDtIDTo9aGsSqsFmZYrhn7doFmFj76-yHNpF2pQIAjJ94xm4ifjAjKN8Qf91aasfnTGLnPGFEXi8PXJLhVb43MfJrLX_bPEnSySFIEyaejURAf3dXYqVgWs90XgpxGuY0INOHhXieP3VqDgPE1VF0qPeIMNRMBZ2Fa95ysoAS8zETnI1k_TF4n4zGaYT3AlJcKltJsIV3qUPAE2Xj-GHSQ_Ujj8TszFYwQl1d6_W22qir6XqkxV1Z0GY4ezvz2iOchflR_99p5TGBQfASqVeak8x1ZTgPpV6_flwDWxnw"
ADMIN_ID = 829211366  # Replace with your Telegram ID

bot = telebot.TeleBot(BOT_TOKEN)
user_balances = {}  # Example: {user_id: balance}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Welcome to OTP Rent Bot!\nUse /buy to rent number.\nCheck /balance.")

@bot.message_handler(commands=['balance'])
def balance(message):
    user_id = message.from_user.id
    bal = user_balances.get(user_id, 0)
    bot.reply_to(message, f"💰 Your Balance: ₹{bal}")

@bot.message_handler(commands=['buy'])
def buy_number(message):
    user_id = message.from_user.id
    balance = user_balances.get(user_id, 0)

    if balance < 5:
        bot.reply_to(message, "❌ Not enough balance. Use /topup")
        return

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

    for _ in range(30):
        time.sleep(5)
        check_url = f"https://5sim.net/v1/user/check/{id_}"
        r = requests.get(check_url, headers=headers).json()

        if r.get("sms"):
            otp = r["sms"][0]["code"]
            bot.send_message(user_id, f"✅ OTP Received: {otp}")
            return

    bot.send_message(user_id, "❌ OTP not received. Refunding ₹5.")
    user_balances[user_id] += 5

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

bot.polling()
