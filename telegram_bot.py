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
# Pronósticos de Argentina y Brasil
# ---------------------------------------------------------
MATCH_PICKS = [
    {
        "code": "ARG-ESTRC-ALD",
        "text": (
            "🇦🇷 <b>ARGENTINA - LIGA PROFESIONAL</b>\n"
            "⏰ <b>23:00 CEST</b> | ⚔️ <b>Estudiantes Río Cuarto vs Aldosivi</b>\n\n"
            "📊 <b>CÓDIGO DE SEGUIMIENTO:</b> <code>ARG-ESTRC-ALD</code>\n\n"
            "• ⚽ <b>xG Proyectado:</b> 1.10 vs 1.05 | Menos de 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Empate o Estudiantes Río Cuarto (HA 0.0) [Cuota 1.90]\n"
            "• 🚩 <b>Córners:</b> Under 9.5 Córners\n"
            "• 🟨 <b>Tarjetas:</b> Over 4.5 Tarjetas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO:</b>\n"
            "Partido muy cerrado de ritmo lento. Ambos equipos priorizan el bloque defensivo bajo y minimizan riesgos en la construcción."
        )
    },
    {
        "code": "ARG-EST-SLO",
        "text": (
            "🇦🇷 <b>ARGENTINA - LIGA PROFESIONAL</b>\n"
            "⏰ <b>23:00 CEST</b> | ⚔️ <b>Estudiantes de La Plata vs San Lorenzo</b>\n\n"
            "📊 <b>CÓDIGO DE SEGUIMIENTO:</b> <code>ARG-EST-SLO</code>\n\n"
            "• ⚽ <b>xG Proyectado:</b> 1.65 vs 0.80 | Over 1.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Estudiantes de La Plata [Cuota 2.01]\n"
            "• 🚩 <b>Córners:</b> Over 8.5 Córners\n"
            "• 🟨 <b>Tarjetas:</b> Over 5.5 Tarjetas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO:</b>\n"
            "Estudiantes en su estadio impone una presión asfixiante sobre los centrales rivales. San Lorenzo sufre en salidas lejanas."
        )
    },
    {
        "code": "BRA-BAH-FLA",
        "text": (
            "🇧🇷 <b>BRASIL - SERIE A</b>\n"
            "⏰ <b>23:30 CEST</b> | ⚔️ <b>Bahia vs Flamengo</b>\n\n"
            "📊 <b>CÓDIGO DE SEGUIMIENTO:</b> <code>BRA-BAH-FLA</code>\n\n"
            "• ⚽ <b>xG Proyectado:</b> 1.15 vs 1.95 | Over 2.0 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Flamengo Directa [Cuota 1.96]\n"
            "• 🚩 <b>Córners:</b> Over 9.5 Córners\n"
            "• 🟨 <b>Tarjetas:</b> Over 4.5 Tarjetas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO:</b>\n"
            "Flamengo llega con plantilla completa y un potencial ofensivo superior. Bahia suele ceder desajustes defensivos en salida."
        )
    },
    {
        "code": "BRA-REM-BRAG",
        "text": (
            "🇧🇷 <b>BRASIL - SERIE A</b>\n"
            "⏰ <b>00:30 CEST</b> | ⚔️ <b>Clube do Remo vs Red Bull Bragantino</b>\n\n"
            "📊 <b>CÓDIGO DE SEGUIMIENTO:</b> <code>BRA-REM-BRAG</code>\n\n"
            "• ⚽ <b>xG Proyectado:</b> 0.90 vs 1.85 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Red Bull Bragantino HA 0.0 [Cuota 1.55]\n"
            "• 🚩 <b>Córners:</b> Over 10.5 Córners\n"
            "• 🟨 <b>Tarjetas:</b> Over 4.0 Tarjetas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO:</b>\n"
            "Bragantino despliega transiciones muy rápidas por las bandas. Clube do Remo sufrirá ante el ritmo intenso en la medular."
        )
    }
]

# ---------------------------------------------------------
# Tarea de Publicación Automática
# ---------------------------------------------------------
async def publish_picks(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    logging.info("Enviando picks de Argentina y Brasil...")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 UNIRSE AL VIP / CONTACTO DIRECTO", url="https://t.me/Mark122")]
    ])

    for match in MATCH_PICKS:
        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=match["text"],
                parse_mode="HTML",
                reply_markup=keyboard
            )
            logging.info(f"Publicado pick: {match['code']}")
            time.sleep(3)
        except Exception as e:
            logging.error(f"Error enviando {match['code']}: {e}")

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
        job_queue.run_once(publish_picks, when=5)

    application.add_handler(CommandHandler
