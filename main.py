from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Function to handle /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("hello")

def main():
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()

    # Add command handler
    app.add_handler(CommandHandler("start", start))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
