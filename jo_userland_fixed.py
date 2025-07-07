import sqlite3
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from datetime import datetime
import re
import logging
import telegram.error

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = "7162917997:AAHjCPWDpdhdGgOUz9Dy137Rv2IzldbG98s"  # Replace with your valid bot token
ADMIN_ID = 7451622773  # Replace with your admin's Telegram user ID
REGISTRATION_CHANNEL = "-1002237023678"  # Replace with registration channel ID
RESULTS_CHANNEL = "-1002158129417"  # Replace with results channel ID
API_URL = "https://nine9ac.onrender.com/gate/?url="

# Initialize SQLite database
def init_db():
    try:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                join_date TEXT,
                credits INTEGER
            )"""
        )
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
    finally:
        conn.close()

# Get user data from database
def get_user(user_id):
    try:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()
        return user
    except sqlite3.Error as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return None
    finally:
        conn.close()

# Register new user
def register_user(user_id, username, join_date):
    try:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO users (user_id, username, join_date, credits) VALUES (?, ?, ?, ?)",
            (user_id, username, join_date, 10),
        )
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Error registering user {user_id}: {e}")
    finally:
        conn.close()

# Update user credits
def update_credits(user_id, amount, add=False):
    try:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        if add:
            c.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (amount, user_id))
        else:
            c.execute("UPDATE users SET credits = ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Error updating credits for user {user_id}: {e}")
    finally:
        conn.close()

# Get all users (for admin)
def get_all_users():
    try:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        users = c.fetchall()
        return users
    except sqlite3.Error as e:
        logger.error(f"Error fetching all users: {e}")
        return []
    finally:
        conn.close()

# Format API result
def format_result(json_data, user_name, username, credits):
    try:
        domain = re.match(r"https?://[^/]+", json_data["URL"]).group(0)
        result = (
            f"🟢 <b>URL</b>: {domain}\n"
            f"💳 <b>Gateway</b>: {json_data['Gateway'] if json_data['Gateway'] != 'None' else 'Retard site 🤢'}\n"
            f"☁️ <b>Cloudflare</b>: {json_data['Cloudflare'] + ' 🔥' if json_data['Cloudflare'] == 'Not Found' else json_data['Cloudflare']}\n"
            f"🔒 <b>Captcha</b>: {json_data['Captcha'] + ' 🔥' if json_data['Captcha'] == 'Not Found' else json_data['Captcha']}\n"
            f"🏬 <b>Platform</b>: {json_data['Platform'] if json_data['Platform'] != 'None' else 'Custom Platform 🗺️'}\n"
            f"🔐 <b>3D Secure</b>: {json_data['3D Secure'] + ' 🔥' if json_data['3D Secure'] == 'Not Found' else json_data['3D Secure']}\n"
            f"🆔 <b>Checked by</b>: <a href='tg://user?id={username}'>{user_name}</a>\n"
            f"💰 <b>Credits left</b>: {credits}"
        )
        return result
    except (KeyError, re.error) as e:
        logger.error(f"Error formatting result: {e}")
        return "Error: Unable to process the API response."

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "No username"
    join_date = datetime.now().strftime("%d/%m/%Y")

    # Check if user is registered
    db_user = get_user(user_id)
    if not db_user:
        keyboard = [[InlineKeyboardButton("Register", callback_data="register")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = (
            "<b>ׂ╰┈➤ Welcome to the Pro Gateway Hunter 3.0</b>\n"
            "✎ Register first to use bot features 🔗"
        )
        try:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML")
        except telegram.error.BadRequest as e:
            logger.error(f"Error sending start message: {e}")
            await update.message.reply_text("Error: Unable to process your request. Please try again.")
    else:
        await show_main_menu(update, context)

# Main menu after registration
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Hunt", callback_data="hunt"),
            InlineKeyboardButton("Credit", callback_data="credit"),
        ],
        [
            InlineKeyboardButton("Info", callback_data="info"),
            InlineKeyboardButton("Owner", callback_data="owner"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = (
        "<b>ׂ╰┈➤ Welcome to the Pro Gateway Hunter 3.0</b>\n"
        ": ̗̀➛ You are already Registered my boy 🎻\n"
        "✎ Use Hunt button to check Website\n"
        "✎ Use Credit button to check Credits\n"
        "✎ Use Info button to check bot Info\n"
        "✎ Use Owner button to contact Owner"
    )
    try:
        if update.callback_query:
            # Check if message content is different to avoid "Message is not modified" error
            current_text = update.callback_query.message.text
            if current_text != message:
                await update.callback_query.message.edit_text(message, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML")
    except telegram.error.BadRequest as e:
        if "Message is not modified" in str(e):
            pass  # Ignore if the message is unchanged
        else:
            logger.error(f"Error showing main menu: {e}")
            await (update.callback_query.message.edit_text("Error: Unable to update menu. Please try again.") if update.callback_query else update.message.reply_text("Error: Unable to show menu. Please try again."))

# Callback query handler for buttons
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest as e:
        logger.error(f"Error answering callback query: {e}")
        return

    user = query.from_user
    user_id = user.id
    db_user = get_user(user_id)

    if not db_user and query.data != "register":
        await query.message.reply_text("Please register first using /start.")
        return

    try:
        if query.data == "register":
            username = f"@{user.username}" if user.username else "No username"
            join_date = datetime.now().strftime("%d/%m/%Y")
            register_user(user_id, username, join_date)
            await context.bot.send_message(
                chat_id=REGISTRATION_CHANNEL,
                text=f"New User Registered:\nUser ID: {user_id}\nUsername: {username}\nJoin Date: {join_date}\nCredits: 10",
            )
            await show_main_menu(update, context)

        elif query.data == "hunt":
            context.user_data["state"] = "hunt"
            keyboard = [[InlineKeyboardButton("Back", callback_data="back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message = (
                "<b>ׂ╰┈➤ Welcome to the Pro Gateway Hunter 3.0</b>\n"
                ": ̗̀➛ Let's start Hunting 💥\n"
                "✎ Use /hunt &lt;url&gt; to check Website\n"
                "╰┈➤ ex: /hunt https://example.com"
            )
            current_text = query.message.text
            if current_text != message:
                await query.message.edit_text(message, reply_markup=reply_markup, parse_mode="HTML")

        elif query.data == "credit":
            credits = "∞" if user_id == ADMIN_ID else db_user[3]
            keyboard = [[InlineKeyboardButton("Back", callback_data="back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message = (
                "<b>ׂ╰┈➤ Welcome to the Pro Gateway Hunter 3.0</b>\n"
                f": ̗̀➛ Hello <a href='tg://user?id={user_id}'>{user.first_name}</a> 🛸\n"
                f"✎ Credits - 💰 {credits}\n"
                f"╰┈➤ Joined - {db_user[2]}"
            )
            current_text = query.message.text
            if current_text != message:
                await query.message.edit_text(message, reply_markup=reply_markup, parse_mode="HTML")

        elif query.data == "info":
            keyboard = [[InlineKeyboardButton("Back", callback_data="back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message = (
                "<b>ׂ╰┈➤ Welcome to the Pro Gateway Hunter 3.0</b>\n"
                ": ̗̀➛ Pro Hunter Capabilities 🎀\n"
                ": ̗̀➛ Our tool Find almost all Gateways\n"
                ": ̗̀➛ Accurately finds Captcha & Cloudflare\n"
                ": ̗̀➛ We use Premium proxies to bypass\n"
                ": ̗̀➛ Hosted on Paid service."
            )
            current_text = query.message.text
            if current_text != message:
                await query.message.edit_text(message, reply_markup=reply_markup, parse_mode="HTML")

        elif query.data == "owner":
            await context.bot.send_message(
                chat_id=user_id,
                text="Contact the owner: @Gen666z",
                parse_mode="HTML",
                disable_web_page_preview=True,
            )

        elif query.data == "back":
            context.user_data["state"] = None
            await show_main_menu(update, context)

    except telegram.error.BadRequest as e:
        if "Message is not modified" in str(e):
            pass
        else:
            logger.error(f"Error in button callback: {e}")
            await query.message.reply_text("Error: Unable to process your request. Please try again.")

# Hunt command handler
async def hunt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    db_user = get_user(user_id)

    if not db_user:
        await update.message.reply_text("Please register first using /start.")
        return

    if context.user_data.get("state") != "hunt":
        return

    args = context.args
    if not args or len(args) != 1:
        keyboard = [[InlineKeyboardButton("Back", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = (
            "<b>ׂ╰┈➤ Welcome to the Pro Gateway Hunter 3.0</b>\n"
            ": ̗̀➛ Are you retard? 🦢\n"
            "✎ Use /hunt &lt;url&gt; to check Website\n"
            "╰┈➤ ex: /hunt https://example.com"
        )
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML")
        return

    url = args[0]
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        processing_msg = await update.message.reply_text("🔭 Processing... 🔭")

        response = requests.get(API_URL + url, timeout=10)
        response.raise_for_status()
        json_data = response.json()

        if user_id != ADMIN_ID:
            if db_user[3] <= 0:
                await processing_msg.edit_text("Error: Insufficient credits.")
                return
            update_credits(user_id, db_user[3] - 1)

        result = format_result(json_data, user.first_name, user_id, "∞" if user_id == ADMIN_ID else db_user[3] - 1)
        await processing_msg.edit_text(result, parse_mode="HTML")

        await context.bot.send_message(chat_id=RESULTS_CHANNEL, text=result, parse_mode="HTML")

        keyboard = [[InlineKeyboardButton("Back", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = (
            "<b>ׂ╰┈➤ Welcome to the Pro Gateway Hunter 3.0</b>\n"
            ": ̗̀➛ Let's start Hunting 💥\n"
            "✎ Use /hunt &lt;url&gt; to check Website\n"
            "╰┈➤ ex: /hunt https://example.com"
        )
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML")

    except requests.RequestException as e:
        logger.error(f"API request error for URL {url}: {e}")
        await processing_msg.edit_text("Error: Unable to fetch website data. Please check the URL and try again.")
    except telegram.error.BadRequest as e:
        logger.error(f"Telegram API error: {e}")
        await processing_msg.edit_text("Error: Unable to process your request. Please try again.")
    except Exception as e:
        logger.error(f"Unexpected error in hunt: {e}")
        await processing_msg.edit_text("Error: An unexpected issue occurred. Please try again later.")

# Admin commands
async def prohunt_add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Error: Unauthorized access.")
        return

    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /prohuntaddcredit <user_id> <credits>")
        return

    try:
        user_id = int(args[0])
        credits = int(args[1])
        db_user = get_user(user_id)
        if not db_user:
            await update.message.reply_text("User not found.")
            return
        update_credits(user_id, credits, add=True)
        await update.message.reply_text(f"Added {credits} credits to user {user_id}.")
    except ValueError:
        await update.message.reply_text("Invalid user ID or credits amount.")
    except Exception as e:
        logger.error(f"Error in prohunt_add_credit: {e}")
        await update.message.reply_text("Error: Unable to add credits. Please try again.")

async def prohunt_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Error: Unauthorized access.")
        return

    users = get_all_users()
    if not users:
        await update.message.reply_text("No registered users.")
        return

    message = ""
    for i, user in enumerate(users, 1):
        message += (
            f"User - {i}\n"
            f"Username - {user[1]}\n"
            f"ChatID - {user[0]}\n"
            f"Date Joined - {user[2]}\n"
            f"Credits available - {'∞' if user[0] == ADMIN_ID else user[3]}\n\n"
        )
    try:
        await update.message.reply_text(message)
    except telegram.error.BadRequest as e:
        logger.error(f"Error sending user list: {e}")
        await update.message.reply_text("Error: Unable to display user list. Please try again.")

# Handle unknown commands or messages
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Back", callback_data="back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = (
        "<b>ׂ╰┈➤ Welcome to the Pro Gateway Hunter 3.0</b>\n"
        ": ̗̀➛ Are you retard? 🦢\n"
        "✎ Use /hunt &lt;url&gt; to check Website\n"
        "╰┈➤ ex: /hunt https://example.com"
    )
    try:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML")
    except telegram.error.BadRequest as e:
        logger.error(f"Error handling unknown command: {e}")
        await update.message.reply_text("Error: Invalid command. Please use /start to begin.")

# Validate bot token
def validate_token(token):
    try:
        import re
        if not re.match(r"^\d+:[\w-]+$", token):
            return False
        return True
    except Exception:
        return False

# Main function to run the bot
def main():
    init_db()
    
    if not validate_token(BOT_TOKEN) or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Invalid or missing bot token.")
        print("Error: Please provide a valid Telegram bot token.")
        return

    try:
        application = Application.builder().token(BOT_TOKEN).build()
    except telegram.error.InvalidToken as e:
        logger.error(f"Invalid bot token: {e}")
        print("Error: The provided bot token is invalid. Please check and try again.")
        return

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("hunt", hunt))
    application.add_handler(CommandHandler("prohuntaddcredit", prohunt_add_credit))
    application.add_handler(CommandHandler("prohuntusers", prohunt_users))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    try:
        application.run_polling()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        print("Error: Failed to start the bot. Please check logs for details.")

if __name__ == "__main__":
    main()
