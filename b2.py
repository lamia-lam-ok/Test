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
import string

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
REQUIRED_CHANNEL = "@team420bd"
REQUIRED_GROUP = "@team_420_bd"

USER_DATA_FILE = "user_data.json"
FREE_CREDITS_PERIOD = 30
FREE_CREDITS_AMOUNT = 8
REFERRAL_REWARD = 1
PRANK_COST = 2
PRANK_RATE_LIMIT = 3600  # 1 hour

# ============ JOKESPHONE CALLER ============
VOICE_OPTIONS = [
    {"dial": "8810", "titulo": "আপনি আমার গার্লফ্রেন্ডকে কল করেন কেন?"},
    {"dial": "8805", "titulo": "গাজার মতো দুর্গন্ধ!"},
    {"dial": "8808", "titulo": "আপনি আমার ওয়াই-ফাই চুরি করছেন!"},
    {"dial": "8809", "titulo": "আপনি কেন আমাকে কল করেন?"},
    {"dial": "8803", "titulo": "পিজ্জা ডেলিভারি"},
    {"dial": "8804", "titulo": "আপনার ট্যাক্সি আপনার জন্য অপেক্ষা করছে"},
    {"dial": "8806", "titulo": "আপনার কামরার হৈচৈ আওয়াজ"},
    {"dial": "8807", "titulo": "আপনার কুকুরটি খুবই ক্লান্তিকর!"}
]

BRANDS = {
    "samsung": {
        "models": ["SM-M366B", "SM-G998B", "SM-A526B", "SM-N986B", "SM-S918B", "SM-S911B", "SM-A546B", "SM-A336B", "SM-F946B", "SM-X906B", "SM-G781B", "SM-A715F"],
        "builds": ["AP3A", "RP1A", "QP1A", "TP1A", "UP1A"]
    },
    "xiaomi": {
        "models": ["M2011K2G", "M2102J20SG", "M2007J3SG", "2201116PG", "2107119SG", "2109119DG", "M2101K7AG", "M2006J10C", "M2102J2SG"],
        "builds": ["RKQ1", "QKQ1", "PKQ1", "SKQ1", "TKQ1"]
    },
    "oneplus": {
        "models": ["LE2113", "LE2123", "IN2013", "LE2115", "LE2125", "IN2023", "NE2213", "NE2215", "DN2103"],
        "builds": ["QKQ1", "RQ1A", "SP1A", "TP1A"]
    },
    "google": {
        "models": ["Pixel 6", "Pixel 7", "Pixel 8", "Pixel 4", "Pixel 5", "Pixel 6a", "Pixel 7a", "Pixel 8a", "Pixel 9"],
        "builds": ["TQ3A", "UP1A", "SP1A", "RP1A", "SQ3A"]
    },
    "huawei": {
        "models": ["ANA-LX1", "VOG-L29", "ELE-L29", "LIO-L29", "MAR-LX1A", "JNY-LX1", "CLT-L29", "LYA-L29", "MHA-L29"],
        "builds": ["HUAWEI", "EMUI", "HarmonyOS"]
    },
    "oppo": {
        "models": ["CPH2205", "CPH2305", "CPH2359", "CPH2451", "CPH2477", "CPH2491", "CPH2505", "CPH2537"],
        "builds": ["QKQ1", "RKQ1", "SKQ1", "TP1A"]
    },
    "vivo": {
        "models": ["V2045", "V2108", "V2115", "V2124", "V2134", "V2144", "V2157", "V2162", "V2171"],
        "builds": ["QKQ1", "RP1A", "SP1A", "TP1A"]
    },
    "motorola": {
        "models": ["XT2215-2", "XT2241-1", "XT2251-1", "XT2261-1", "XT2271-1", "XT2315-1", "XT2321-1", "XT2331-1"],
        "builds": ["S3ST32", "S3SS32", "S3ZS32", "T1TS32"]
    },
    "realme": {
        "models": ["RMX3370", "RMX3393", "RMX3478", "RMX3491", "RMX3501", "RMX3576", "RMX3615", "RMX3622"],
        "builds": ["QKQ1", "RKQ1", "SKQ1", "TP1A"]
    },
    "sony": {
        "models": ["XQ-AT51", "XQ-BC52", "XQ-BT52", "XQ-CT52", "XQ-DQ72", "XQ-DS72"],
        "builds": ["55.2.A", "58.0.A", "59.0.A", "62.0.A"]
    },
    "nokia": {
        "models": ["TA-1334", "TA-1346", "TA-1387", "TA-1395", "TA-1403", "TA-1417"],
        "builds": ["00WW", "0WW", "1WW", "2WW"]
    },
    "lg": {
        "models": ["LM-G900", "LM-V600", "LM-Q730", "LM-K520", "LM-X420", "LM-G850"],
        "builds": ["QKQ1", "PKQ1", "RKQ1", "SP1A"]
    },
    "asus": {
        "models": ["ZS671KS", "ZS672KS", "ZS673KS", "ZS630KL", "ZS620KL", "ZS660KL"],
        "builds": ["QKQ1", "RP1A", "SP1A", "TP1A"]
    }
}

