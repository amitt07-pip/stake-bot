import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Resolve asset paths relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIRST_IMAGE = os.path.join(BASE_DIR, "assets", "welcome_first.jpg")
SECOND_IMAGE = os.path.join(BASE_DIR, "assets", "welcome.jpg")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start - send two images then welcome text with buttons."""
    chat_id = update.effective_chat.id

    # 1. Send first image alone (no caption)
    with open(FIRST_IMAGE, "rb") as f:
        await context.bot.send_photo(chat_id=chat_id, photo=f)

    # 2. Build inline keyboard
    keyboard = [
        [InlineKeyboardButton("Register Now (for new users)", url="https://stake.com")],
        [InlineKeyboardButton("Access Bonuses", callback_data="access_bonuses")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 3. Send second image with bold welcome text and buttons
    with open(SECOND_IMAGE, "rb") as f:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=f,
            caption="<b>Welcome to Official Stake Bonus Time Bot, please continue with the below options to claim your following bonuses \U0001f389</b>",
            parse_mode="HTML",
            reply_markup=reply_markup,
        )


async def access_bonuses_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Access Bonuses' button press."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("\u2705 Yes", callback_data="has_account_yes")],
        [InlineKeyboardButton("\u274c No", callback_data="has_account_no")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        "Do you already have a Stake account? \U0001f389",
        reply_markup=reply_markup,
    )


async def has_account_yes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Yes' button - delete the message and ask for username."""
    query = update.callback_query
    await query.answer()

    # Delete the original message (removes buttons too)
    await query.message.delete()

    # Send a new message asking for the username
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please send us your Stake account username displayed in the dashboard to check your eligibility!",
    )

    # Mark that we are waiting for a username from this user
    context.user_data["awaiting_username"] = True


async def has_account_no_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'No' button - delete the message and send account creation link."""
    query = update.callback_query
    await query.answer()

    # Delete the original message (removes buttons too)
    await query.message.delete()

    # Send message with account creation link and Resume button
    keyboard = [
        [InlineKeyboardButton("\u2705 Resume the process", callback_data="resume_process")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "Create your account using the link below, then click the button to continue the process! \U0001f60e\n\n"
            '\U0001f449 <a href="https://stake.com">Use this link to create an account</a> \U0001f448\n\n'
            "\u26a0\ufe0f If the site doesn't work, simply use a VPN (Canada, Norway)."
        ),
        parse_mode="HTML",
        reply_markup=reply_markup,
    )


async def resume_process_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Resume the process' button - same as Yes flow."""
    query = update.callback_query
    await query.answer()

    # Delete the original message (removes buttons too)
    await query.message.delete()

    # Send the same username prompt as the Yes flow
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please send us your Stake account username displayed in the dashboard to check your eligibility!",
    )

    # Mark that we are waiting for a username from this user
    context.user_data["awaiting_username"] = True


async def username_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages - capture username when expected."""
    if not context.user_data.get("awaiting_username"):
        return

    username = update.message.text.strip()
    context.user_data["awaiting_username"] = False
    context.user_data["stake_username"] = username

    # Placeholder: respond to the username (to be customised later)
    await update.message.reply_text(
        f"Thank you! We received your username: <b>{username}</b>.\nPlease wait while we check your eligibility.",
        parse_mode="HTML",
    )


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))

    # Callback query handlers
    app.add_handler(CallbackQueryHandler(access_bonuses_callback, pattern="^access_bonuses$"))
    app.add_handler(CallbackQueryHandler(has_account_yes_callback, pattern="^has_account_yes$"))
    app.add_handler(CallbackQueryHandler(has_account_no_callback, pattern="^has_account_no$"))
    app.add_handler(CallbackQueryHandler(resume_process_callback, pattern="^resume_process$"))

    # Text message handler (for username input)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, username_handler))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
