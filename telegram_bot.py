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
# Mensaje Promocional del Pick VIP (Tercera RFEF Grupo 10)
# ---------------------------------------------------------
PAID_PICK_PROMO_TEXT = (
    "🔥 <b>STAKE MÁXIMO DEFINIDO: TERCERA RFEF - GRUPO 10</b> 🔥\n\n"
    "Familia, he detectado una <b>INFORMACIÓN DE VALOR ABSOLUTO</b> en nuestro mercado estrella: el Grupo 10 de Tercera Federación.\n\n"
    "Cuando la información local supera a las cuotas de las casas de apuestas, no se puede dejar pasar. Tengo analizado al milímetro un partido con un contexto táctico y condicionantes únicos donde la victoria/línea no debería estar, bajo ningún concepto, por encima de 1.50.\n\n"
    "💎 <b>DETALLES DEL PICK VIP:</b>\n"
    "• 🏆 <b>Competición:</b> Tercera RFEF (Grupo 10)\n"
    "• 📊 <b>Cuota:</b> <b>@2.00+ (¡DOBLAMOS INVERSIÓN!)</b>\n"
    "• 🎯 <b>Fiabilidad / Confianza:</b> <b>95%</b>\n"
    "• 💰 <b>Precio de acceso:</b> <b>Solo 9,99€</b>\n\n"
    "💡 <b>¿POR QUÉ ENTRAR HOY?</b>\n"
    "1. <b>Información privilegiada de plantilla:</b> Sanciones, bajas de última hora y rotaciones clave en uno de los conjuntos.\n"
    "2. <b>Desajuste de cuota:</b> Bet365 y las principales bookies han colocado una línea inflada por guiarse solo por la clasificación general.\n"
    "3. <b>Rentabilidad garantizada:</b> Buscamos doblar la banca con una sola apuesta de altísimo valor.\n\n"
    "🔒 <i>CUPOS LIMITADOS (Para no desplomar la cuota antes de tiempo)</i>\n\n"
    "📲 <b>¡Consigue tu pase ahora por solo 9,99€!</b>\n"
    "Pulsa en el botón de abajo para escribirme por privado y recibir la selección de inmediato."
)

# ---------------------------------------------------------
# Tarea de Publicación Automática
# ---------------------------------------------------------
async def publish_paid_pick_promo(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    logging.info("Enviando mensaje promocional del Pick VIP del Grupo 10...")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 COMPRAR PICK VIP (9,99€)", url="https://t.me/Mark122")]
    ])

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=PAID_PICK_PROMO_TEXT,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        logging.info("Mensaje promocional del Pick VIP publicado con éxito.")
    except Exception as e:
        logging.error(f"Error enviando la promoción: {e}")

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
            "Para adquirir el Pick VIP por 9,99€ o consultar cualquier duda, pulsa el botón de abajo para hablar conmigo directamente.",
            parse_mode="HTML",
            reply_markup=keyboard
        )

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    job_queue = application.job_queue
    if job_queue:
        # Publica el mensaje promocional 5 segundos después de arrancar el bot
        job_queue.run_once(publish_paid_pick_promo, when=5)

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("vip", start_command))

    logging.info("Bot en marcha. Programado para enviar la oferta del Pick VIP...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
