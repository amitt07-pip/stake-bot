import asyncio
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

# Deposit address mapping: {currency: {network: address}}
DEPOSIT_ADDRESSES = {
    "USDT": {
        "BEP20": "0x8c640881238BEC28509bB3a8F37Dbf3398668a4F",
        "ERC20": "0x8c640881238BEC28509bB3a8F37Dbf3398668a4F",
        "TRC20": "TEsiVdTukJYz8KbhyhrLQ1WQ1G6LHq7Ctc",
        "POLYGON": "0x8c640881238BEC28509bB3a8F37Dbf3398668a4F",
    },
    "USDC": {
        "BEP20": "0x8c640881238BEC28509bB3a8F37Dbf3398668a4F",
        "ERC20": "0x8c640881238BEC28509bB3a8F37Dbf3398668a4F",
        "POLYGON": "0x8c640881238BEC28509bB3a8F37Dbf3398668a4F",
    },
    "ETH": {
        "BEP20": "0x8c640881238BEC28509bB3a8F37Dbf3398668a4F",
        "ERC20": "0x8c640881238BEC28509bB3a8F37Dbf3398668a4F",
    },
}

# Network display names for deposit message
NETWORK_DISPLAY = {
    "BEP20": "BEP20/BSC",
    "ERC20": "ERC20",
    "TRC20": "TRC20",
    "POLYGON": "POLYGON",
}

