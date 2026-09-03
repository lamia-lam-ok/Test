import warnings
warnings.filterwarnings("ignore", category=Warning)

import requests
import json
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import os
import re
from datetime import datetime
import time
import asyncio
import random

# ============ CONFIGURATION ============
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN environment variable not set!")
    exit(1)

OWNER_ID = os.environ.get("OWNER_ID")
if OWNER_ID:
    OWNER_ID = int(OWNER_ID)

# ============ LOGGING ============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============ CONSTANTS ============
REFRESH_TOKEN = "AMf-vBx2NF07mspl6qH2dBUBNE0DWkwyrjMvqElbwXoq8fA07xd4oaTPho8OWo_wwCmACHqgWn7ZMKYOqiTV4_UX4P5xNT78c_uR-DHa1aqPw1zznx5LgZ03dA3biu9u9IEsvprr6mzDcSAvH7A9-bdIkVG_O2EeV92e2oswF-WniYoKDmRKUGfJ-PNOnWD0Ttg7jGsKk9XLbNQFsLpp4iQ6uGIgZ3OIhA"
TOKEN_URL = "https://securetoken.googleapis.com/v1/token?key=AIzaSyAtRVK71cLulaRpQCQ3C8YAB-jV5lQ-0kQ"
UNITECH_URL = "https://lookup.unitechapps.in/"

REQUIRED_CHANNEL = "@team420bd"
REQUIRED_GROUP = "@team_420_bd"

USER_DATA_FILE = "user_data.json"
FREE_CREDITS_PERIOD = 30
FREE_CREDITS_AMOUNT = 8
REFERRAL_REWARD = 2

