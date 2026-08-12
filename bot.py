import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# এনভায়রনমেন্ট থেকে টোকেন নেওয়া হবে
BOT_TOKEN = os.getenv("BOT_TOKEN")

user_urls = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("স্বাগতম! 👋\n\nযেকোনো ভিডিওর লিঙ্ক পাঠান। আমি কোয়ালিটি বেছে নেওয়ার অপশন দেব।")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_id = update.message.from_user.id
    
    if "http://" not in url and "https://" not in url:
        await update.message.reply_text("অনুগ্রহ করে একটি সঠিক লিঙ্ক পাঠান।")
        return

    user_urls[user_id] = url

    keyboard = [
        [InlineKeyboardButton("144p", callback_data="144"), InlineKeyboardButton("360p", callback_data="360")],
        [InlineKeyboardButton("720p (HD)", callback_data="720"), InlineKeyboardButton("1080p (FHD)", callback_data="1080")],
        [InlineKeyboardButton("Best Quality", callback_data="best")]
    ]
    await update.message.reply_text("ভিডিওর কোয়ালিটি সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    quality = query.data
    url = user_urls.get(user_id)

    if not url:
        await query.edit_message_text("কোনো লিঙ্ক পাওয়া যায়নি। আবার পাঠান।")
        return

    await query.edit_message_text(f"⏳ {quality}p ডাউনলোড প্রসেস করা হচ্ছে...")

    if quality == "best":
        format_spec = "bestvideo/best"
    else:
        format_spec = f"bestvideo[height<={quality}]/best[height<={quality}]"

    filename = f"video_{user_id}.mp4"

    ydl_opts = {
        'format': format_spec,
        'outtmpl': filename,
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        await query.edit_message_text("📤 ভিডিও টেলিগ্রামে আপলোড হচ্ছে...")

        with open(filename, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=user_id,
                video=video_file,
                caption=f"✅ ডাউনলোড সম্পন্ন ({quality}p)"
            )

        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        await query.edit_message_text(f"❌ এরর হয়েছে: {str(e)}")
        if os.path.exists(filename):
            os.remove(filename)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))

    print("বট চালু হয়েছে...")
    app.run_polling()

if __name__ == '__main__':
    main()