# QR code images mapped by address
QR_DIR = os.path.join(BASE_DIR, "assets", "qr")
ADDRESS_QR = {
    "0x8c640881238BEC28509bB3a8F37Dbf3398668a4F": os.path.join(QR_DIR, "evm.png"),
    "TEsiVdTukJYz8KbhyhrLQ1WQ1G6LHq7Ctc": os.path.join(QR_DIR, "trc20.png"),
}


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

    # Send eligibility check message
    msg = await update.message.reply_text(
        f"We have received your Stake account username : <b>{username}</b>, please wait while we check your eligibility for bonus \U0001f504",
        parse_mode="HTML",
    )

    # Wait 20 seconds then edit to congratulations with bonus options
    await asyncio.sleep(20)

    keyboard = [
        [InlineKeyboardButton("\U0001f381 $30 Free", callback_data="bonus_30_free")],
        [InlineKeyboardButton("\U0001f3b0 200% Bonus", callback_data="bonus_200_pct")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await msg.edit_text(
        "\U0001f389 Congratulations, your Stake account is eligible for the Stake BONUSTiME Bonuses. <b>Choose one of the three options below! \U0001f60e</b>",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )


async def bonus_30_free_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle '$30 Free' button - send deposit question with Yes/No."""
    query = update.callback_query
    await query.answer()

    context.user_data["selected_offer"] = "30_free"
    context.user_data["min_deposit"] = 20

    keyboard = [
        [InlineKeyboardButton("\u2705 Yes", callback_data="deposit_yes")],
        [InlineKeyboardButton("\u274c No", callback_data="deposit_no")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        "Do you want to make a deposit of minimum $20? (If yes, you will receive $30 in any currency of your choice with no strings attached, which guarantees you earn money even if you lose your deposit ! \U0001f60e)",
        reply_markup=reply_markup,
    )


async def bonus_200_pct_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle '200% Bonus' button - send deposit question with Yes/No."""
    query = update.callback_query
    await query.answer()

    context.user_data["selected_offer"] = "200_pct"
    context.user_data["min_deposit"] = 50

    keyboard = [
        [InlineKeyboardButton("\u2705 Yes", callback_data="deposit_yes")],
        [InlineKeyboardButton("\u274c No", callback_data="deposit_no")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        "On your first deposit from our bot you will receive a guaranteed 200% bonus if you make a minimum deposit of $50 in any currency of your choice ( can be withdrawn instantly ). Do you want to proceed ?",
        reply_markup=reply_markup,
    )


async def deposit_yes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Yes' on deposit question - edit message to confirm offer selected, then ask currency."""
    query = update.callback_query
    await query.answer()

    offer = context.user_data.get("selected_offer", "30_free")
    if offer == "200_pct":
        offer_text = "Offer Selected : 200% Deposit Bonus."
    else:
        offer_text = "Offer Selected : $30 Free Deposit Bonus."

    await query.edit_message_text(
        f"<b>{offer_text}</b>",
        parse_mode="HTML",
    )

    # Send currency selection message
    keyboard = [
        [
            InlineKeyboardButton("USDT", callback_data="currency_USDT"),
            InlineKeyboardButton("USDC", callback_data="currency_USDC"),
            InlineKeyboardButton("ETH", callback_data="currency_ETH"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please choose the Currency you want to deposit!",
        reply_markup=reply_markup,
    )


async def deposit_no_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'No' on deposit question - edit to rejection message."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "<b>\u274c User has rejected the offer</b>",
        parse_mode="HTML",
    )


async def currency_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle currency selection - show network options."""
    query = update.callback_query
    await query.answer()

    currency = query.data.replace("currency_", "")
    context.user_data["selected_currency"] = currency

    # Build network buttons based on available networks for this currency
    networks = list(DEPOSIT_ADDRESSES.get(currency, {}).keys())
    keyboard = [
        [InlineKeyboardButton(net, callback_data=f"network_{net}") for net in networks],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"<b>Currency Selected : {currency}\nPlease choose the network for the following currency</b>",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )


async def network_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle network selection - show deposit address."""
    query = update.callback_query
    await query.answer()

    network = query.data.replace("network_", "")
    currency = context.user_data.get("selected_currency", "USDT")
    context.user_data["selected_network"] = network

    # Edit message to show currency + network selected
    await query.edit_message_text(
        f"<b>Currency Selected : {currency}\nNetwork Selected : {network}</b>",
        parse_mode="HTML",
    )

    # Get the deposit address
    address = DEPOSIT_ADDRESSES.get(currency, {}).get(network, "")
    network_display = NETWORK_DISPLAY.get(network, network)

    # Send QR code for the deposit address
    qr_path = ADDRESS_QR.get(address)
    if qr_path:
        with open(qr_path, "rb") as qr_file:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=qr_file,
            )

    # Send deposit address message with "I have deposited" button
    keyboard = [
        [InlineKeyboardButton("\u2705 I have deposited", callback_data="i_have_deposited")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            f"<i>Please Deposit minimum ${context.user_data.get('min_deposit', 20)} to the following Stake deposit address to proceed.</i>\n\n"
            f"Address : <code>{address}</code>\n"
            f"Network : <b>{network_display}</b>"
        ),
        parse_mode="HTML",
        reply_markup=reply_markup,
    )


async def i_have_deposited_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'I have deposited' button - send confirmation message."""
    query = update.callback_query
    await query.answer()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "Please wait while the system check your deposit, you will be informed by the "
            "registered mail in your account once the deposit is confirmed! \U0001f60e\n\n"
            "Sincerely,\nStake Team"
        ),
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
    app.add_handler(CallbackQueryHandler(bonus_30_free_callback, pattern="^bonus_30_free$"))
    app.add_handler(CallbackQueryHandler(bonus_200_pct_callback, pattern="^bonus_200_pct$"))
    app.add_handler(CallbackQueryHandler(deposit_yes_callback, pattern="^deposit_yes$"))
    app.add_handler(CallbackQueryHandler(deposit_no_callback, pattern="^deposit_no$"))
    app.add_handler(CallbackQueryHandler(currency_callback, pattern="^currency_"))
    app.add_handler(CallbackQueryHandler(network_callback, pattern="^network_"))
    app.add_handler(CallbackQueryHandler(i_have_deposited_callback, pattern="^i_have_deposited$"))

    # Text message handler (for username input)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, username_handler))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
