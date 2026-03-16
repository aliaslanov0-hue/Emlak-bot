import os
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
        "Baku Emlak Analiz Botuna Hos Geldiniz!\n\nKomutlar:\n/ara - Yeni arama yap\n/rapor - Son aramanin raporunu al\n/bildirim - Fiyat dusus bildirimi\n/yardim - Yardim"
    )

async def ara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Kiralik", callback_data="tip_kiralik"),
         InlineKeyboardButton("Satilik", callback_data="tip_satilik")],
        [InlineKeyboardButton("Her Ikisi", callback_data="tip_her")]
    ]
    await update.message.reply_text("Ne ariyorsunuz?", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data.startswith("tip_"):
        tip = query.data.replace("tip_", "")
        user_searches[user_id] = {"tip": tip}
        keyboard = [
            [InlineKeyboardButton("1 otaqli", callback_data="oda_1"),
             InlineKeyboardButton("2 otaqli", callback_data="oda_2")],
            [InlineKeyboardButton("3 otaqli", callback_data="oda_3"),
             InlineKeyboardButton("4+ otaqli", callback_data="oda_4")],
            [InlineKeyboardButton("Fark etmez", callback_data="oda_0")]
        ]
        await query.edit_message_text("Kac odali?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("oda_"):
        user_searches[user_id]["oda"] = query.data.replace("oda_", "")
        keyboard = [
            [InlineKeyboardButton("0-300 AZN", callback_data="fiyat_0_300"),
             InlineKeyboardButton("300-600 AZN", callback_data="fiyat_300_600")],
            [InlineKeyboardButton("600-1000 AZN", callback_data="fiyat_600_1000"),
             InlineKeyboardButton("1000+ AZN", callback_data="fiyat_1000_99999")],
            [InlineKeyboardButton("Fark etmez", callback_data="fiyat_0_99999")]
        ]
        await query.edit_message_text("Fiyat araligi?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("fiyat_"):
        parts = query.data.replace("fiyat_", "").split("_")
        user_searches[user_id]["min_fiyat"] = int(parts[0])
        user_searches[user_id]["max_fiyat"] = int(parts[1])
        user_searches[user_id]["bekleniyor"] = "semt"
        await query.edit_message_text("Hangi semtte ariyorsunuz?\nOrnek: Nasimi, Xetai, Sabuncu\nVeya 'her yer' yazin.")

async def mesaj_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    metin = update.message.text.strip()

    if user_id in user_searches and user_searches[user_id].get("bekleniyor") == "semt":
        user_searches[user_id]["semt"] = metin
        user_searches[user_id].pop("bekleniyor")
        await update.message.reply_text("Ilanlar aranıyor, lutfen bekleyin...")
        try:
            ilanlar = await search_listings(user_searches[user_id])
            if not ilanlar:
                await update.message.reply_text("Ilan bulunamadi. /ara ile tekrar deneyin.")
                return
            user_searches[user_id]["ilanlar"] = ilanlar
            rapor = generate_report(ilanlar, user_searches[user_id])
            await update.message.reply_text(rapor, disable_web_page_preview=True)
            harita_url = "https://www.google.com/maps/search/emlak+" + metin + "+Baku/@40.4093,49.8671,13z"
            keyboard = [[InlineKeyboardButton("Haritada Gor", url=harita_url)]]
            await update.message.reply_text("Bolgeyi haritada gormek ister misiniz?", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            logger.error("Hata: " + str(e))
            await update.message.reply_text("Hata olustu. Tekrar deneyin.")
    else:
        await update.message.reply_text("Arama icin /ara yazin.")

async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_searches or "ilanlar" not in user_searches.get(user_id, {}):
        await update.message.reply_text("Henuz arama yapmadiniz. /ara ile baslayin.")
        return
    await update.message.reply_text(generate_report(user_searches[user_id]["ilanlar"], user_searches[user_id]), disable_web_page_preview=True)

async def bildirim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Takibe alindi! Fiyat dususunde bilgilendireceğim.")

async def yardim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/ara - Arama yap\n/rapor - Rapor al\n/bildirim - Bildirim kur")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ara", ara))
    app.add_handler(CommandHandler("rapor", rapor))
    app.add_handler(CommandHandler("bildirim", bildirim))
    app.add_handler(CommandHandler("yardim", yardim))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj_handler))
    logger.info("Bot basladi...")
    app.run_polling()

if __name__ == "__main__":
    main()
