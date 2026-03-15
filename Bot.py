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
        await query.edit_message_text("Kaç odalı?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("oda_"):
        user_searches[user_id]["oda"] = query.data.replace("oda_", "")
        keyboard = [
            [InlineKeyboardButton("0-300 AZN", callback_data="fiyat_0_300"), InlineKeyboardButton("300-600 AZN", callback_data="fiyat_300_600")],
            [InlineKeyboardButton("600-1000 AZN", callback_data="fiyat_600_1000"), InlineKeyboardButton("1000+ AZN", callback_data="fiyat_1000_99999")],
            [InlineKeyboardButton("Fark etmez", callback_data="fiyat_0_99999")]
        ]
        await query.edit_message_text("Fiyat aralığı?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("fiyat_"):
        parts = query.data.replace("fiyat_", "").split("_")
        user_searches[user_id]["min_fiyat"] = int(parts[0])
        user_searches[user_id]["max_fiyat"] = int(parts[1])
        await query.edit_message_text("Hangi semtte arıyorsunuz?\n\nÖrnek: Nəsimi, Xətai, Sabunçu\n\nVeya 'Hər yer' yazın.")
        user_searches[user_id]["bekleniyor"] = "semt"

async def mesaj_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    metin = update.message.text.strip()

    if user_id in user_searches and user_searches[user_id].get("bekleniyor") == "semt":
        user_searches[user_id]["semt"] = metin
        user_searches[user_id].pop("bekleniyor")
        await update.message.reply_text("⏳ İlanlar aranıyor...")
        try:
            ilanlar = await search_listings(user_searches[user_id]
