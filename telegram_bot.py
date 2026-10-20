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
# Resumen Oficial con Resultados Reales Exactos
# ---------------------------------------------------------
SUMMARY_TEXT = (
    "🏁 <b>BALANCE Y RECUENTO OFICIAL DE LA JORNADA DE CHAMPIONS</b> 🏁\n\n"
    "Familia, repasamos con total transparencia los resultados de los partidos analizados hoy en <b>@FreeTopTip</b>:\n\n"
    "✅ <b>PICKS ACERTADOS / VERDES:</b>\n"
    "• 🟢 <code>UCL-FEN-SLA</code> | <b>Fenerbahçe vs Slavia Praga:</b> Victoria Fenerbahçe [ACERTADO por 2 Goles de Ventaja ⚡] [Cuota 1.61]\n"
    "• 🟢 <code>UCL-SAB-DOR</code> | <b>Sabah vs Dortmund:</b> Dortmund HA -1.5 [ACERTADO - Victoria 0-3] [Cuota 1.75]\n"
    "• 🟢 <code>UCL-LIV-VIL</code> | <b>Liverpool vs Villarreal:</b> Victoria Liverpool + Over 1.5 [ACERTADO - Victoria 3-1] [Cuota 1.72]\n"
    "• 🟢 <code>UCL-MCI-AEK</code> | <b>Man City vs AEK Atenas:</b> Man City HA -2.5 [ACERTADO - Goleada 4-0] [Cuota 1.85]\n"
    "• 🟢 <code>UCL-NAP-BOD</code> | <b>Nápoles vs Bodo/Glimt:</b> Victoria Nápoles [ACERTADO - Victoria 2-0] [Cuota 1.61]\n"
    "• 🟢 <code>UCL-PSG-BAR</code> | <b>PSG vs Barcelona:</b> Ambos Anotan + Over 2.5 [ACERTADO - Marcador 2-2] [Cuota 1.70]\n"
    "• 🟢 <code>UCL-ROM-SLO</code> | <b>Roma vs Slovan Bratislava:</b> Roma HA -1.5 [ACERTADO - Victoria 3-0] [Cuota 1.55]\n"
    "• 🟢 <code>UCL-STU-ATM</code> | <b>Stuttgart vs At. Madrid:</b> At. Madrid HA 0.0 [ACERTADO - Victoria 1-2] [Cuota 1.55]\n\n"
    "❌ <b>PICKS FALLADOS:</b>\n"
    "• 🔴 <code>UCL-OPO-PSV</code> | <b>Oporto vs PSV:</b> Ambos Equipos Anotan [FALLADO - Marcador 0-1]\n\n"
    "📊 <b>ESTADÍSTICAS TOTALES DE LA JORNADA:</b>\n"
    "• 🎯 <b>Aciertos (Verdes):</b> 8\n"
    "• 🔄 <b>Nulos:</b> 0\n"
    "• ❌ <b>Fallos:</b> 1\n"
    "• 💰 <b>BALANCE NETO DEL DÍA:</b> <b>+3.34 Unidades Netas (+3.34 U)</b>\n\n"
    "───────────────\n"
    "🔥 <b>¡8 VERDES DE 9 EN UNA JORNADA ESPECTACULAR!</b> 🔥\n\n"
    "Cerramos otro día sumando +3.34U de beneficio neto gracias al análisis métrico de la Champions League. La consistencia sigue siendo nuestra mayor garantía.\n\n"
    "🚨 <b>OFERTA FLASH VIP PREMIUM</b> 🚨\n"
    "Consigue acceso al <b>Canal VIP Premium</b> para lo que resta de semana por solo <b>9,99€</b> (Precio habitual 29,99€).\n\n"
    "👇 <b>PULSA ABAJO Y ÚNETE AL VIP AHORA:</b>"
)

# ---------------------------------------------------------
# Tarea de Publicación Automática
# ---------------------------------------------------------
async def publish_summary(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    logging.info("Publicando el resumen con resultados reales del día...")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 UNIRSE AL VIP POR 9,99€ (CLICK AQUÍ)", url="https://t.me/Mark122")]
    ])

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=SUMMARY_TEXT,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        logging.info("Resumen corregido publicado con éxito.")
    except Exception as e:
        logging.error(f"Error al enviar el resumen: {e}")

# ---------------------------------------------------------
# Controladores del Bot
# ---------------------------------------------------------
async def start_command(update: object, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 UNIRSE AL VIP (9,99€)", url="https://t.me/Mark122")]
    ])
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            "👋 <b>¡Hola! Bienvenido al bot oficial de @FreeTopTip.</b>\n\n"
            "Aprovecha la promoción del VIP para lo que resta de semana por solo 9,99€. Pulsa el botón de abajo para hablar directamente conmigo.",
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
