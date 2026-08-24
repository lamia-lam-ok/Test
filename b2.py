import warnings
warnings.filterwarnings("ignore", category=Warning)

import logging
import os
import re
import urllib.parse
import tempfile
from datetime import datetime
import pytz
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ============ CONFIGURATION ============
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN environment variable not set!")
    exit(1)

OWNER_ID = os.environ.get("OWNER_ID")
if OWNER_ID:
    OWNER_ID = int(OWNER_ID)
else:
    print("⚠️ OWNER_ID not set. Bot will not forward user details.")

REQUIRED_CHANNEL = "@InfinitelyInteresting"
REQUIRED_GROUP = "@team_420_bd"

BD_TIMEZONE = pytz.timezone('Asia/Dhaka')

# ============ LOGGING ============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============ FACEBOOK SCRAPER ============
def extract_facebook_images(profile_url):
    """
    Returns a tuple: (cover_photo_url, profile_picture_url)
    Uses the exact logic from the provided standalone script.
    """
    # Format URL
    if 'profile.php?id=' in profile_url:
        parsed = urllib.parse.urlparse(profile_url)
        query_params = urllib.parse.parse_qs(parsed.query)
        if 'id' in query_params:
            profile_id = query_params['id'][0]
            base_url = f"https://www.facebook.com/{profile_id}"
        else:
            base_url = profile_url.rstrip('/')
    else:
        base_url = profile_url.rstrip('/')

    url = f"{base_url}/?hr=1&wtsid=rdr_0StRnXFIDwHXVBBRB"

    cookies = {
        "datr": "pQi0aWq7H5A3-agoSlN81uyN",
        "locale": "en_GB",
        "sb": "l-22aZ0eJPr0zLAvZH1AfBBS",
        "m_pixel_ratio": "2.8125",
        "wd": "384x832",
        "vpd": "v1%3B719x384x2.8125",
        "ps_l": "1",
        "ps_n": "1",
        "fr": "00Jgx7F9kdRNNyeZd..BptC4p..AAA.0.0.BptxL5.AWc6gReBk0taVG9HkpuWk31Nb38",
    }

    headers = {
        "Host": "www.facebook.com",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "dpr": "2.8125",
        "viewport-width": "980",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-ch-ua-platform-version": '"10.0.0"',
        "sec-ch-ua-model": '"R7-PRIMO"',
        "sec-ch-ua-full-version-list": '"Google Chrome";v="131.0.6778.260", "Chromium";v="131.0.6778.260", "Not_A Brand";v="24.0.0.0"',
        "sec-ch-prefers-color-scheme": "dark",
    }

    try:
        res = requests.get(url, headers=headers, cookies=cookies, timeout=30)
        if res.status_code != 200:
            logger.error(f"Facebook page request failed: {res.status_code}")
            return None, None

        html_content = res.text

        # Find all fbcdn.net images
        img_pattern = r'https?://[^"\'\s]+\.fbcdn\.net[^"\'\s]+\.(?:jpg|jpeg|png|webp)[^"\'\s]*'
        all_images = re.findall(img_pattern, html_content, re.IGNORECASE)

        unique_images = []
        seen = set()
        for img in all_images:
            clean_url = img.replace('&amp;', '&')
            base = clean_url.split('?')[0]
            if base not in seen:
                seen.add(base)
                unique_images.append(clean_url)

        if not unique_images:
            return None, None

        cover_photo = None
        profile_picture = None

        for img_url in unique_images:
            if 'p1080x375' in img_url or 'p851x315' in img_url:
                cover_photo = img_url
            elif 'p270x270' in img_url or 'p200x200' in img_url or 'p100x100' in img_url:
                if not profile_picture:
                    profile_picture = img_url

        # Fallback: take first image as cover if none found, second as profile
        if not cover_photo and len(unique_images) >= 1:
            cover_photo = unique_images[0]
        if not profile_picture and len(unique_images) >= 2:
            profile_picture = unique_images[1]

        return cover_photo, profile_picture

    except Exception as e:
        logger.error(f"Facebook scraper error: {e}")
        return None, None

# ========================================================
# This function downloads an image and sends it as a photo.
# The temporary file is deleted immediately after sending.
# ========================================================
async def download_and_send_photo(context, chat_id, img_url, caption):
    if not img_url:
        return False
    temp_file = None
    try:
        img_headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            "Referer": "https://www.facebook.com/",
        }
        response = requests.get(img_url, headers=img_headers, timeout=30)
        if response.status_code != 200:
            return False

        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(response.content)
            temp_file = tmp.name

        # Send the photo
        with open(temp_file, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                parse_mode='Markdown'
            )

        # Delete the temporary file immediately after sending
        os.remove(temp_file)
        return True
    except Exception as e:
        logger.error(f"Image download/send error: {e}")
        # Clean up if something went wrong
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
        return False

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

