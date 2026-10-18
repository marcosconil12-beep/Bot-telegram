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
# Lista de Pronósticos con Análisis Completo Extenso
# ---------------------------------------------------------
MATCH_PICKS = [
    {
        "code": "ARG-ESTRC-ALD",
        "text": (
            "🇦🇷 <b>ARGENTINA - LIGA PROFESIONAL</b>\n"
            "⏰ <b>Hora:</b> 23:00 CEST | ⚔️ <b>Estudiantes Río Cuarto vs Aldosivi</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 1.10 vs 1.05 | Menos de 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Estudiantes Río Cuarto HA 0.0 (Cuota 1.90)\n"
            "• 🚩 <b>Córners totales:</b> Under 9.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Estudiantes R.C. (3.8) vs Aldosivi (3.2)\n"
            "• 🧤 <b>Paradas Porteros:</b> Over 2.5 Paradas cada uno\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Nos encontramos ante un choque típicamente trabado del fútbol argentino donde primará el orden táctico sobre la fluidez de juego. Ambos entrenadores plantean bloques muy consolidados sin arriesgar en la salida de balón. Las métricas nos señalan un partido de muy pocas ocasiones claras, por lo que cubrimos el empate con la línea asiática a favor de los locales en su feudo.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Estudiantes Río Cuarto HA 0.0 (Apuesta Sin Empate)\n"
            "🎲 <b>Índice de Confianza:</b> 86%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "code": "ARG-EST-SLO",
        "text": (
            "🇦🇷 <b>ARGENTINA - LIGA PROFESIONAL</b>\n"
            "⏰ <b>Hora:</b> 23:00 CEST | ⚔️ <b>Estudiantes de La Plata vs San Lorenzo</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 1.65 vs 0.80 | Over 1.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Estudiantes de La Plata (Cuota 2.01)\n"
            "• 🚩 <b>Córners totales:</b> Over 8.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 5.5 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Estudiantes L.P. (5.2) vs San Lorenzo (2.9)\n"
            "• 🧤 <b>Paradas Portero San Lorenzo:</b> Over 3.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Estudiantes en el Estadio UNO imprime un ritmo sumamente intenso en los primeros 45 minutos, ahogando la salida de pelota de sus rivales. San Lorenzo sufre en desplazamientos lejanos para sostener la posesión en la medular. La cuota por encima de 2.00 para el triunfo del conjunto pincharrata tiene un valor métrico excepcional.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Victoria Estudiantes de La Plata Directa (2.01)\n"
            "🎲 <b>Índice de Confianza:</b> 88%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "code": "BRA-BAH-FLA",
        "text": (
            "🇧🇷 <b>BRASIL - SERIE A</b>\n"
            "⏰ <b>Hora:</b> 23:30 CEST | ⚔️ <b>Bahia vs Flamengo</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 1.15 vs 1.95 | Over 2.0 Goles Totales\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Flamengo Directa (Cuota 1.96)\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Bahia (3.9) vs Flamengo (6.1)\n"
            "• 🧤 <b>Paradas Portero Bahia:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El Flamengo llega en plena dinámica ascendente en el Brasileirão con un caudal ofensivo muy superior. Bahia suele conceder desajustes en el perfil defensivo cuando le ejercen presión alta. Esperamos un dominio claro del Mengão que termine imponiendo su calidad individual arriba.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Victoria Flamengo Directa (1.96)\n"
            "🎲 <b>Índice de Confianza:</b> 89%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "code": "BRA-REM-BRAG",
        "text": (
            "🇧🇷 <b>BRASIL - SERIE A</b>\n"
            "⏰ <b>Hora:</b> 00:30 CEST | ⚔️ <b>Clube do Remo vs Red Bull Bragantino</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 0.90 vs 1.85 | Over 2.5 Goles Totales\n"
            "• 🏆 <b>Pick Resultado:</b> Red Bull Bragantino HA 0.0 (Cuota 1.55)\n"
            "• 🚩 <b>Córners totales:</b> Over 10.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.0 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Clube do Remo (3.1) vs Bragantino (5.8)\n"
            "• 🧤 <b>Paradas Portero Remo:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El proyecto de Bragantino destaca por la velocidad en sus bandas y transiciones vertiginosas. Clube do Remo sufrirá para sostener la embestida visitante cuando el choque se abra en la segunda parte. La línea sin empate nos protege totalmente ante una posible igualdad.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Red Bull Bragantino HA 0.0 (Apuesta Sin Empate)\n"
            "🎲 <b>Índice de Confianza:</b> 87%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    }
]

# ---------------------------------------------------------
# Función de Envío Al Canal
# ---------------------------------------------------------
async def publish_picks(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    logging.info("Enviando publicaciones completas...")

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
            logging.info(f"Publicado: {match['code']}")
            time.sleep(3)
        except Exception as e:
            logging.error(f"Error publicando {match['code']}: {e}")

# ---------------------------------------------------------
# Función Start
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
# Ejecución Principal
# ---------------------------------------------------------
def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    if application.job_queue:
        application.job_queue.run_once(publish_picks, when=5)

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("vip", start_command))

    logging.info("Bot activo...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
