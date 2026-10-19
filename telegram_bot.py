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
# Resumen Oficial con Códigos y Resultados Reales
# ---------------------------------------------------------
SUMMARY_TEXT = (
    "🏁 <b>BALANCE Y RECUENTO OFICIAL DE LA JORNADA</b> 🏁\n\n"
    "Familia, repasamos con total transparencia los resultados oficiales con los códigos de seguimiento de hoy en <b>@FreeTopTip</b>:\n\n"
    "✅ <b>PICKS ACERTADOS / VERDES:</b>\n"
    "• 🟢 <code>ENG-TOT-COV</code> | <b>Tottenham vs Coventry:</b> Victoria Tottenham + Over 1.5 [ACERTADO - Victoria 3-1] [Cuota 1.53]\n"
    "• 🟢 <code>ITA-MON-CAG</code> | <b>Monza vs Cagliari:</b> Monza HA 0.0 [ACERTADO - Goleada 4-0] [Cuota 1.62]\n"
    "• 🟢 <code>ITA-PAR-TOR</code> | <b>Parma vs Torino:</b> Torino HA 0.0 [ACERTADO - Victoria 0-3] [Cuota 1.70]\n\n"
    "🔄 <b>PICKS NULOS / DEVOLUCIÓN:</b>\n"
    "• 🔄 <code>ESP-GET-RAY</code> | <b>Getafe vs Rayo Vallecano:</b> Rayo Vallecano HA 0.0 [NULO - Empate 1-1 / Devolución] [Cuota 1.85]\n\n"
    "❌ <b>PICKS FALLADOS:</b>\n"
    "• 🔴 <code>TUR-TRAB-BESIK</code> | <b>Trabzonspor vs Beşiktaş:</b> Ambos Anotan [FALLADO - Victoria 2-0 Trabzonspor]\n"
    "• 🔴 <code>POR-BRA-GIL</code> | <b>Braga vs Gil Vicente:</b> Victoria Braga Directa [FALLADO - Victoria 1-2 Gil Vicente]\n\n"
    "📊 <b>ESTADÍSTICAS GLOBALES DEL DÍA:</b>\n"
    "• 🎯 <b>Aciertos (Verdes):</b> 3\n"
    "• 🔄 <b>Nulos (Devolución):</b> 1\n"
    "• ❌ <b>Fallos:</b> 2\n"
    "• 💰 <b>BALANCE NETO:</b> <b>+0.85 Unidades Netas (+0.85 U)</b>\n\n"
    "🔥 <i>¡Cerramos la jornada en verde (+0.85U) gracias al pleno en Italia e Inglaterra y la protección de nuestro hándicap en España!</i>"
)

# ---------------------------------------------------------
# Tarea de Publicación Automática
# ---------------------------------------------------------
async def publish_summary(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    logging.info("Publicando el resumen oficial con códigos y resultados...")

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
        logging.info("Resumen publicado con éxito.")
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
            "👋 <b>¡Hola! Bienvenido al bot oficial de @FreeTopTip.</b>",
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