# ============ OWNER NOTIFICATION ============
async def notify_owner(context, user, activity, extra=None):
    if not OWNER_ID:
        return
    if user.id == OWNER_ID:
        return
    name = user.full_name or "N/A"
    username = f"@{user.username}" if user.username else "N/A"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"📢 **User Activity**\n\n"
    msg += f"**Activity:** {activity}\n"
    msg += f"**Full Name:** {name}\n"
    msg += f"**Username:** {username}\n"
    msg += f"**User ID:** `{user.id}`\n"
    msg += f"**Timestamp:** {timestamp}\n"
    if extra:
        msg += f"\n**Extra Info:** {extra}"
    try:
        await context.bot.send_message(chat_id=OWNER_ID, text=msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Failed to notify owner: {e}")

# ============ TOKEN GENERATION ============
def _generate_random_headers():
    """Generate a random User-Agent, keep all other headers static."""
    base_headers = {
        "Content-Type": "application/json",
        "X-Android-Package": "com.uni.tech.numberlookup",
        "X-Android-Cert": "61ED377E85D386A8DFEE6B864BD85B0BFAA5AF81",
        "Accept-Language": "en-US",
        "X-Client-Version": "Android/Fallback/X24001000/FirebaseCore-Android",
        "X-Firebase-GMPID": "1:1067701877947:android:8c30e3edca32c5cd383d9e",
        "X-Firebase-Client": "H4sIAAAAAAAA_6tWykhNLCpJSk0sKVayio7VUSpLLSrOzM9TslIyUqoFAFyivEQfAAAA",
        "X-Firebase-AppCheck": "eyJlcnJvciI6IlVOS05PV05fRVJST1IifQ==",
        "Host": "securetoken.googleapis.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }
    
    device_models = [
        "SM-S921B", "SM-S928B", "SM-A556B", "SM-M546B", "SM-G991B",
        "SM-N986B", "SM-F956B", "SM-F731B", "SM-A356B",
        "iPhone15,2", "iPhone15,3", "iPhone16,1", "iPhone16,2",
        "Pixel-8-Pro", "Pixel-7-Pro", "Pixel-6", "Pixel-9-Pro",
        "M2011K2G", "M2101K9G", "2211133G", "23013PC75G",
        "OnePlus-12", "OnePlus-11", "OnePlus-10-Pro",
        "CPH2609", "CPH2451", "Find-X7-Pro", "Find-X5-Pro",
        "V2230", "V2244", "X90-Pro", "X100-Pro",
        "RMX3370", "RMX3841", "GT-Neo-5", "Realme-11-Pro",
        "XT2301-1", "Moto-G84", "Edge-40-Pro", "Edge-50-Ultra",
        "LYA-L09", "ELE-L29", "NOH-NX9", "P40-Pro",
        "Nothing-Phone-2", "Nothing-Phone-1",
        "XQ-DQ72", "Xperia-1-V", "Xperia-5-IV",
        "LG-V600", "LM-G900"
    ]
    android_versions = ["10", "11", "12", "13", "14", "15"]
    model = random.choice(device_models)
    version = random.choice(android_versions)
    build = "AP3A.240905.015.A2"
    user_agent = f"Dalvik/2.1.0 (Linux; U; Android {version}; {model} Build/{build})"
    
    headers = base_headers.copy()
    headers["User-Agent"] = user_agent
    return headers

def generate_access_token():
    try:
        headers = _generate_random_headers()
        data = {"grantType": "refresh_token", "refreshToken": REFRESH_TOKEN}
        response = requests.post(TOKEN_URL, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return response.json().get('access_token')
    except Exception as e:
        logger.error(f"Token generation failed: {e}")
        return None

# ============ UNITECH API ============
def unitech_lookup(number, access_token):
    try:
        url = "https://lookup.unitechapps.in/"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "Host": "lookup.unitechapps.in",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/4.12.0"
        }
        payload = {
            "code": "880",
            "number": number
        }
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Unitech API error: {e}")
        return None

# ============ FORMAT RESULT (UPDATED) ============
def format_result(number, unitech_data):
    result = []
    result.append("🔍 PHONE NUMBER LOOKUP RESULTS")
    result.append(f"📱 Number: +880{number}")
    result.append("=" * 50)
    result.append("")   # blank line

    result.append("📋 DAILY USAGES NAME:")
    if unitech_data and unitech_data.get('status') == True:
        data = unitech_data.get('data', {})
        full_name = data.get('fullName')
        other_names = data.get('otherNames', [])

        # Build a flat list of all names (fullName first, then otherNames)
        name_list = []
        if full_name:
            name_list.append(full_name)
        for item in other_names:
            name = item.get('name', '[Unnamed]')
            if name:
                name_list.append(name)

        if name_list:
            for idx, name in enumerate(name_list, start=1):
                result.append(f"✅ Name {idx}: {name}")
        else:
            result.append("❌ Name 1: Not Found")
            result.append("❌ Other Names: Not Found")
    else:
        result.append("❌ Information unavailable")

    result.append("")   # blank line before separator
    result.append("=" * 50)
    result.append(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    result.append("🤖 Bot Says: To find more names, multiple photos, and Social IDs without rate limit use our paid bot.")
    result.append("")
    result.append("💰 Our Paid Bot Price List 💰 ")
    result.append("")
    result.append("40 Credits = 50 tk (30 days)")
    result.append("100 Credits = 100 tk (30 days)")
    result.append("200 Credit = 170 tk (30 days)")
    result.append("")
    result.append("Admin Contact: @team420_contact_admin_bot")

    return "\n".join(result)

# ============ MEMBERSHIP CHECK ============
async def check_membership(user_id, context):
    try:
        channel_member = await context.bot.get_chat_member(
            chat_id=REQUIRED_CHANNEL, user_id=user_id
        )
        if channel_member.status in ['left', 'kicked']:
            return False, "channel"
        
        group_member = await context.bot.get_chat_member(
            chat_id=REQUIRED_GROUP, user_id=user_id
        )
        if group_member.status in ['left', 'kicked']:
            return False, "group"
        
        return True, None
    except Exception as e:
        logger.error(f"Membership check failed: {e}")
        return False, "error"

# ============ CREDIT & USER DATA SYSTEM ============
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f)

def ensure_user_exists(user_id, first_name=None, username=None):
    data = load_user_data()
    user_id_str = str(user_id)
    if user_id_str not in data:
        data[user_id_str] = {
            "credits": FREE_CREDITS_AMOUNT,
            "last_reset": time.time(),
            "referred_users": [],
            "banned": False,
            "bonus_credits": [],
            "first_name": first_name,
            "username": username,
            "joined": time.time(),
            "admin_credits_expiry": None,
            "last_search_time": 0
        }
        save_user_data(data)
    else:
        updated = False
        if first_name and data[user_id_str].get("first_name") != first_name:
            data[user_id_str]["first_name"] = first_name
            updated = True
        if username and data[user_id_str].get("username") != username:
            data[user_id_str]["username"] = username
            updated = True
        if updated:
            save_user_data(data)
    return data[user_id_str]

def get_user_data(user_id):
    data = load_user_data()
    user_id_str = str(user_id)
    if user_id_str not in data:
        data[user_id_str] = {
            "credits": FREE_CREDITS_AMOUNT,
            "last_reset": time.time(),
            "referred_users": [],
            "banned": False,
            "bonus_credits": [],
            "first_name": None,
            "username": None,
            "joined": time.time(),
            "admin_credits_expiry": None,
            "last_search_time": 0
        }
        save_user_data(data)
    else:
        if "last_search_time" not in data[user_id_str]:
            data[user_id_str]["last_search_time"] = 0
            save_user_data(data)
    return data[user_id_str]

def update_user_data(user_id, new_data):
    data = load_user_data()
    user_id_str = str(user_id)
    data[user_id_str] = new_data
    save_user_data(data)

def ensure_monthly_credits(user_id):
    user = get_user_data(user_id)
    now = time.time()
    admin_expiry = user.get("admin_credits_expiry")
    if admin_expiry and admin_expiry > now:
        return user
    else:
        last_reset = user.get("last_reset", 0)
        if now - last_reset >= FREE_CREDITS_PERIOD * 24 * 3600:
            user["credits"] = user.get("credits", 0) + FREE_CREDITS_AMOUNT
            user["last_reset"] = now
            if admin_expiry and admin_expiry <= now:
                user["admin_credits_expiry"] = None
            update_user_data(user_id, user)
    return user

def get_bonus_credits(user_id):
    user = get_user_data(user_id)
    bonus_list = user.get("bonus_credits", [])
    now = time.time()
    total = 0
    for item in bonus_list:
        if item.get("expiry", 0) > now:
            total += item.get("amount", 0)
    return total

def get_credits(user_id):
    user = ensure_monthly_credits(user_id)
    free = user.get("credits", 0)
    bonus = get_bonus_credits(user_id)
    admin_expiry = user.get("admin_credits_expiry")
    if admin_expiry and admin_expiry <= time.time():
        return bonus
    return free + bonus

def deduct_credit(user_id):
    if OWNER_ID and user_id == OWNER_ID:
        return True

    user = ensure_monthly_credits(user_id)
    total = get_credits(user_id)

    if total < 2:
        return False

    free = user.get("credits", 0)
    need = 2

    if free > 0:
        take = min(free, need)
        user["credits"] = free - take
        need -= take

    if need > 0:
        bonus_list = user.get("bonus_credits", [])
        now = time.time()
        for item in bonus_list:
            if need <= 0:
                break
            if item.get("expiry", 0) > now and item.get("amount", 0) > 0:
                take = min(item["amount"], need)
                item["amount"] -= take
                need -= take
        user["bonus_credits"] = [
            item for item in bonus_list
            if item.get("amount", 0) > 0 and item.get("expiry", 0) > now
        ]

    update_user_data(user_id, user)
    return True

def days_until_next_free(user_id):
    user = get_user_data(user_id)
    admin_expiry = user.get("admin_credits_expiry")
    if admin_expiry and admin_expiry > time.time():
        remaining = max(0, admin_expiry - time.time())
        return int(remaining // (24 * 3600)) + 1
    last_reset = user.get("last_reset", 0)
    next_reset = last_reset + FREE_CREDITS_PERIOD * 24 * 3600
    remaining = max(0, next_reset - time.time())
    return int(remaining // (24 * 3600)) + 1

def give_referral_credits(referrer_id, new_user_id):
    if referrer_id == new_user_id:
        return False
    referrer_data = get_user_data(referrer_id)
    referred_list = referrer_data.get("referred_users", [])
    if str(new_user_id) in referred_list:
        return False
    referred_list.append(str(new_user_id))
    referrer_data["referred_users"] = referred_list
    referrer_data["bonus_credits"] = referrer_data.get("bonus_credits", [])
    referrer_data["bonus_credits"].append({
        "amount": REFERRAL_REWARD,
        "expiry": time.time() + 365 * 24 * 3600
    })
    update_user_data(referrer_id, referrer_data)
    return True

# ============ ADMIN FUNCTIONS ============
def is_user_banned(user_id):
    user = get_user_data(user_id)
    return user.get("banned", False)

def ban_user(user_id):
    user = get_user_data(user_id)
    user["banned"] = True
    update_user_data(user_id, user)

def unban_user(user_id):
    user = get_user_data(user_id)
    user["banned"] = False
    update_user_data(user_id, user)

def add_bonus_credits(user_id, amount, expiry_timestamp):
    user = get_user_data(user_id)
    user["bonus_credits"] = user.get("bonus_credits", [])
    user["bonus_credits"].append({"amount": amount, "expiry": expiry_timestamp})
    update_user_data(user_id, user)

def set_credits_with_expiry(user_id, amount, expiry_timestamp):
    user = get_user_data(user_id)
    user["credits"] = amount
    user["bonus_credits"] = []
    user["admin_credits_expiry"] = expiry_timestamp
    user["last_reset"] = expiry_timestamp
    update_user_data(user_id, user)

def get_all_users():
    return load_user_data()

# ============ KEYBOARDS ============
def get_keyboard():
    buttons = [
        [KeyboardButton("🔍 Search Number")],
        [
            KeyboardButton("👥 Refer Friends"),
            KeyboardButton("📊 My Credits")
        ],
        [KeyboardButton("📞 Contact Admin")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)

def get_join_buttons():
    keyboard = [
        [
            InlineKeyboardButton("📢 Join Channel", url="https://t.me/team420bd"),
            InlineKeyboardButton("👥 Join Group", url="https://t.me/team_420_bd")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    buttons = [
        [KeyboardButton("👥 User List")],
        [KeyboardButton("🚫 Ban User")],
        [KeyboardButton("✅ Unban User")],
        [KeyboardButton("➕ Add Credits")],
        [KeyboardButton("🔧 Set Credits")],
        [KeyboardButton("🔍 Check Credits")],
        [KeyboardButton("📢 Broadcast")],
        [KeyboardButton("❌ Close Panel")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)

# ============ TELEGRAM BOT HANDLERS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username
    ensure_user_exists(user_id, first_name, username)

    referral_extra = None
    if context.args:
        arg = context.args[0]
        if arg.startswith("ref_"):
            referrer_id_str = arg.split("_")[1]
            try:
                referrer_id = int(referrer_id_str)
                if referrer_id != user_id:
                    success = give_referral_credits(referrer_id, user_id)
                    if success:
                        referral_extra = f"Referred by: `{referrer_id}`"
                        try:
                            await context.bot.send_message(
                                chat_id=referrer_id,
                                text=f"🎉 **You earned +{REFERRAL_REWARD} credits!**\n"
                                     f"A new user joined using your referral link.",
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            logger.error(f"Could not notify referrer: {e}")
            except ValueError:
                pass

    await notify_owner(context, update.effective_user, "Started Bot", extra=referral_extra)

    if is_user_banned(user_id):
        await update.message.reply_text(
            "🚫 **You are banned from using this bot.**\n"
            "Contact the administrator for assistance.",
            parse_mode='Markdown'
        )
        return

    is_member, missing = await check_membership(user_id, context)

    if not is_member:
        keyboard = [
            [
                InlineKeyboardButton("📢 Join Channel", url="https://t.me/team420bd"),
                InlineKeyboardButton("👥 Join Group", url="https://t.me/team_420_bd")
            ],
            [InlineKeyboardButton("✅ I've Joined", callback_data="verify_joined")]
        ]
        await update.message.reply_text(
            "❌ **Access Denied!**\n\n"
            "You must join both the channel and group to use this bot:\n"
            f"📢 Channel: {REQUIRED_CHANNEL}\n"
            f"👥 Group: {REQUIRED_GROUP}\n\n"
            "After joining, click the button below to verify.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    user = update.effective_user
    welcome_text = f"""
👋 **Welcome to Number Lookup Bot!**

Hi {user.first_name}! Search a number to get its information.

🎁 12 Free Credits / 30 Days
🔎 1 Search = 2 Credits

Your free credits renew automatically every 30 days.

📌 **Commands:**
/start — Restart the bot anytime
/help — Number format guide
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_keyboard())

async def verify_joined_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    await notify_owner(context, update.effective_user, "Verified Joined")

    if is_user_banned(user_id):
        await query.message.reply_text(
            "🚫 **You are banned from using this bot.**\n"
            "Contact the administrator for assistance.",
            parse_mode='Markdown'
        )
        return

    try:
        is_member, missing = await check_membership(user_id, context)
    except Exception as e:
        logger.error(f"Membership check error: {e}")
        await query.message.reply_text(
            "❌ **Verification failed.**\n\n"
            "I couldn't check your membership. Please make sure I'm a member of both:\n"
            f"📢 Channel: {REQUIRED_CHANNEL}\n"
            f"👥 Group: {REQUIRED_GROUP}\n\n"
            "If you're still having issues, contact the admin.",
            parse_mode='Markdown'
        )
        return

    if not is_member:
        keyboard = [
            [
                InlineKeyboardButton("📢 Join Channel", url="https://t.me/team420bd"),
                InlineKeyboardButton("👥 Join Group", url="https://t.me/team_420_bd")
            ],
            [InlineKeyboardButton("✅ I've Joined", callback_data="verify_joined")]
        ]
        if missing == "channel":
            msg = "❌ **You haven't joined the channel yet.**\n\n"
        elif missing == "group":
            msg = "❌ **You haven't joined the group yet.**\n\n"
        else:
            msg = "❌ **You haven't joined both yet.**\n\n"
        msg += f"📢 Channel: {REQUIRED_CHANNEL}\n"
        msg += f"👥 Group: {REQUIRED_GROUP}\n\n"
        msg += "After joining, click the button below to verify."
        await query.message.reply_text(
            msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    user = update.effective_user
    welcome_text = f"""
👋 **Welcome to Number Lookup Bot!**

Hi {user.first_name}! Search a number to get its information.

🎁 12 Free Credits / 30 Days
🔎 1 Search = 2 Credits

Your free credits renew automatically every 30 days.

📌 **Commands:**
/start — Restart the bot anytime
/help — Number format guide
"""
    await query.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify_owner(context, update.effective_user, "Help Command")

    user_id = update.effective_user.id
    is_member, missing = await check_membership(user_id, context)
    if not is_member:
        await update.message.reply_text(
            "❌ **Access Denied!**\n\n"
            "You must join both the channel and group to use this bot:\n"
            f"📢 Channel: {REQUIRED_CHANNEL}\n"
            f"👥 Group: {REQUIRED_GROUP}\n\n"
            "Please join and try again.",
            parse_mode='Markdown',
            reply_markup=get_join_buttons()
        )
        return

    if is_user_banned(user_id):
        await update.message.reply_text("🚫 **You are banned.**", parse_mode='Markdown')
        return

    help_text = """
❓ **How to use:**
Just send the phone number WITHOUT country code.

✅ **Correct:** `1712345678`
❌ **Wrong:** `+8801712345678`

**Status:** 🟢 Online
"""
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=get_keyboard())

async def refer_friends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_username = context.bot.username or "number2infolookup_bot"
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    await notify_owner(context, update.effective_user, "Refer Friends", extra=f"Link: {referral_link}")

    is_member, _ = await check_membership(user_id, context)
    if not is_member:
        await update.message.reply_text(
            "❌ **Access Denied!**\n\n"
            "You must join both the channel and group to use this bot:\n"
            f"📢 Channel: {REQUIRED_CHANNEL}\n"
            f"👥 Group: {REQUIRED_GROUP}\n\n"
            "Please join and try again.",
            parse_mode='Markdown',
            reply_markup=get_join_buttons()
        )
        return
    if is_user_banned(user_id):
        await update.message.reply_text("🚫 You are banned.", parse_mode='Markdown')
        return

    msg = f"""
👥 **Refer Friends**

Share your referral link with friends:

`{referral_link}`

When a friend joins using this link, you get **+{REFERRAL_REWARD} free credits**!

👤 Your current credits: **{get_credits(user_id)}**
"""
    keyboard = [[InlineKeyboardButton("📋 Tap and Hold to Copy Referral Link", url=referral_link)]]
    await update.message.reply_text(
        msg,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def my_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    credits = get_credits(user_id)
    days_left = days_until_next_free(user_id)
    await notify_owner(context, update.effective_user, "My Credits", extra=f"Credits: {credits}, Next free in {days_left} days")

    is_member, _ = await check_membership(user_id, context)
    if not is_member:
        await update.message.reply_text(
            "❌ **Access Denied!**\n\n"
            "You must join both the channel and group to use this bot:\n"
            f"📢 Channel: {REQUIRED_CHANNEL}\n"
            f"👥 Group: {REQUIRED_GROUP}\n\n"
            "Please join and try again.",
            parse_mode='Markdown',
            reply_markup=get_join_buttons()
        )
        return
    if is_user_banned(user_id):
        await update.message.reply_text("🚫 You are banned.", parse_mode='Markdown')
        return

    owner_note = " (Owner – unlimited)" if (OWNER_ID and user_id == OWNER_ID) else ""
    msg = f"""
📊 **Your Credits{owner_note}**

Remaining Credits: **{credits}**

📅 Next free credits: in **{days_left}** day(s)
(You get {FREE_CREDITS_AMOUNT} free credits every {FREE_CREDITS_PERIOD} days)
"""
    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=get_keyboard())

async def contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify_owner(context, update.effective_user, "Contact Admin")

    user_id = update.effective_user.id
    is_member, _ = await check_membership(user_id, context)
    if not is_member:
        await update.message.reply_text(
            "❌ **Access Denied!**\n\n"
            "You must join both the channel and group to use this bot:\n"
            f"📢 Channel: {REQUIRED_CHANNEL}\n"
            f"👥 Group: {REQUIRED_GROUP}\n\n"
            "Please join and try again.",
            parse_mode='Markdown',
            reply_markup=get_join_buttons()
        )
        return
    if is_user_banned(user_id):
        await update.message.reply_text("🚫 You are banned.", parse_mode='Markdown')
        return

    msg = "📞 **Contact Admin**\n\nIf you need help or have any issues, you can contact our admin via the bot below:\n\nClick the button to start a chat with the admin bot."
    keyboard = [[InlineKeyboardButton("👤 Contact Admin", url="https://t.me/team420_contact_admin_bot")]]
    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def search_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify_owner(context, update.effective_user, "Search Button Clicked")

    user_id = update.effective_user.id
    is_member, _ = await check_membership(user_id, context)
    if not is_member:
        await update.message.reply_text(
            "❌ **Access Denied!**\n\n"
            "You must join both the channel and group to use this bot:\n"
            f"📢 Channel: {REQUIRED_CHANNEL}\n"
            f"👥 Group: {REQUIRED_GROUP}\n\n"
            "Please join and try again.",
            parse_mode='Markdown',
            reply_markup=get_join_buttons()
        )
        return
    if is_user_banned(user_id):
        await update.message.reply_text("🚫 You are banned.", parse_mode='Markdown')
        return

    await update.message.reply_text(
        "📱 Please send the phone number **without** country code.\n\n"
        "Example: `1712345678`",
        parse_mode='Markdown',
        reply_markup=get_keyboard()
    )

# ============ handle_message ============
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id == OWNER_ID and context.user_data.get("admin_action"):
        await handle_admin_input(update, context)
        return

    is_member, missing = await check_membership(user_id, context)
    if not is_member:
        await update.message.reply_text(
            "❌ **Access Denied!**\n\n"
            "You must join both the channel and group to use this bot:\n"
            f"📢 Channel: {REQUIRED_CHANNEL}\n"
            f"👥 Group: {REQUIRED_GROUP}\n\n"
            "Please join and try again.",
            parse_mode='Markdown',
            reply_markup=get_join_buttons()
        )
        return

    if is_user_banned(user_id):
        await update.message.reply_text("🚫 You are banned.", parse_mode='Markdown')
        return

    user_input = update.message.text.strip()

    # ---- RATE LIMIT CHECK (1 hour) ----
    if not (OWNER_ID and user_id == OWNER_ID):
        user = get_user_data(user_id)
        last_search = user.get("last_search_time", 0)
        now = time.time()
        limit_seconds = 3600  # 1 hour
        if now - last_search < limit_seconds:
            remaining = limit_seconds - (now - last_search)
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            hours = limit_seconds // 3600
            time_unit = "hour" if hours == 1 else "hours"
            await update.message.reply_text(
                f"⏳ **Rate Limit Exceeded!**\n\n"
                f"You can only search **once every {hours} {time_unit}**.\n"
                f"Please wait **{minutes} minutes and {seconds} seconds** before trying again.",
                parse_mode='Markdown',
                reply_markup=get_keyboard()
            )
            return

    if not (OWNER_ID and user_id == OWNER_ID):
        credits = get_credits(user_id)
        if credits <= 0:
            await update.message.reply_text(
                "❌ **Insufficient Credits!**\n\n"
                "You have 0 credits. Please use **Refer Friends** to get more.\n"
                "You'll also receive free credits every 30 days.",
                parse_mode='Markdown',
                reply_markup=get_keyboard()
            )
            return

    if not re.match(r'^1[0-9]{9}$', user_input):
        await update.message.reply_text(
            "❌ **Invalid format!**\n\nSend: `1712345678`\nDon't include: +880 or 0",
            parse_mode='Markdown',
            reply_markup=get_keyboard()
        )
        return

    await notify_owner(context, update.effective_user, "Number Lookup Request", extra=f"Phone: +880{user_input}")

    if not deduct_credit(user_id):
        await update.message.reply_text(
            "❌ **Insufficient Credits!**\n\n"
            "You have 0 credits. Please use **Refer Friends** to get more.",
            parse_mode='Markdown',
            reply_markup=get_keyboard()
        )
        return

    # Update last search time (after deduction, so rate limit is applied)
    user_data = get_user_data(user_id)
    user_data["last_search_time"] = time.time()
    update_user_data(user_id, user_data)

    processing_msg = await update.message.reply_text("🔍 **Processing...**", parse_mode='Markdown')
    try:
        access_token = generate_access_token()
        if not access_token:
            await processing_msg.edit_text("❌ **Error:** Authentication failed.")
            return

        unitech_data = unitech_lookup(user_input, access_token)

        result_text = format_result(user_input, unitech_data)

        await processing_msg.delete()
        # === FIX: removed Markdown parsing to avoid underscore error ===
        await update.message.reply_text(result_text, parse_mode=None)

    except Exception as e:
        logger.error(f"Error: {e}")
        await processing_msg.edit_text("❌ **Error:** Something went wrong.")

# ============ ADMIN COMMAND ============
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("⛔ You are not authorized.")
        return
    context.user_data.pop("admin_action", None)
    await update.message.reply_text(
        "🛠 **Admin Panel**\nSelect an action:",
        reply_markup=get_admin_keyboard(),
        parse_mode='Markdown'
    )

# ============ ADMIN INPUT HANDLER ============
async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return
    action = context.user_data.get("admin_action")
    if not action:
        return
    text = update.message.text.strip()
    context.user_data.pop("admin_action", None)

    if action == "ban_user":
        try:
            target = int(text)
            if is_user_banned(target):
                await update.message.reply_text("ℹ️ User is already banned.")
            else:
                ban_user(target)
                await update.message.reply_text(f"✅ User `{target}` has been banned.", parse_mode='Markdown')
        except ValueError:
            await update.message.reply_text("❌ Invalid chat ID.")
        return

    if action == "unban_user":
        try:
            target = int(text)
            if not is_user_banned(target):
                await update.message.reply_text("ℹ️ User is not banned.")
            else:
                unban_user(target)
                await update.message.reply_text(f"✅ User `{target}` has been unbanned.", parse_mode='Markdown')
        except ValueError:
            await update.message.reply_text("❌ Invalid chat ID.")
        return

    if action == "check_credits":
        try:
            target = int(text)
            user_data = get_user_data(target)
            credits = get_credits(target)
            free = user_data.get("credits", 0)
            bonus = get_bonus_credits(target)
            banned = "Banned" if user_data.get("banned") else "Active"
            msg = f"📊 **Credits for user `{target}`**\n"
            msg += f"Free credits: {free}\n"
            msg += f"Bonus credits: {bonus}\n"
            msg += f"Total: {credits}\n"
            msg += f"Status: {banned}\n"
            bonus_list = user_data.get("bonus_credits", [])
            if bonus_list:
                msg += "\n**Bonus entries:**\n"
                for i, item in enumerate(bonus_list, 1):
                    expiry = datetime.fromtimestamp(item["expiry"]).strftime("%d-%m-%Y")
                    msg += f"{i}. {item['amount']} credits (expires {expiry})\n"
            admin_expiry = user_data.get("admin_credits_expiry")
            if admin_expiry and admin_expiry > time.time():
                exp = datetime.fromtimestamp(admin_expiry).strftime("%d-%m-%Y")
                msg += f"\n📌 Admin-set credits expire on {exp}"
            await update.message.reply_text(msg, parse_mode='Markdown')
        except ValueError:
            await update.message.reply_text("❌ Invalid chat ID.")
        return

    if action == "add_credits":
        parts = text.split()
        if len(parts) != 3:
            await update.message.reply_text("❌ Format: `user_id amount dd-mm-yyyy`")
            return
        try:
            target = int(parts[0])
            amount = int(parts[1])
            expiry_date = datetime.strptime(parts[2], "%d-%m-%Y")
            expiry_timestamp = expiry_date.timestamp()
            add_bonus_credits(target, amount, expiry_timestamp)
            await update.message.reply_text(
                f"✅ Added {amount} credits to user `{target}` until {expiry_date.strftime('%d-%m-%Y')}.",
                parse_mode='Markdown'
            )
        except ValueError as e:
            await update.message.reply_text(f"❌ Invalid input: {e}")
        return

    if action == "set_credits":
        parts = text.split()
        if len(parts) != 3:
            await update.message.reply_text("❌ Format: `user_id amount dd-mm-yyyy`")
            return
        try:
            target = int(parts[0])
            amount = int(parts[1])
            expiry_date = datetime.strptime(parts[2], "%d-%m-%Y")
            expiry_timestamp = expiry_date.timestamp()
            set_credits_with_expiry(target, amount, expiry_timestamp)
            await update.message.reply_text(
                f"✅ Set credits for user `{target}` to {amount} until {expiry_date.strftime('%d-%m-%Y')}.\n"
                "All previous credits (free & bonus) have been replaced.",
                parse_mode='Markdown'
            )
        except ValueError as e:
            await update.message.reply_text(f"❌ Invalid input: {e}")
        return

    if action == "broadcast":
        msg_text = text
        users = get_all_users()
        sent_count = 0
        failed_count = 0
        for uid_str, data in users.items():
            uid = int(uid_str)
            if uid == OWNER_ID:
                continue
            if data.get("banned", False):
                continue
            try:
                await context.bot.send_message(chat_id=uid, text=msg_text, parse_mode='Markdown')
                sent_count += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.error(f"Failed to send broadcast to {uid}: {e}")
                failed_count += 1
        await update.message.reply_text(
            f"✅ **Broadcast sent!**\n\n"
            f"Delivered to: {sent_count} users\n"
            f"Failed: {failed_count}\n"
            f"Total users (excluding banned and owner): {sent_count + failed_count}"
        )
        return

    await update.message.reply_text("Unknown action. Use /admin again.")

# ============ ADMIN BUTTON HANDLER ============
async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("⛔ Unauthorized.")
        return

    text = update.message.text
    if text == "❌ Close Panel":
        context.user_data.pop("admin_action", None)
        await update.message.reply_text("🔒 Admin panel closed.", reply_markup=get_keyboard())
        return

    action_map = {
        "👥 User List": "user_list",
        "🚫 Ban User": "ban_user",
        "✅ Unban User": "unban_user",
        "➕ Add Credits": "add_credits",
        "🔧 Set Credits": "set_credits",
        "🔍 Check Credits": "check_credits",
        "📢 Broadcast": "broadcast"
    }
    if text in action_map:
        action = action_map[text]
        if action == "user_list":
            users = get_all_users()
            if not users:
                await update.message.reply_text("📭 No users found.")
                return
            msg = "👥 **User List**\n\n"
            for uid, data in users.items():
                name = data.get("first_name", "N/A")
                username = data.get("username", "N/A")
                credits = get_credits(int(uid))
                banned = "🚫" if data.get("banned") else "✅"
                joined = datetime.fromtimestamp(data.get("joined", 0)).strftime("%d-%m-%Y")
                msg += f"**ID:** `{uid}`\n"
                msg += f"**Name:** {name}\n"
                msg += f"**Username:** @{username}\n"
                msg += f"**Credits:** {credits}\n"
                msg += f"**Status:** {banned}\n"
                msg += f"**Joined:** {joined}\n\n"
            if len(msg) > 4000:
                parts = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
                for part in parts:
                    await update.message.reply_text(part, parse_mode='Markdown')
                    await asyncio.sleep(0.1)
            else:
                await update.message.reply_text(msg, parse_mode='Markdown')
            return

        prompts = {
            "ban_user": "🚫 Send the **chat ID** of the user to ban:",
            "unban_user": "✅ Send the **chat ID** of the user to unban:",
            "check_credits": "🔍 Send the **chat ID** of the user to check credits:",
            "add_credits": "➕ Send in format:\n`user_id amount dd-mm-yyyy`\ne.g. `123456789 10 29-08-2026`",
            "set_credits": "🔧 Send in format:\n`user_id amount dd-mm-yyyy`\ne.g. `123456789 50 29-08-2026`",
            "broadcast": "📢 Send your broadcast message:"
        }
        if action in prompts:
            context.user_data["admin_action"] = action
            await update.message.reply_text(prompts[action], parse_mode='Markdown')
        else:
            await update.message.reply_text("Unknown action.")
    else:
        pass

# ============ MAIN ============
def main():
    print("🤖 Bot starting...")
    print(f"📌 Bot Token: {'✅ Set' if BOT_TOKEN else '❌ Not Set'}")
    if OWNER_ID:
        print(f"👤 Owner ID: {OWNER_ID} (exempt from credit deduction & rate limit)")
    else:
        print("ℹ️ No owner set – all users consume credits.")

    if not BOT_TOKEN:
        print("❌ Please set BOT_TOKEN environment variable!")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_command))

    application.add_handler(CallbackQueryHandler(verify_joined_callback, pattern="^verify_joined$"))

    application.add_handler(MessageHandler(
        filters.Regex('^(👥 User List|🚫 Ban User|✅ Unban User|➕ Add Credits|🔧 Set Credits|🔍 Check Credits|📢 Broadcast|❌ Close Panel)$'),
        handle_admin_buttons
    ))

    application.add_handler(MessageHandler(filters.Regex('^🔍 Search Number$'), search_button_handler))
    application.add_handler(MessageHandler(filters.Regex('^👥 Refer Friends$'), refer_friends))
    application.add_handler(MessageHandler(filters.Regex('^📊 My Credits$'), my_credits))
    application.add_handler(MessageHandler(filters.Regex('^📞 Contact Admin$'), contact_admin))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
