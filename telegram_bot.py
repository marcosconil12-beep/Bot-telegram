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

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8665484015:AAF1zLm4wuAItvQiqI2K-dmmyFn1hjzNUOk")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@FreeTopTip")

SPAIN_TZ = ZoneInfo("Europe/Madrid")

# ---------------------------------------------------------
# Publicaciones de Análisis por Partido (Japón)
# ---------------------------------------------------------
MATCH_POSTS = [
    {
        "code": "JPN-FAG-MIT",
        "text": (
            "🇯🇵 <b>JAPÓN: Fagiano Okayama vs Mito Hollyhock</b> (12:00 CEST)\n\n"
            "📌 <b>Código Pick:</b> <code>JPN-FAG-MIT</code>\n"
            "⚽ <b>Partido:</b> Fagiano Okayama vs Mito Hollyhock\n"
            "⏰ <b>Hora:</b> 12:00 CEST\n\n"
            "🧠 <b>ANÁLISIS TÁCTICO Y MÉTRICO:</b>\n"
            "El Fagiano Okayama mantendrá la iniciativa atacando por bandas. Mito Hollyhock replegará en bloque bajo buscando frenar con faltas el juego directo local.\n\n"
            "📊 <b>MERCADOS SECUNDARIOS DEL PARTIDO:</b>\n"
            "🚩 <b>Córners:</b> Más de 8.5 Córners Totales\n"
            "🧤 <b>Paradas:</b> Portero Mito Hollyhock: Más de 3.5 Paradas\n"
            "🟨 <b>Tarjetas:</b> Más de 3.5 Tarjetas Totales\n"
            "🎯 <b>Remates a Puerta:</b> Fagiano: Más de 4.5 Remates a puerta\n\n"
            "🎯 <b>PRONÓSTICO PRINCIPAL:</b> Victoria Fagiano Okayama\n"
            "💰 <b>Cuota:</b> 1.71 (Bet365)\n"
            "📊 <b>Stake Sugerido:</b> 1.5/10"
        )
    },
    {
        "code": "JPN-TOK-KAS",
        "text": (
            "🇯🇵 <b>JAPÓN: FC Tokyo vs Kashiwa Reysol</b> (12:00 CEST)\n\n"
            "📌 <b>Código Pick:</b> <code>JPN-TOK-KAS</code>\n"
            "⚽ <b>Partido:</b> FC Tokyo vs Kashiwa Reysol\n"
            "⏰ <b>Hora:</b> 12:00 CEST\n\n"
            "🧠 <b>ANÁLISIS TÁCTICO Y MÉTRICO:</b>\n"
            "Partido abierto con transiciones rápidas de área a área. La fragilidad defensiva en los centros provocará muchas intervenciones de ambos guardametas.\n\n"
            "📊 <b>MERCADOS SECUNDARIOS DEL PARTIDO:</b>\n"
            "🚩 <b>Córners:</b> Más de 9.5 Córners Totales\n"
            "🧤 <b>Paradas:</b> Ambos Porteros: Más de 2.5 Paradas c/u\n"
            "🟨 <b>Tarjetas:</b> Más de 4.5 Tarjetas Totales\n"
            "🎯 <b>Remates a Puerta:</b> Más de 8.5 Remates a puerta totales\n\n"
            "🎯 <b>PRONÓSTICO PRINCIPAL:</b> Ambos Equipos Anotan (Sí)\n"
            "💰 <b>Cuota:</b> 1.70 (Bet365)\n"
            "📊 <b>Stake Sugerido:</b> 1.5/10"
        )
    },
    {
        "code": "JPN-KAW-VIS",
        "text": (
            "🇯🇵 <b>JAPÓN: Kawasaki Frontale vs Vissel Kobe</b> (12:00 CEST)\n\n"
            "📌 <b>Código Pick:</b> <code>JPN-KAW-VIS</code>\n"
            "⚽ <b>Partido:</b> Kawasaki Frontale vs Vissel Kobe\n"
            "⏰ <b>Hora:</b> 12:00 CEST\n\n"
            "🧠 <b>ANÁLISIS TÁCTICO Y MÉTRICO:</b>\n"
            "Choque de trenes con altísima intensidad física y volumen de disparos elevado desde fuera y dentro del área.\n\n"
            "📊 <b>MERCADOS SECUNDARIOS DEL PARTIDO:</b>\n"
            "🚩 <b>Córners:</b> Más de 10.5 Córners Totales\n"
            "🧤 <b>Paradas:</b> Portero Kawasaki: Más de 3.5 Paradas\n"
            "🟨 <b>Tarjetas:</b> Más de 4.5 Tarjetas Totales\n"
            "🎯 <b>Remates a Puerta:</b> Más de 9.5 Remates a puerta totales\n\n"
            "🎯 <b>PRONÓSTICO PRINCIPAL:</b> Más de 2.5 Goles\n"
            "💰 <b>Cuota:</b> 1.75 (Bet365)\n"
            "📊 <b>Stake Sugerido:</b> 1.5/10"
        )
    },
    {
        "code": "JPN-KYO-KAS",
        "text": (
            "🇯🇵 <b>JAPÓN: Kyoto Sanga FC vs Kashima Antlers</b> (12:00 CEST)\n\n"
            "📌 <b>Código Pick:</b> <code>JPN-KYO-KAS</code>\n"
            "⚽ <b>Partido:</b> Kyoto Sanga FC vs Kashima Antlers\n"
            "⏰ <b>Hora:</b> 12:00 CEST\n\n"
            "🧠 <b>ANÁLISIS TÁCTICO Y MÉTRICO:</b>\n"
            "Kashima volcará el juego en campo rival. Kyoto sufrirá en las marcas individuales acumulando faltas y amonestaciones.\n\n"
            "📊 <b>MERCADOS SECUNDARIOS DEL PARTIDO:</b>\n"
            "🚩 <b>Córners:</b> Más de 9.5 Córners Totales\n"
            "🧤 <b>Paradas:</b> Portero Kyoto Sanga: Más de 4.5 Paradas\n"
            "🟨 <b>Tarjetas:</b> Kyoto Sanga: Más de 2.5 Tarjetas\n"
            "🎯 <b>Remates a Puerta:</b> Kashima: Más de 4.5 Remates a puerta\n\n"
            "🎯 <b>PRONÓSTICO PRINCIPAL:</b> Victoria Kashima Antlers\n"
            "💰 <b>Cuota:</b> 1.91 (Bet365)\n"
            "📊 <b>Stake Sugerido:</b> 1.5/10"
        )
    },
    {
        "code": "JPN-NAG-CER",
        "text": (
            "🇯🇵 <b>JAPÓN: Nagoya Grampus vs Cerezo Osaka</b> (12:00 CEST)\n\n"
            "📌 <b>Código Pick:</b> <code>JPN-NAG-CER</code>\n"
            "⚽ <b>Partido:</b> Nagoya Grampus vs Cerezo Osaka\n"
            "⏰ <b>Hora:</b> 12:00 CEST\n\n"
            "🧠 <b>ANÁLISIS TÁCTICO Y MÉTRICO:</b>\n"
            "Planteamiento táctico muy rocoso de Nagoya. Dominio del juego aéreo en el área con pocos espacios interiores.\n\n"
            "📊 <b>MERCADOS SECUNDARIOS DEL PARTIDO:</b>\n"
            "🚩 <b>Córners:</b> Más de 8.5 Córners Totales\n"
            "🧤 <b>Paradas:</b> Portero Cerezo Osaka: Más de 3.5 Paradas\n"
            "🟨 <b>Tarjetas:</b> Más de 3.5 Tarjetas Totales\n"
            "🎯 <b>Remates a Puerta:</b> Nagoya: Más de 3.5 Remates a puerta\n\n"
            "🎯 <b>PRONÓSTICO PRINCIPAL:</b> Nagoya Grampus - Empate No Válido (DNB)\n"
            "💰 <b>Cuota:</b> 1.57 (Bet365)\n"
            "📊 <b>Stake Sugerido:</b> 2/10"
        )
    },
    {
        "code": "JPN-SHI-MAC",
        "text": (
            "🇯🇵 <b>JAPÓN: Shimizu S-Pulse vs Machida Zelvia</b> (12:00 CEST)\n\n"
            "📌 <b>Código Pick:</b> <code>JPN-SHI-MAC</code>\n"
            "⚽ <b>Partido:</b> Shimizu S-Pulse vs Machida Zelvia\n"
            "⏰ <b>Hora:</b> 12:00 CEST\n\n"
            "🧠 <b>ANÁLISIS TÁCTICO Y MÉTRICO:</b>\n"
            "Machida castigará al contragolpe. El empuje de Shimizu generará muchos saques de esquina pero también concesiones defensivas.\n\n"
            "📊 <b>MERCADOS SECUNDARIOS DEL PARTIDO:</b>\n"
            "🚩 <b>Córners:</b> Más de 9.5 Córners Totales\n"
            "🧤 <b>Paradas:</b> Portero Machida Zelvia: Más de 3.5 Paradas\n"
            "🟨 <b>Tarjetas:</b> Más de 4.5 Tarjetas Totales\n"
            "🎯 <b>Remates a Puerta:</b> Ambos: Más de 3.5 Remates a puerta c/u\n\n"
            "🎯 <b>PRONÓSTICO PRINCIPAL:</b> Victoria Machida Zelvia\n"
            "💰 <b>Cuota:</b> 2.05 (Bet365)\n"
            "📊 <b>Stake Sugerido:</b> 1/10"
        )
    },
    {
        "code": "JPN-NAG-SAN",
        "text": (
            "🇯🇵 <b>JAPÓN: V-Varen Nagasaki vs Sanfrecce Hiroshima</b> (12:00 CEST)\n\n"
            "📌 <b>Código Pick:</b> <code>JPN-NAG-SAN</code>\n"
            "⚽ <b>Partido:</b> V-Varen Nagasaki vs Sanfrecce Hiroshima\n"
            "⏰ <b>Hora:</b> 12:00 CEST\n\n"
            "🧠 <b>ANÁLISIS TÁCTICO Y MÉTRICO:</b>\n"
            "Monopolio absoluto de la pelota por parte de Sanfrecce Hiroshima, exigiendo constantemente al meta rival bajo palos.\n\n"
            "📊 <b>MERCADOS SECUNDARIOS DEL PARTIDO:</b>\n"
            "🚩 <b>Córners:</b> Sanfrecce Hiroshima: Más de 5.5 Córners\n"
            "🧤 <b>Paradas:</b> Portero V-Varen Nagasaki: Más de 4.5 Paradas\n"
            "🟨 <b>Tarjetas:</b> V-Varen Nagasaki: Más de 2.5 Tarjetas\n"
            "🎯 <b>Remates a Puerta:</b> Sanfrecce: Más de 5.5 Remates a puerta\n\n"
            "🎯 <b>PRONÓSTICO PRINCIPAL:</b> Sanfrecce Hiroshima HA -1.0\n"
            "💰 <b>Cuota:</b> 1.65 (Bet365)\n"
            "📊 <b>Stake Sugerido:</b> 1.5/10"
        )
    },
    {
        "code": "JPN-YOK-VER",
        "text": (
            "🇯🇵 <b>JAPÓN: Yokohama F-Marinos vs Tokyo Verdy</b> (12:00 CEST)\n\n"
            "📌 <b>Código Pick:</b> <code>JPN-YOK-VER</code>\n"
            "⚽ <b>Partido:</b> Yokohama F-Marinos vs Tokyo Verdy\n"
            "⏰ <b>Hora:</b> 12:00 CEST\n\n"
            "🧠 <b>ANÁLISIS TÁCTICO Y MÉTRICO:</b>\n"
            "Asedio continuo de los Marinos por los costados con centros laterales bloqueados y constante flujo de disparos a puerta.\n\n"
            "📊 <b>MERCADOS SECUNDARIOS DEL PARTIDO:</b>\n"
            "🚩 <b>Córners:</b> Yokohama F-Marinos: Más de 6.5 Córners\n"
            "🧤 <b>Paradas:</b> Portero Tokyo Verdy: Más de 4.5 Paradas\n"
            "🟨 <b>Tarjetas:</b> Más de 3.5 Tarjetas Totales\n"
            "🎯 <b>Remates a Puerta:</b> Yokohama: Más de 5.5 Remates a puerta\n\n"
            "🎯 <b>PRONÓSTICO PRINCIPAL:</b> Victoria Yokohama F-Marinos\n"
            "💰 <b>Cuota:</b> 1.81 (Bet365)\n"
            "📊 <b>Stake Sugerido:</b> 1.5/10"
        )
    },
    {
        "code": "JPN-URA-JEF",
        "text": (
            "🇯🇵 <b>JAPÓN: Urawa Red Diamonds vs JEF Utd Chiba</b> (12:30 CEST)\n\n"
            "📌 <b>Código Pick:</b> <code>JPN-URA-JEF</code>\n"
            "⚽ <b>Partido:</b> Urawa Red Diamonds vs JEF Utd Chiba\n"
            "⏰ <b>Hora:</b> 12:30 CEST\n\n"
            "🧠 <b>ANÁLISIS TÁCTICO Y MÉTRICO:</b>\n"
            "Urawa encerrará a Chiba en su área. El desgaste defensivo visitante provocará cortes tácticos y faltas reiteradas.\n\n"
            "📊 <b>MERCADOS SECUNDARIOS DEL PARTIDO:</b>\n"
            "🚩 <b>Córners:</b> Más de 9.5 Córners Totales\n"
            "🧤 <b>Paradas:</b> Portero JEF Utd Chiba: Más de 4.5 Paradas\n"
            "🟨 <b>Tarjetas:</b> JEF Utd Chiba: Más de 2.5 Tarjetas\n"
            "🎯 <b>Remates a Puerta:</b> Urawa: Más de 5.5 Remates a puerta\n\n"
            "🎯 <b>PRONÓSTICO PRINCIPAL:</b> Victoria Urawa Red Diamonds\n"
            "💰 <b>Cuota:</b> 1.62 (Bet365)\n"
            "📊 <b>Stake Sugerido:</b> 2/10"
        )
    }
]

# ---------------------------------------------------------
# Tarea de Publicación Automática
# ---------------------------------------------------------
async def publish_all_picks(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    logging.info("Iniciando envío de picks para la jornada japonesa con el bot nuevo...")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 UNIRSE AL VIP POR 9,99€ (CLICK AQUÍ)", url="https://t.me/Mark122")]
    ])

    for post in MATCH_POSTS:
        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=post["text"],
                parse_mode="HTML",
                reply_markup=keyboard
            )
            logging.info(f"Publicado pick: {post['code']}")
            time.sleep(2)
        except Exception as e:
            logging.error(f"Error al enviar {post['code']}: {e}")

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
        application.job_queue.run_once(publish_all_picks, when=5)

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("vip", start_command))

    logging.info("Bot activo...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
