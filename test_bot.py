from telegram.ext import ApplicationBuilder, CommandHandler

async def start(update, context):
    await update.message.reply_text("Hello, bot is alive!")

app = ApplicationBuilder().token('8004250406:AAEsd9sb7pZDy7wh0axdi4pdQWSu7wSkmDA').build()
app.add_handler(CommandHandler("start", start))

print("✅ Bot is running")
app.run_polling()