ANDROID_VERSIONS = ["10", "11", "12", "13", "14", "15"]

def generate_random_id(length=16):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def get_current_timestamp():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

def send_prank_call(dst_number, voice):
    """
    Execute the JokesPhone prank call.
    Returns True if successful (res=="OK"), False otherwise.
    """
    dial = voice["dial"]
    titulo = voice["titulo"]

    base_id = generate_random_id()
    brand = random.choice(list(BRANDS.keys()))
    version = random.choice(ANDROID_VERSIONS)
    model = random.choice(BRANDS[brand]["models"])
    build_base = random.choice(BRANDS[brand]["builds"])
    build_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    build = f"{build_base}.{build_suffix}"
    user_agent = f"Dalvik/2.1.0 (Linux; U; Android {version}; {model} Build/{build})"
    did = f"{base_id}@jokesphone"

    common_headers = {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": user_agent,
        "Host": "master.appha.es",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }

    # Register
    register_payload = {
        "uv": "jokesphone",
        "dtype": "adr",
        "did": did,
        "route": "jo_1",
        "timezone": "Asia/Dhaka",
        "tags": {
            "mf": brand,
            "mcc": 470,
            "mnc": 4,
            "r": version,
            "v": "4.0.030826.346",
            "l": "en_US",
            "c": "US",
            "lnf": "en",
            "platform": "gplay",
            "aid": base_id,
            "class": "Jokesphone_o"
        },
        "root": True,
        "imeiex": False,
        "version": "4.0.030826.346",
        "version_num": 346,
        "recommender": ""
    }
    try:
        requests.post(
            "https://master.appha.es/lua/jokesphone/user/create.lua",
            headers=common_headers,
            json=register_payload,
            timeout=10
        )
    except Exception:
        return False

    # Check credit
    credit_payload = {"did": did}
    try:
        credit_resp = requests.post(
            "https://master.appha.es/lua/jokesphone/user/getCredit.lua",
            headers=common_headers,
            json=credit_payload,
            timeout=10
        )
        credit_data = credit_resp.json()
        credit = credit_data.get("credit", 0)
    except Exception:
        return False

    # Create task
    current_time = get_current_timestamp()
    task_id = generate_random_id(20)
    task_payload = {
        "real_f": current_time,
        "f": current_time,
        "uid": did,
        "dst": dst_number,
        "dial": dial,
        "titulo": titulo,
        "credit": credit,
        "smscredit": 0,
        "tz": "Asia/Dhaka",
        "c": "bd",
        "sc": "bd",
        "rec": True,
        "landline": False,
        "odid": did,
        "_id": task_id
    }
    try:
        task_resp = requests.post(
            "https://master.appha.es/lua/jokesphone/user/create_task.lua",
            headers=common_headers,
            json=task_payload,
            timeout=10
        )
        result = task_resp.json()
        return result.get("res") == "OK"
    except Exception:
        return False

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
            "last_prank_time": 0,
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
        if "last_prank_time" not in data[user_id_str]:
            data[user_id_str]["last_prank_time"] = 0
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
            "last_prank_time": 0,
        }
        save_user_data(data)
    else:
        if "last_prank_time" not in data[user_id_str]:
            data[user_id_str]["last_prank_time"] = 0
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
    if OWNER_ID and user_id == OWNER_ID:
        return float('inf')
    user = ensure_monthly_credits(user_id)
    free = user.get("credits", 0)
    bonus = get_bonus_credits(user_id)
    admin_expiry = user.get("admin_credits_expiry")
    if admin_expiry and admin_expiry <= time.time():
        return bonus
    return free + bonus

