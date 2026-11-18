import os
import json
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# --- تنظیمات دیتابیس (فایل JSON) ---
DB_FILE = 'database.json'
TEST_PRICE = 0.1  # حجم تست به گیگ
PRICE_PER_GB = 5000 # قیمت هر گیگ

# لود کردن دیتابیس
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# ذخیره دیتابیس
def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# گرفتن اطلاعات کاربر (اگه نبود می‌سازه)
def get_user(user_id):
    db = load_db()
    user_id = str(user_id)
    if user_id not in db:
        db[user_id] = {
            'wallet': 0,          # موجودی کیف پول
            'configs': {},        # دیکشنری کانفیگ‌ها: { "username": {"gb": 10.5} }
            'test_count': 0       # تعداد تست‌های گرفته شده
        }
        save_db(db)
    return db[user_id]

# آپدیت اطلاعات کاربر
def update_user(user_id, data):
    db = load_db()
    db[str(user_id)] = data
    save_db(db)

# تولید اسم تصادفی برای کانفیگ
def generate_random_name():
    letters = string.ascii_lowercase
    digits = string.digits
    return ''.join(random.choices(letters + digits, k=8))

# --- منوی اصلی ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 قیمت خدمات", callback_data='prices')],
        [InlineKeyboardButton("🛒 خرید کانفیگ جدید", callback_data='buy_new')],
        [InlineKeyboardButton("🔄 تمدید کانفیگ قبلی", callback_data='renew')],
        [InlineKeyboardButton("📦 مشاهده حجم باقی مانده", callback_data='check_usage')],
        [InlineKeyboardButton("🎁 دریافت کانفیگ تست", callback_data='test_config')],
        [InlineKeyboardButton("💳 کیف پول", callback_data='wallet')],
        [InlineKeyboardButton("🎧 تماس با پشتیبانی", callback_data='support')],
    ]
    return InlineKeyboardMarkup(keyboard)

# دکمه بازگشت
def back_menu():
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_user(update.effective_user.id)
    await update.message.reply_text(
        "سلام! به بات BlueVPN خوش آمدید 👋\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=main_menu()
    )

# --- هندل کردن دکمه‌های شیشه‌ای ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = str(query.from_user.id)
    user = get_user(user_id)

    if data == 'main_menu':
        await query.edit_message_text("منوی اصلی:", reply_markup=main_menu())

    elif data == 'prices':
        text = "💰 قیمت خدمات:\n\nقیمت هر گیگ 5,000 تومان\nتمامی سرور‌ها، از لحاظ تعداد کاربر و تاریخ انقضا نامحدود هستند."
        await query.edit_message_text(text, reply_markup=back_menu())

    elif data == 'support':
        text = "🎧 جهت ارتباط با پشتیبانی به آیدی زیر مراجعه کنید:\n@Void_66"
        await query.edit_message_text(text, reply_markup=back_menu())

    elif data == 'wallet':
        text = f"💳 کیف پول شما:\n\nموجودی فعلی: {user['wallet']:,} تومان\n\nبرای شارژ کیف پول به پشتیبانی پیام دهید."
        await query.edit_message_text(text, reply_markup=back_menu())

    elif data == 'check_usage':
        if not user['configs']:
            await query.edit_message_text("شما هیچ کانفیگ فعالی ندارید.", reply_markup=back_menu())
        else:
            text = "📦 حجم باقی مانده کانفیگ‌های شما:\n\n"
            for name, info in user['configs'].items():
                text += f"👤 نام: `{name}`\n📊 حجم: {info['gb']:.3f}G\n\n"
            await query.edit_message_text(text, reply_markup=back_menu(), parse_mode='Markdown')

    elif data == 'test_config':
        if user['test_count'] >= 3:
            await query.edit_message_text("❌ شما سقف ۳ بار دریافت کانفیگ تست را استفاده کرده‌اید.", reply_markup=back_menu())
        else:
            random_name = generate_random_name()
            user['configs'][random_name] = {'gb': 0.1}
            user['test_count'] += 1
            update_user(user_id, user)
            text = f"🎁 کانفیگ تست شما آماده شد!\n\n👤 نام کاربری: `{random_name}`\n📊 حجم: 0.100G\n\n(شما {3 - user['test_count']} بار دیگر می‌توانید تست بگیرید)"
            await query.edit_message_text(text, reply_markup=back_menu(), parse_mode='Markdown')

    # --- خرید کانفیگ جدید ---
    elif data == 'buy_new':
        context.user_data['action'] = 'buy_new_step1'
        await query.edit_message_text("🛒 چند گیگ حجم می‌خواهید؟\n(لطفاً فقط عدد انگلیسی بفرستید، مثلاً: 10)", reply_markup=back_menu())

    # --- تمدید کانفیگ ---
    elif data == 'renew':
        context.user_data['action'] = 'renew_step1'
        await query.edit_message_text("🔄 لطفاً نام کاربری (Username) کانفیگ قبلی خود را وارد کنید:", reply_markup=back_menu())