# ============ OWNER NOTIFICATION ============
async def notify_owner(context, user, url):
    if not OWNER_ID:
        return
    name = user.full_name or "N/A"
    username = f"@{user.username}" if user.username else "N/A"
    user_id = user.id
    now_bd = datetime.now(BD_TIMEZONE)
    timestamp = now_bd.strftime("%Y-%m-%d %I:%M:%S %p")
    msg = f"📩 **New Facebook URL Submitted**\n\n"
    msg += f"**Full Name:** {name}\n"
    msg += f"**Username:** {username}\n"
    msg += f"**User ID:** `{user_id}`\n"
    msg += f"**URL:** {url}\n"
    msg += f"**Timestamp (BD):** {timestamp}"
    try:
        await context.bot.send_message(chat_id=OWNER_ID, text=msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Failed to notify owner: {e}")

# ============ KEYBOARDS ============
def get_join_buttons():
    keyboard = [
        [
            InlineKeyboardButton("📢 Join Channel", url="https://t.me/InfinitelyInteresting"),
            InlineKeyboardButton("👥 Join Group", url="https://t.me/team_420_bd")
        ],
        [InlineKeyboardButton("✅ I've Joined", callback_data="verify_joined")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============ HANDLERS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    is_member, _ = await check_membership(user_id, context)
    if is_member:
        await update.message.reply_text(
            f"👋 Welcome, {user.first_name}!\n\n"
            "Send me a Facebook profile URL and I will download the cover photo and profile picture for you.\n\n"
            "Example:\n"
            "`https://www.facebook.com/username`\n"
            "or `https://www.facebook.com/profile.php?id=123456789`",
            parse_mode='Markdown'
        )
    else:
        keyboard = get_join_buttons()
        await update.message.reply_text(
            "❌ **Access Denied!**\n\n"
            "You must join both the channel and group to use this bot:\n"
            f"📢 Channel: {REQUIRED_CHANNEL}\n"
            f"👥 Group: {REQUIRED_GROUP}\n\n"
            "After joining, click the button below to verify.",
            parse_mode='Markdown',
            reply_markup=keyboard
        )

async def verify_joined_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user = update.effective_user

    is_member, missing = await check_membership(user_id, context)
    if is_member:
        await query.message.reply_text(
            f"✅ Verification successful!\n\n"
            f"Welcome, {user.first_name}!\n"
            "Now send any Facebook profile URL and I'll fetch the images for you.",
            parse_mode='Markdown'
        )
    else:
        keyboard = get_join_buttons()
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
            reply_markup=keyboard
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **How to use:**\n"
        "Send me a Facebook profile URL.\n"
        "I'll fetch the cover photo and profile picture and send them to you.\n\n"
        "Examples:\n"
        "`https://www.facebook.com/johndoe`\n"
        "`https://www.facebook.com/profile.php?id=123456789`\n\n"
        "Make sure you are a member of our channel and group.",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()

    # Check membership
    is_member, _ = await check_membership(user_id, context)
    if not is_member:
        await update.message.reply_text(
            "❌ **Access Denied!**\n\n"
            "You must join both the channel and group to use this bot.\n"
            f"📢 Channel: {REQUIRED_CHANNEL}\n"
            f"👥 Group: {REQUIRED_GROUP}\n\n"
            "Please join and then use /start to verify.",
            parse_mode='Markdown',
            reply_markup=get_join_buttons()
        )
        return

    # Check if it's a Facebook URL
    if not re.search(r'(facebook\.com|fb\.com)', text, re.IGNORECASE):
        await update.message.reply_text(
            "❌ **I only accept Facebook profile URLs.**\n"
            "Please send a valid link like:\n"
            "`https://www.facebook.com/username`",
            parse_mode='Markdown'
        )
        return

    # Notify owner
    await notify_owner(context, user, text)

    # Process and send images
    processing_msg = await update.message.reply_text("📸 **Fetching Facebook images...**", parse_mode='Markdown')
    try:
        cover, profile = extract_facebook_images(text)

        if not cover and not profile:
            await processing_msg.edit_text(
                "❌ **No images found.**\n"
                "Make sure the profile is public or the URL is correct.",
                parse_mode='Markdown'
            )
            return

        await processing_msg.delete()

        # Send cover (if found)
        if cover:
            await download_and_send_photo(context, update.effective_chat.id, cover, "🖼️ **Cover Photo**")
        else:
            await update.message.reply_text("⚠️ Cover photo not found.", parse_mode='Markdown')

        # Send profile (if found)
        if profile:
            await download_and_send_photo(context, update.effective_chat.id, profile, "👤 **Profile Picture**")
        else:
            await update.message.reply_text("⚠️ Profile picture not found.", parse_mode='Markdown')

        # Success summary
        summary = f"✅ **Download Complete!**\n\n"
        summary += f"🔗 URL: {text}\n"
        summary += f"🖼️ Cover: {'✅' if cover else '❌'}\n"
        summary += f"👤 Profile: {'✅' if profile else '❌'}"
        await update.message.reply_text(summary, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error processing: {e}")
        await processing_msg.edit_text("❌ **Error:** Something went wrong. Please try again later.")

# ============ MAIN ============
def main():
    print("🤖 Bot starting... (Facebook Image Downloader + Membership Verification)")
    if OWNER_ID:
        print(f"👤 Owner ID: {OWNER_ID}")
    else:
        print("⚠️ No owner set – user details won't be forwarded.")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(verify_joined_callback, pattern="^verify_joined$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