def deduct_credit(user_id, amount=2):
    if OWNER_ID and user_id == OWNER_ID:
        return True

    user = ensure_monthly_credits(user_id)
    total = get_credits(user_id)

    if total < amount:
        return False

    free = user.get("credits", 0)
    need = amount

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
        [KeyboardButton("📞 Send Prank Call")],
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
                                text=f"🎉 **You earned +{REFERRAL_REWARD} credit!**\n"
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
👋 **Welcome to Prank Call Bot!**

Hi {user.first_name}! Send a prank call to any number.

🎁 8 Free Credits / 30 Days
📞 1 Prank Call = 2 Credits

Your free credits renew automatically every 30 days.
**Rate limit:** 1 call per hour.

📌 **Commands:**
/start — Restart the bot
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
👋 **Welcome to Prank Call Bot!**

Hi {user.first_name}! Send a prank call to any number.

🎁 8 Free Credits / 30 Days
📞 1 Prank Call = 2 Credits

Your free credits renew automatically every 30 days.
**Rate limit:** 1 call per hour.

📌 **Commands:**
/start — Restart the bot
"""
    await query.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_keyboard()
    )

async def refer_friends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_username = context.bot.username or "prankcall_bot"
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

When a friend joins using this link, you get **+{REFERRAL_REWARD} free credit**!

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

💡 **Usage cost:**
📞 1 Prank call = 2 credits
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

    msg = "📞 **Contact Admin**\n\nIf you need help, contact our admin via the bot below."
    keyboard = [[InlineKeyboardButton("👤 Contact Admin", url="https://t.me/team420_contact_admin_bot")]]
    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# ============ PRANK CALL HANDLERS ============
async def prank_call_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await notify_owner(context, update.effective_user, "Prank Call Button Clicked")

    if is_user_banned(user_id):
        await update.message.reply_text("🚫 You are banned.", parse_mode='Markdown')
        return

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

    msg = "🎤 **Choose a voice message:**\n\n"
    for i, opt in enumerate(VOICE_OPTIONS, 1):
        msg += f"{i}. {opt['titulo']}\n"
    msg += "\nPlease reply with the **number** (1-8) of your choice."

    context.user_data["state"] = "awaiting_voice"
    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=get_keyboard())

async def handle_prank_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if not text.isdigit() or not (1 <= int(text) <= len(VOICE_OPTIONS)):
        await update.message.reply_text(
            "❌ Invalid choice. Please send a number between 1 and 8.",
            parse_mode='Markdown'
        )
        return

    voice_index = int(text) - 1
    selected = VOICE_OPTIONS[voice_index]
    context.user_data["prank_voice"] = selected
    context.user_data["state"] = "awaiting_prank_number"

    await update.message.reply_text(
        f"📱 Selected: *{selected['titulo']}*\n\n"
        "Now send the **destination phone number** with country code:\n"
        "Example: `+8801712345678`",
        parse_mode='Markdown',
        reply_markup=get_keyboard()
    )

async def handle_prank_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    dst_raw = update.message.text.strip()

    # Validate format: must start with +880 and have 10 digits after that
    # Also accept any number that starts with +880 and has at least 13 characters (basic check)
    if not re.match(r'^\+8801[0-9]{9}$', dst_raw):
        await update.message.reply_text(
            "❌ **Invalid format!**\n"
            "Send the number with country code: `+8801712345678`\n"
            "Must start with +880 and have 10 digits after that.",
            parse_mode='Markdown',
            reply_markup=get_keyboard()
        )
        return

    dst_full = dst_raw  # use as is

    # ---- RATE LIMIT CHECK ----
    if not (OWNER_ID and user_id == OWNER_ID):
        user_data = get_user_data(user_id)
        last_prank = user_data.get("last_prank_time", 0)
        now = time.time()
        if now - last_prank < PRANK_RATE_LIMIT:
            remaining = PRANK_RATE_LIMIT - (now - last_prank)
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            await update.message.reply_text(
                f"⏳ **Rate Limit Exceeded!**\n\n"
                f"You can only send **1 prank call per hour**.\n"
                f"Please wait **{minutes} minutes and {seconds} seconds** before trying again.",
                parse_mode='Markdown',
                reply_markup=get_keyboard()
            )
            context.user_data.pop("state", None)
            context.user_data.pop("prank_voice", None)
            return

    # Check credits
    if get_credits(user_id) < PRANK_COST:
        await update.message.reply_text(
            f"❌ **Insufficient Credits!**\n\n"
            f"You need {PRANK_COST} credits for a prank call.\n"
            f"Your current credits: {get_credits(user_id)}",
            parse_mode='Markdown',
            reply_markup=get_keyboard()
        )
        context.user_data.pop("state", None)
        context.user_data.pop("prank_voice", None)
        return

    # Deduct credits
    if not deduct_credit(user_id, PRANK_COST):
        await update.message.reply_text(
            "❌ **Failed to deduct credits.** Please try again.",
            parse_mode='Markdown',
            reply_markup=get_keyboard()
        )
        context.user_data.pop("state", None)
        context.user_data.pop("prank_voice", None)
        return

    selected = context.user_data.get("prank_voice")
    if not selected:
        await update.message.reply_text("❌ Voice selection lost. Please start over.", reply_markup=get_keyboard())
        context.user_data.pop("state", None)
        context.user_data.pop("prank_voice", None)
        return

    await notify_owner(context, update.effective_user, "Prank Call Request",
                       extra=f"Number: {dst_full}, Voice: {selected['titulo']}")

    processing_msg = await update.message.reply_text("📞 **Sending prank call...**", parse_mode='Markdown')

    success = send_prank_call(dst_full, selected)

    context.user_data.pop("state", None)
    context.user_data.pop("prank_voice", None)

    if success:
        user_data = get_user_data(user_id)
        user_data["last_prank_time"] = time.time()
        update_user_data(user_id, user_data)
        await processing_msg.edit_text("✅ **Call send successfully!**", parse_mode='Markdown')
    else:
        await processing_msg.edit_text("❌ **Something went wrong!**", parse_mode='Markdown')

# ============ ADMIN COMMAND & INPUT ============
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

# ============ handle_message ============
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id == OWNER_ID and context.user_data.get("admin_action"):
        await handle_admin_input(update, context)
        return

    state = context.user_data.get("state")
    if state == "awaiting_voice":
        await handle_prank_voice(update, context)
        return
    elif state == "awaiting_prank_number":
        await handle_prank_number(update, context)
        return

    await update.message.reply_text(
        "Please use the buttons below to interact.",
        reply_markup=get_keyboard()
    )

# ============ MAIN ============
def main():
    print("🤖 Prank Call Bot starting...")
    print(f"📌 Bot Token: {'✅ Set' if BOT_TOKEN else '❌ Not Set'}")
    if OWNER_ID:
        print(f"👤 Owner ID: {OWNER_ID} (exempt from credit deduction & rate limit)")
    else:
        print("ℹ️ No owner set – all users consume credits and rate limits.")

    if not BOT_TOKEN:
        print("❌ Please set BOT_TOKEN environment variable!")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_command))

    application.add_handler(CallbackQueryHandler(verify_joined_callback, pattern="^verify_joined$"))

    application.add_handler(MessageHandler(
        filters.Regex('^(👥 User List|🚫 Ban User|✅ Unban User|➕ Add Credits|🔧 Set Credits|🔍 Check Credits|📢 Broadcast|❌ Close Panel)$'),
        handle_admin_buttons
    ))

    application.add_handler(MessageHandler(filters.Regex('^📞 Send Prank Call$'), prank_call_button))
    application.add_handler(MessageHandler(filters.Regex('^👥 Refer Friends$'), refer_friends))
    application.add_handler(MessageHandler(filters.Regex('^📊 My Credits$'), my_credits))
    application.add_handler(MessageHandler(filters.Regex('^📞 Contact Admin$'), contact_admin))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
