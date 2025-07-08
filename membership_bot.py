from dotenv import load_dotenv
load_dotenv()

import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatInviteLink,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
)
from telegram.ext import filters
from datetime import datetime, timedelta
import json

# === CONFIGURATION ===
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DEMO_LINK = os.getenv("DEMO_LINK")
UPI_ID = os.getenv("UPI_ID")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
QR_IMAGES = {
    '499': os.getenv("QR_499"),
    '1499': os.getenv("QR_1499")
}
settings_file = "settings.json"

# === In-Memory Storage ===
pending_payments = {}
qr_image_urls = QR_IMAGES.copy()

# === Load Admin Config ===
def load_settings():
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            return json.load(f)
    return qr_image_urls

def save_settings():
    with open(settings_file, 'w') as f:
        json.dump(qr_image_urls, f)

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📥 /start triggered by {update.message.from_user.username}")
    keyboard = [
        [InlineKeyboardButton("₹499 Plan", callback_data="buy_499")],
        [InlineKeyboardButton("₹1499 Plan", callback_data="buy_1499")],
        [InlineKeyboardButton("Support", callback_data="support")]
    ]
    await update.message.reply_photo(
        photo=qr_image_urls['1499'],
        caption=f"🎓 Welcome to PAID SEEK Membership!\n\n🧾 Lifetime Access Plans Available\n\n💡 DEMO Channel: {DEMO_LINK}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# === Buy Plan Handler ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    print(f"👉 Button clicked by {user_id}: {query.data}")

    if query.data.startswith("buy_"):
        amount = query.data.split("_")[1]
        image_url = qr_image_urls.get(amount)

        await query.message.reply_photo(
            photo=image_url,
            caption=f"💳 Please pay ₹{amount} to UPI ID: `{UPI_ID}`\n\n📤 Then send the payment screenshot here.",
            parse_mode="Markdown"
        )

    elif query.data == "support":
        await query.message.reply_text("🛠 Support is here. Type your message.")

    elif query.data.startswith("accept_"):
        target_user_id = int(query.data.split("_")[1])
        invite_link: ChatInviteLink = await context.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            expire_date=datetime.utcnow() + timedelta(minutes=5),
            member_limit=1
        )
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"✅ Payment confirmed!\nHere is your 1-time link:\n{invite_link.invite_link}\n\n⏳ Expires in 5 min. Use once only.\n❤️ Thank you, take care of your brother!"
        )
        await query.message.reply_text("✅ Access granted.")

    elif query.data.startswith("reject_"):
        target_user_id = int(query.data.split("_")[1])
        await context.bot.send_message(
            chat_id=target_user_id,
            text="❌ Your payment was not approved. Please try again."
        )
        await query.message.reply_text("❌ Rejected.")

# === Screenshot Upload ===
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    file_id = update.message.photo[-1].file_id
    pending_payments[user.id] = file_id
    print(f"📸 Screenshot received from {user.username or user.first_name} ({user.id})")

    keyboard = [[
        InlineKeyboardButton("✅ Accept", callback_data=f"accept_{user.id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
    ]]

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=file_id,
        caption=f"📸 Payment from @{user.username or user.first_name}\nUser ID: {user.id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await update.message.reply_text("📥 Screenshot received. Waiting for admin approval.")

# === Admin Panel ===
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.from_user.id) != str(ADMIN_ID):
        await update.message.reply_text("❌ Unauthorized")
        return

    args = context.args
    if not args or args[0] != ADMIN_PASSWORD:
        await update.message.reply_text("🔐 Invalid password.")
        return

    await update.message.reply_text(
        "🛠 Admin Panel\n\nUse command:\n/updateqr <499|1499> <image_url>"
    )

async def update_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.from_user.id) != str(ADMIN_ID):
        return
    try:
        plan = context.args[0]
        url = context.args[1]
        qr_image_urls[plan] = url
        save_settings()
        await update.message.reply_text(f"✅ QR for ₹{plan} updated.")
    except:
        await update.message.reply_text("⚠️ Failed. Use /updateqr <499|1499> <url>")

# === Main ===
def main():
    print("🔄 Loading QR config...")
    global qr_image_urls
    qr_image_urls = load_settings()

    app = ApplicationBuilder().token(TOKEN).build()
    print("✅ Bot initialized")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("updateqr", update_qr))

    print("🚀 Bot running... Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ Bot crashed: {e}")
