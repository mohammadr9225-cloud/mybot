import os
import random
import string
import asyncpg
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

PRICE_PER_GB = 5000
SUPPORT_ID = "@Void_6646" # آیدی اصلاح شده

async def get_db():
    url = DATABASE_URL.replace("postgres://", "postgresql://", 1) if DATABASE_URL.startswith("postgres://") else DATABASE_URL
    return await asyncpg.connect(url)

async def init_db():
    conn = await get_db()
    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                wallet BIGINT DEFAULT 0,
                test_count INT DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS configs (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                username TEXT UNIQUE,
                gb REAL,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
        ''')
    finally:
        await conn.close()

async def get_user_data(user_id):
    conn = await get_db()
    try:
        user = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
        if not user:
            await conn.execute('INSERT INTO users (user_id) VALUES ($1)', user_id)
            user = await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
        configs = await conn.fetch('SELECT username, gb FROM configs WHERE user_id = $1', user_id)
        return user, {row['username']: {'gb': row['gb']} for row in configs}
    finally:
        await conn.close()

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

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='main_menu')]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_user_data(update.effective_user.id)
    await update.message.reply_text("سلام! به بات BlueVPN خوش آمدید 👋", reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    user, configs = await get_user_data(user_id)

    if data == 'main_menu':
        await query.edit_message_text("منوی اصلی:", reply_markup=main_menu())
    elif data == 'prices':
        await query.edit_message_text("💰 قیمت هر گیگ 5,000 تومان\nتمامی سرور‌ها نامحدود هستند.", reply_markup=back_menu())
    elif data == 'support':
        await query.edit_message_text(f"🎧 پشتیبانی: {SUPPORT_ID}", reply_markup=back_menu())
    elif data == 'wallet':
        await query.edit_message_text(f"💳 موجودی: {user['wallet']:,} تومان", reply_markup=back_menu())
    elif data == 'check_usage':
        if not configs:
            await query.edit_message_text("شما هیچ کانفیگی ندارید.", reply_markup=back_menu())
        else:
            text = "📦 کانفیگ‌های شما:\n\n"
            for name, info in configs.items():
                text += f"👤 `{name}`\n📊 {info['gb']:.3f}G\n\n"
            await query.edit_message_text(text, reply_markup=back_menu(), parse_mode='Markdown')
    elif data == 'test_config':
        if user['test_count'] >= 3:
            await query.edit_message_text("❌ سقف ۳ بار تست استفاده شده.", reply_markup=back_menu())
        else:
            random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            conn = await get_db()
            try:
                await conn.execute('INSERT INTO configs (user_id, username, gb) VALUES ($1, $2, $3)', user_id, random_name, 0.1)
                await conn.execute('UPDATE users SET test_count = test_count + 1 WHERE user_id = $1', user_id)
            finally:
                await conn.close()
            await query.edit_message_text(f"🎁 تست شما:\n👤 `{random_name}`\n📊 0.100G", reply_markup=back_menu(), parse_mode='Markdown')
    elif data == 'buy_new':
        context.user_data['action'] = 'buy_new_step1'
        await query.edit_message_text("🛒 چند گیگ می‌خواهید؟ (فقط عدد)", reply_markup=back_menu())
    elif data == 'renew':
        context.user_data['action'] = 'renew_step1'
        await query.edit_message_text("🔄 نام کانفیگ قبلی را وارد کنید:", reply_markup=back_menu())

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user, configs = await get_user_data(user_id)
    text = update.message.text.strip()
    action = context.user_data.get('action')

    if action == 'buy_new_step1':
        if not text.isdigit(): return await update.message.reply_text("❌ فقط عدد وارد کنید.")
        context.user_data.update({'buy_gb': float(text), 'buy_price': float(text) * PRICE_PER_GB, 'action': 'buy_new_step2'})
        await update.message.reply_text(f"مبلغ: {float(text) * PRICE_PER_GB:,} تومان\nیک نام انگلیسی وارد کنید:")
    
    elif action == 'buy_new_step2':
        if not text.isalpha() or not text.isascii(): return await update.message.reply_text("❌ فقط حروف انگلیسی.")
        if text.lower() in configs: return await update.message.reply_text("❌ نام تکراری است.")
        if user['wallet'] >= context.user_data['buy_price']:
            conn = await get_db()
            try:
                await conn.execute('UPDATE users SET wallet = wallet - $1 WHERE user_id = $2', context.user_data['buy_price'], user_id)
                await conn.execute('INSERT INTO configs (user_id, username, gb) VALUES ($1, $2, $3)', user_id, text.lower(), context.user_data['buy_gb'])
            finally:
                await conn.close()
            context.user_data['action'] = None
            await update.message.reply_text(f"✅ خرید موفق!\n👤 `{text.lower()}`", reply_markup=back_menu(), parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ موجودی کافی نیست. برای شارژ به {SUPPORT_ID} پیام دهید.", reply_markup=back_menu())
            context.user_data['action'] = None

    elif action == 'renew_step1':
        if text.lower() not in configs: return await update.message.reply_text("❌ کانفیگ پیدا نشد.")
        context.user_data.update({'renew_user': text.lower(), 'action': 'renew_step2'})
        await update.message.reply_text("چند گیگ اضافه شود؟ (فقط عدد)")

    elif action == 'renew_step2':
        if not text.isdigit(): return await update.message.reply_text("❌ فقط عدد.")
        price = float(text) * PRICE_PER_GB
        if user['wallet'] >= price:
            conn = await get_db()
            try:
                await conn.execute('UPDATE users SET wallet = wallet - $1 WHERE user_id = $2', price, user_id)
                await conn.execute('UPDATE configs SET gb = gb + $1 WHERE user_id = $2 AND username = $3', float(text), user_id, context.user_data['renew_user'])
            finally:
                await conn.close()
            context.user_data['action'] = None
            await update.message.reply_text("✅ تمدید شد!", reply_markup=back_menu())
        else:
            await update.message.reply_text(f"❌ موجودی کافی نیست. به {SUPPORT_ID} پیام دهید.", reply_markup=back_menu())
            context.user_data['action'] = None

async def post_init(application: Application):
    await init_db()

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling()

if __name__ == '__main__':
    main()