# --- هندل کردن پیام‌های متنی (برای خرید و تمدید) ---
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    text = update.message.text.strip()
    action = context.user_data.get('action')

    if action == 'buy_new_step1':
        if not text.isdigit():
            await update.message.reply_text("❌ لطفاً فقط عدد انگلیسی وارد کنید. مثلاً 10")
            return
        gb = float(text)
        price = gb * PRICE_PER_GB
        context.user_data['buy_gb'] = gb
        context.user_data['buy_price'] = price
        context.user_data['action'] = 'buy_new_step2'
        
        await update.message.reply_text(
            f"شما {gb} گیگ انتخاب کردید.\n💰 مبلغ قابل پرداخت: {price:,} تومان\n\nلطفاً یک نام کاربری انگلیسی (Username) برای کانفیگ خود وارد کنید:"
        )

    elif action == 'buy_new_step2':
        if not text.isalpha() or not text.isascii():
            await update.message.reply_text("❌ لطفاً فقط حروف انگلیسی وارد کنید.")
            return
        
        username = text.lower()
        if username in user['configs']:
            await update.message.reply_text("❌ این نام کاربری قبلاً استفاده شده است. یک نام دیگر وارد کنید.")
            return

        gb = context.user_data['buy_gb']
        price = context.user_data['buy_price']

        if user['wallet'] >= price:
            user['wallet'] -= price
            user['configs'][username] = {'gb': gb}
            update_user(user_id, user)
            context.user_data['action'] = None
            await update.message.reply_text(
                f"✅ خرید با موفقیت انجام شد!\n\n👤 نام کاربری: `{username}`\n📊 حجم: {gb}G\n💰 کسر شده از کیف پول: {price:,} تومان\n💳 موجودی جدید: {user['wallet']:,} تومان",
                reply_markup=back_menu(), parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ موجودی کیف پول شما کافی نیست!\n\n💰 مبلغ لازم: {price:,} تومان\n💳 موجودی شما: {user['wallet']:,} تومان\n\nلطفاً جهت شارژ کیف پول به پشتیبانی (@Void_66) پیام دهید.",
                reply_markup=back_menu()
            )
            context.user_data['action'] = None

    elif action == 'renew_step1':
        username = text.lower()
        if username not in user['configs']:
            await update.message.reply_text("❌ کانفیگی با این نام کاربری پیدا نشد.")
            return
        
        context.user_data['renew_username'] = username
        context.user_data['action'] = 'renew_step2'
        await update.message.reply_text(f"کانفیگ `{username}` پیدا شد.\nچند گیگ می‌خواهید به آن اضافه کنید؟ (فقط عدد انگلیسی)", parse_mode='Markdown')

    elif action == 'renew_step2':
        if not text.isdigit():
            await update.message.reply_text("❌ لطفاً فقط عدد انگلیسی وارد کنید.")
            return
        gb = float(text)
        price = gb * PRICE_PER_GB
        username = context.user_data['renew_username']

        if user['wallet'] >= price:
            user['wallet'] -= price
            user['configs'][username]['gb'] += gb
            update_user(user_id, user)
            context.user_data['action'] = None
            await update.message.reply_text(
                f"✅ تمدید با موفقیت انجام شد!\n\n👤 نام کاربری: `{username}`\n➕ حجم اضافه شده: {gb}G\n💳 موجودی جدید: {user['wallet']:,} تومان",
                reply_markup=back_menu(), parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ موجودی کیف پول کافی نیست!\n\n💰 مبلغ لازم: {price:,} تومان\n💳 موجودی شما: {user['wallet']:,} تومان\n\nبرای شارژ به @Void_466 پیام دهید.",
                reply_markup=back_menu()
            )
            context.user_data['action'] = None

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    print("بات روشن شد...")
    app.run_polling()

if __name__ == '__main__':
    main()
