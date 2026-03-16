import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from scraper import search_listings
from report import generate_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")

user_searches = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏠 *Baku Emlak Analiz Botuna Hoş Geldiniz!*\n\nKomutlar:\n🔍 /ara - Yeni arama yap\n📊 /rapor - Son aramanın raporunu al\n🔔 /bildirim - Fiyat düşüş bildirimi\n❓ /yardim - Yardım",
        parse_mode="Markdown"
    )

async def ara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🏠 Kiralık", callback_data="tip_kiralik"),
         InlineKeyboardButton("🏢 Satılık", callback_data="tip_satilik")],
        [InlineKeyboardButton("🔄 Her İkisi", callback_data="tip_her")]
    ]
    await update.message.reply_text("Ne arıyorsunuz?", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data.startswith("tip_"):
        tip = query.data.replace("tip_", "")
        user_searches[user_id] = {"tip": tip}
        keyboard = [
            [InlineKeyboardButton("1 otaqlı", callback_data="oda_1"), InlineKeyboardButton("2 otaqlı", callback_data="oda_2")],
            [InlineKeyboardButton("3 otaqlı", callback_data="oda_3"), InlineKeyboardButton("4+ otaqlı", callback_data="oda_4")],
            [InlineKeyboardButton("Fark etmez", callback_data="oda_0")]
        ]
        await query.
