import os
import time
import logging
from zoneinfo import ZoneInfo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------------------------------------------------
# Configuración y Log
# ---------------------------------------------------------
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8657360203:AAHdtvCjS5o4_-p2Bk7w6mSDBBA2gbHi470")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@FreeTopTip")

SPAIN_TZ = ZoneInfo("Europe/Madrid")

# ---------------------------------------------------------
# Resumen Oficial de Resultados
# ---------------------------------------------------------
SUMMARY_TEXT = (
    "🏁 <b>BALANCE Y RECUENTO OFICIAL DE LOS PICKS DE ANOCHE</b> 🏁\n\n"
    "Familia, repasamos con total transparencia los resultados oficiales de los pronósticos seleccionados anoche en <b>@FreeTopTip</b>:\n\n"
    "✅ <b>PICKS ACERTADOS:</b>\n"
    "• 🟢 <b>Bahia vs Flamengo:</b> Victoria Flamengo Directa [ACERTADO - Victoria 0-3] [Cuota 1.96]\n"
    "• 🟢 <b>Estudiantes Río Cuarto vs Aldosivi:</b> Estudiantes R.C. HA 0.0 [ACERTADO - Remontada y victoria 2-1] [Cuota 1.90]\n\n"
    "🔄 <b>PICKS NULOS:</b>\n"
    "• 🔄 <b>Clube do Remo vs Red Bull Bragantino:</b> Bragantino HA 0.0 [NULO - Empate 1-1 / Devolución] [Cuota 1.55]\n\n"
    "❌ <b>PICKS FALLADOS:</b>\n"
    "• 🔴 <b>Estudiantes de La Plata vs San Lorenzo:</b> Victoria Estudiantes L.P. [FALLADO - Victoria San Lorenzo 1-2]\n\n"
    "📊 <b>ESTADÍSTICAS DEL BLOQUE:</b>\n"
    "• 🎯 <b>Aciertos (Verdes):</b> 2\n"
    "• 🔄 <b>Nulos (Devolución):</b> 1\n"
    "• ❌ <b>Fallos:</b> 1\n"
    "• 💰 <b>BALANCE NETO:</b> <b>+1.86 Unidades Netas (+1.86 U)</b>\n\n"
    "🔥 <i>¡Cerramos la noche en positivo (+1.86U) gracias a la remontada de Estudiantes de Río Cuarto y la goleada del Flamengo!</i>"
)

# ---------------------------------------------------------
# Tarea de Publicación Automática
# ---------------------------------------------------------
async def publish_summary(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    logging.info("Publicando el resumen de los resultados reales de anoche...")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 UNIRSE AL VIP / CONTACTO DIRECTO", url="https://t.me/Mark122")]
    ])

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=SUMMARY_TEXT,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        logging.info("Resumen publicado con éxito en el canal.")
    except Exception as e:
        logging.error(f"Error al enviar el resumen: {e}")

# ---------------------------------------------------------
# Controladores del Bot
# ---------------------------------------------------------
async def start_command(update: object, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 HABLAR CON MARK122", url="https://t.me/Mark122")]
    ])
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            "👋 <b>¡Hola! Bienvenido al bot oficial de @FreeTopTip.</b>\n\n"
            "Para adquirir pases VIP o resolver cualquier duda, pulsa el botón de abajo para contactar directamente.",
            parse_mode="HTML",
            reply_markup=keyboard
        )

# ---------------------------------------------------------
# Función Principal
# ---------------------------------------------------------
def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    if application.job_queue:
        application.job_queue.run_once(publish_summary, when=5)

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("vip", start_command))

    logging.info("Bot activo...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
