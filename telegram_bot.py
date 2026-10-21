import os
import time
import logging
import threading
from flask import Flask
from zoneinfo import ZoneInfo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Servidor Flask simulado para engañar a Render Web Service
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot activo", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---------------------------------------------------------
# Configuración y Log
# ---------------------------------------------------------
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "5268021862:AAFD3fiHf0MTeVdKqHydfYSfyvMWaKtTxNU")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@FreeTopTip")

SPAIN_TZ = ZoneInfo("Europe/Madrid")

# ---------------------------------------------------------
# 1. Resumen de Resultados Reales de la Jornada Japonesa
# ---------------------------------------------------------
JAPAN_RESULTS_POST = {
    "code": "JPN-RESULTS-SUMMARY",
    "text": (
        "🇯🇵 <b>RECAP Y RESULTADOS REALES - JORNADA JAPÓN</b> 🇯🇵\n\n"
        "¡Finalizados todos los partidos de la jornada matutina en Japón! Aquí tenéis el desglose oficial de marcadores:\n\n"
        "✅ <b>Fagiano Okayama 2 - 0 Mito Hollyhock</b>\n"
        "➖ <b>FC Tokyo 0 - 0 Kashiwa Reysol</b>\n"
        "✅ <b>Kawasaki Frontale 2 - 1 Vissel Kobe</b>\n"
        "➖ <b>Kyoto Sanga FC 2 - 2 Kashima Antlers</b>\n"
        "➖ <b>Nagoya Grampus 1 - 1 Cerezo Osaka</b>\n"
        "✅ <b>Shimizu S-Pulse 0 - 5 Machida Zelvia</b>\n"
        "❌ <b>V-Varen Nagasaki 4 - 0 Sanfrecce Hiroshima</b>\n"
        "➖ <b>Yokohama F-Marinos 2 - 2 Tokyo Verdy</b>\n"
        "✅ <b>Urawa Red Diamonds 3 - 2 JEF Utd Chiba</b>\n\n"
        "📌 <i>Seguimos ajustando y sumando en las ligas internacionales.</i>"
    )
}

# ---------------------------------------------------------
# 2. Anuncio Especial Champions League & Promo Premium
# ---------------------------------------------------------
CHAMPIONS_ANNOUNCEMENT_POST = {
    "code": "UCL-PROMO-ANNOUNCEMENT",
    "text": (
        "🔥 <b>¡ATENCIÓN FAMILIA! HOY TENEMOS CHAMPIONS LEAGUE</b> 🔥\n\n"
        "Para la jornada europea de hoy, <b>publicaremos en abierto únicamente UN PARTIDO que nos encanta</b> con un análisis completísimo y de máximo valor.\n\n"
        "🔒 <b>El resto de la jornada de Champions League queda reservada en exclusiva para nuestro grupo PREMIUM.</b>\n\n"
        "🎁 <b>PROMOCIÓN ESPECIAL GRATUITA:</b>\n"
        "Dejaremos el acceso al canal <b>PREMIUM COMPLETAMENTE GRATUITO</b> desde este momento <b>hasta las 16:45 CEST</b>.\n\n"
        "📩 Todo el que quiera acceder de manera gratuita solo tiene que hablarme directamente al privado antes de las 16:45 CEST.\n\n"
        "👇 <b>¡PULSA AQUÍ PARA ENTRAR GRATIS AL PREMIUM!</b>"
    )
}

# ---------------------------------------------------------
# Tarea de Publicación Automática
# ---------------------------------------------------------
async def publish_all_picks(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    logging.info("Iniciando publicación del resumen de Japón y promoción Champions...")

    keyboard_vip = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 HABLAR AL PRIVADO / ENTRAR GRATIS AL PREMIUM", url="https://t.me/Mark122")]
    ])

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=JAPAN_RESULTS_POST["text"],
            parse_mode="HTML"
        )
        logging.info("Publicado el resumen de resultados de Japón.")
        time.sleep(3)

        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=CHAMPIONS_ANNOUNCEMENT_POST["text"],
            parse_mode="HTML",
            reply_markup=keyboard_vip
        )
        logging.info("Publicado el anuncio de la Champions y promo Premium.")

    except Exception as e:
        logging.error(f"Error al enviar publicaciones: {e}")

# ---------------------------------------------------------
# Controladores del Bot
# ---------------------------------------------------------
async def start_command(update: object, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 ENTRAR GRATIS AL PREMIUM", url="https://t.me/Mark122")]
    ])
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            "👋 <b>¡Hola! Bienvenido al bot oficial de @FreeTopTip.</b>\n\n"
            "Aprovecha el acceso <b>GRATUITO al PREMIUM</b> hasta las 16:45 CEST. Pulsa el botón de abajo para hablar directamente conmigo.",
            parse_mode="HTML",
            reply_markup=keyboard
        )

# ---------------------------------------------------------
# Función Principal
# ---------------------------------------------------------
def main():
    # Iniciar servidor web Flask en segundo plano
    threading.Thread(target=run_flask, daemon=True).start()

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    if application.job_queue:
        application.job_queue.run_once(publish_all_picks, when=5)

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("vip", start_command))

    logging.info("Bot activo...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
