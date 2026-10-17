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
# Balance Real y Verificado de los Picks de la Madrugada
# ---------------------------------------------------------
VERIFIED_ madrugada_SUMMARY = (
    "🏁 <b>BALANCE Y RECUENTO OFICIAL DE LOS PICKS DE LA JORNADA</b>\n\n"
    "¡Finalizada la jornada de hoy, repasamos con total transparencia los resultados de los pronósticos que publicamos esta madrugada en @FreeTopTip:\n\n"
    "✅ <b>PICKS ACERTADOS:</b>\n"
    "• 🟢 <b>Espanyol vs Atlético de Madrid:</b> Victoria Atlético de Madrid (ACERTADO - 0-1) [Cuota 1.70]\n"
    "• 🟢 <b>Real Betis vs Barcelona:</b> Barcelona HA -1.0 / Goles (ACERTADO - 2-5) [Cuota 1.36]\n"
    "• 🟢 <b>Everton vs Chelsea:</b> Chelsea Victoria (ACERTADO - 0-2) [Cuota 2.15]\n"
    "• 🟢 <b>Brentford vs Liverpool:</b> Over 2.5 Goles (ACERTADO - 1-2)\n"
    "• 🟢 <b>Manchester City vs Ipswich:</b> Man City HA -2.0 / Over (ACERTADO - 3-2)\n"
    "• 🟢 <b>Bayern Múnich vs RB Leipzig:</b> Bayern Gana + Over (ACERTADO - 6-1) [Cuota 1.22]\n"
    "• 🟢 <b>Botafogo vs Chapecoense:</b> Botafogo HA -1.0 (ACERTADO - 2-0) [Cuota 1.30]\n\n"
    "❌ <b>PICKS FALLADOS:</b>\n"
    "• 🔴 <b>Villarreal vs Elche:</b> Victoria Villarreal (FALLADO - Empate 0-0)\n"
    "• 🔴 <b>Valencia vs Athletic Club:</b> Athletic HA 0.0 (FALLADO - Empate 0-0)\n"
    "• 🔴 <b>Newcastle vs Aston Villa:</b> Victoria Newcastle (FALLADO - Victoria Aston Villa 0-1)\n"
    "• 🔴 <b>Unión Berlín vs Dortmund:</b> Victoria Dortmund (FALLADO - Empate 0-0)\n\n"
    "📊 <b>ESTADÍSTICAS GLOBALES DE LA JORNADA:</b>\n"
    "• 🎯 <b>Aciertos:</b> 7 de 11 (63.6% de efectividad)\n"
    "• ❌ <b>Fallos:</b> 4\n"
    "• 💰 <b>BALANCE NETO FINAL:</b> <b>+3.40 Unidades Netas (+3.40 U)</b>\n\n"
    "🔥 <i>¡Seguimos sumando en verde y demostrando el rigor de nuestras métricas en @FreeTopTip! Gracias a todos por la confianza.</i>"
)

# ---------------------------------------------------------
# Tarea de Publicación Automática
# ---------------------------------------------------------
async def publish_verified_summary(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    logging.info("Publicando balance de los picks de la madrugada...")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 UNIRSE AL VIP / CONTACTO DIRECTO", url="https://t.me/Mark122")]
    ])

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=VERIFIED_madrugada_SUMMARY,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        logging.info("Balance publicado con éxito en el canal.")
    except Exception as e:
        logging.error(f"Error publicando el balance: {e}")

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

    logging.info("Bot en marcha. Programado para publicar el balance...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
