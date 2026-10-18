import os
import time
import logging
from zoneinfo import ZoneInfo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------------------------------------------------
# Configuración y Entorno
# ---------------------------------------------------------
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8657360203:AAHdtvCjS5o4_-p2Bk7w6mSDBBA2gbHi470")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@FreeTopTip")

SPAIN_TZ = ZoneInfo("Europe/Madrid")

# ---------------------------------------------------------
# Balance Oficial y Resumen de los Picks de Hoy
# ---------------------------------------------------------
SUMMARY_CAPTION = (
    "🏁 <b>BALANCE Y RECUENTO OFICIAL DE LOS PICKS DE HOY</b>\n\n"
    "Familia, repasamos con total transparencia los resultados oficiales de los pronósticos seleccionados hoy para @FreeTopTip:\n\n"
    "✅ <b>PICKS ACERTADOS:</b>\n"
    "• 🟢 <b>Real Madrid vs Sevilla:</b> Real Madrid Gana + Over 2.5 Goles [ACERTADO - 🟢 Verde cobrado con los 2 goles de ventaja de Bet365 / Güler 30', Mbappé 37' y 63']\n"
    "• 🟢 <b>Celta de Vigo vs Alavés:</b> Celta HA 0.0 (ACERTADO - Victoria local 2-1) [Cuota 1.55]\n"
    "• 🟢 <b>Nottingham Forest vs Arsenal:</b> Victoria Arsenal (ACERTADO - Victoria 0-1) [Cuota 1.61]\n"
    "• 🟢 <b>Brighton vs Crystal Palace:</b> Victoria Brighton (ACERTADO - Goleada 5-0) [Cuota 1.50]\n"
    "• 🟢 <b>AC Milan vs Atalanta:</b> Both Teams to Score + Over 2.5 (ACERTADO - Marcador 3-2) [Cuota 1.85]\n"
    "• 🟢 <b>Bayer Leverkusen vs Friburgo:</b> Victoria Bayer Leverkusen (ACERTADO - Victoria 2-1) [Cuota 1.66]\n"
    "• 🟢 <b>Lyon vs Niza:</b> Victoria Lyon (ACERTADO - Marcador 2-1) [Cuota 1.75]\n"
    "• 🟢 <b>Halmstad vs Hammarby:</b> Victoria Hammarby (ACERTADO - Victoria 0-1) [Cuota 1.22]\n"
    "• 🟢 <b>Atlético Mineiro vs Coritiba:</b> Victoria Atlético Mineiro (ACERTADO - Victoria 1-0) [Cuota 1.66]\n\n"
    "❌ <b>PICKS FALLADOS:</b>\n"
    "• 🔴 <b>Wellington Phoenix vs Melbourne Victory:</b> Melbourne Victory HA 0.0 (FALLADO - Victoria Wellington 2-1)\n"
    "• 🔴 <b>Cambuur vs AZ Alkmaar:</b> Victoria AZ Alkmaar (FALLADO - Empate 2-2)\n"
    "• 🔴 <b>Istanbul Basaksehir vs Gaziantep:</b> Victoria Istanbul Basaksehir (FALLADO)\n\n"
    "📊 <b>ESTADÍSTICAS GLOBALES DEL DÍA:</b>\n"
    "• 🎯 <b>Aciertos:</b> 9 de 12 (75% de efectividad)\n"
    "• ❌ <b>Fallos:</b> 3\n"
    "• 💰 <b>BALANCE NETO FINAL:</b> <b>+4.25 Unidades Netas (+4.25 U)</b>\n\n"
    "🔥 <i>¡Súper jornada dominical cerrada en verde (+4.25U) gracias a la regla de 2 goles de ventaja y nuestras lecturas en @FreeTopTip!</i>"
)

# ---------------------------------------------------------
# Tarea de Publicación Automática
# ---------------------------------------------------------
async def publish_verified_summary(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    logging.info("Publicando resumen de aciertos y fallos de la jornada...")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 UNIRSE AL VIP / CONTACTO DIRECTO", url="https://t.me/Mark122")]
    ])

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=SUMMARY_CAPTION,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        logging.info("Resumen publicado con éxito en el canal.")
    except Exception as e:
        logging.error(f"Error publicando el resumen: {e}")

# ---------------------------------------------------------
# Controladores de Telegram
# ---------------------------------------------------------
async def start_command(update: object, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 HABLAR CON MARK122", url="https://t.me/Mark122")]
    ])
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            "👋 <b>¡Hola! Bienvenido al bot oficial de @FreeTopTip.</b>\n\n"
            "Para unirte a nuestro Canal VIP o consultar dudas, pulsa el botón de abajo para hablar conmigo directamente.",
            parse_mode="HTML",
            reply_markup=keyboard
        )

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    job_queue = application.job_queue
    if job_queue:
        job_queue.run_once(publish_verified_summary, when=5)

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("vip", start_command))

    logging.info("Bot en marcha sin errores...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
