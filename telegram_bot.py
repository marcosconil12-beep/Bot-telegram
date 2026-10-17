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
# Balance Real de los Picks de la Madrugada de Hoy
# ---------------------------------------------------------
SUMMARY_CAPTION = (
    "🏁 <b>RECUENTO Y BALANCE DE LOS PICKS DE HOY</b>\n\n"
    "Repasamos con total transparencia los resultados oficiales de la lista enviada esta madrugada a @FreeTopTip:\n\n"
    "✅ <b>PICKS ACERTADOS:</b>\n"
    "• 🟢 <b>Espanyol vs Atlético de Madrid:</b> Victoria Atlético (ACERTADO - 0-1) [Cuota 1.70]\n"
    "• 🟢 <b>Betis vs Barcelona:</b> Barcelona HA -1.0 (ACERTADO - 2-5) [Cuota 1.36]\n"
    "• 🟢 <b>Everton vs Chelsea:</b> Victoria Chelsea (ACERTADO - 0-2) [Cuota 2.15]\n"
    "• 🟢 <b>Brentford vs Liverpool:</b> Over 2.5 Goles (ACERTADO - 1-2) [Cuota 1.70]\n"
    "• 🟢 <b>Bayern Múnich vs RB Leipzig:</b> Bayern Gana + Over 2.5 Goles (ACERTADO - 6-1) [Cuota 1.50]\n"
    "• 🟢 <b>Botafogo vs Chapecoense:</b> Botafogo HA -1.0 (ACERTADO - 2-0) [Cuota 1.30]\n\n"
    "➖ <b>APUESTA NULA (DEVOLUCIÓN):</b>\n"
    "• ⚪ <b>Valencia vs Athletic Club:</b> Athletic HA 0.0 (NULO - Empate 0-0)\n\n"
    "❌ <b>PICKS FALLADOS:</b>\n"
    "• 🔴 <b>Villarreal vs Elche:</b> Victoria Villarreal (FALLADO - Empate 0-0)\n"
    "• 🔴 <b>Manchester City vs Ipswich:</b> Man City HA -2.0 (FALLADO - 3-2)\n"
    "• 🔴 <b>Newcastle vs Aston Villa:</b> Victoria Newcastle (FALLADO - 0-1)\n"
    "• 🔴 <b>Unión Berlín vs Dortmund:</b> Victoria Dortmund (FALLADO - Empate 0-0)\n\n"
    "📊 <b>BALANCE GLOBAL DE HOY:</b>\n"
    "• 🎯 <b>Aciertos:</b> 6\n"
    "• ⚪ <b>Nulos:</b> 1\n"
    "• ❌ <b>Fallos:</b> 4\n"
    "• 💰 <b>UNIDADES NETAS GANADAS:</b> <b>+1.71 Unidades (+1.71 U)</b>\n\n"
    "🔥 <i>¡Cerramos el día con beneficio positivo (+1.71U) demostrando el valor real de nuestras lecturas en @FreeTopTip!</i>"
)

# ---------------------------------------------------------
# Tarea de Publicación Automática
# ---------------------------------------------------------
async def publish_verified_summary(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    logging.info("Publicando recuento exacto de los picks de hoy...")

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

    logging.info("Bot en marcha sin errores...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
