import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# --- دکمه‌های شیشه‌ای منو ---
async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("💰 قیمت خدمات", callback_data='prices')],
        [InlineKeyboardButton("🛒 خرید کانفیگ جدید", callback_data='buy_new')],
        [InlineKeyboardButton("🔄 تمدید کانفیگ قبلی", callback_data='renew')],
        [InlineKeyboardButton("📦 مشاهده حجم باقی مانده", callback_data='check_usage')],
        [InlineKeyboardButton("💳 کیف پول", callback_data='wallet')],
        [InlineKeyboardButton("🎧 تماس با پشتیبانی", callback_data='support')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "سلام! به بات BlueVPN خوش آمدید 👋\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )

# --- پاسخ به کلیک روی دکمه‌ها ---
async def button_handler(update: Update, context):
    query = update.callback_query
    await query.answer() # برای اینکه دکمه لودینگ نمونه

    if query.data == 'prices':
        await query.edit_message_text("💰 **قیمت خدمات:**\n\n۱ ماهه ۱۰ گیگ: ۵۰ هزار تومان\n۲ ماهه ۲۰ گیگ: ۹۰ هزار تومان\n\n(اینجا متن خودت رو بذار)", parse_mode='Markdown')
    
    elif query.data == 'buy_new':
        await query.edit_message_text("🛒 **خرید کانفیگ جدید:**\n\nبرای خرید لطفاً با پشتیبانی در ارتباط باشید یا به درگاه پرداخت متصل شوید.")
    
    elif query.data == 'renew':
        await query.edit_message_text("🔄 **تمدید کانفیگ:**\n\nلطفاً نام کاربری یا لینک کانفیگ خود را ارسال کنید.")
    
    elif query.data == 'check_usage':
        await query.edit_message_text("📦 **حجم باقی مانده:**\n\nبرای مشاهده حجم، لطفاً نام کاربری خود را ارسال کنید.")
    
    elif query.data == 'wallet':
        await query.edit_message_text("💳 **کیف پول:**\n\nموجودی فعلی شما: ۰ تومان\nبرای شارژ کیف پول با پشتیبانی تماس بگیرید.")
    
    elif query.data == 'support':
        await query.edit_message_text("🎧 **پشتیبانی:**\n\nبرای ارتباط با پشتیبانی به آیدی @YourSupportID پیام دهید.")

# --- هندل کردن پیام‌های متنی ---
async def text_handler(update: Update, context):
    text = update.message.text
    # اینجا می‌تونی منطق بات رو بر اساس متنی که کاربر می‌فرسته بنویسی
    await update.message.reply_text(f"شما نوشتید: {text}\n\nبرای دیدن منو دستور /start را بزنید.")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    print("بات روشن شد...")
    app.run_polling()

if __name__ == '__main__':
    main()
