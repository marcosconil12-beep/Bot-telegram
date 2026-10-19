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
# Pronósticos de los Partidos Seleccionados
# ---------------------------------------------------------
MATCH_PICKS = [
    {
        "code": "TUR-TRAB-BESIK",
        "text": (
            "🇹🇷 <b>TURQUÍA - SUPER LIG</b>\n"
            "⏰ <b>Hora:</b> 19:00 CEST | ⚔️ <b>Trabzonspor vs Besiktas</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 1.45 vs 1.50 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Ambos Equipos Anotan (BTTS) [Cuota 1.66]\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 5.5 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Trabzonspor (4.5) vs Besiktas (4.8)\n"
            "• 🧤 <b>Paradas Porteros:</b> Over 3.5 Paradas cada uno\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Partidazo en Papara Park entre dos gigantes turcos que no especulan. Trabzonspor se fortalece como local proponiendo ataques verticales directos, mientras que Besiktas llega con un bloque ofensivo muy dinámico en transición. Ambas defensas suelen conceder ocasiones claras en balones divididos.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Ambos Equipos Anotan (BTTS)\n"
            "🎲 <b>Índice de Confianza:</b> 88%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "code": "ITA-MON-CAG",
        "text": (
            "🇮🇹 <b>ITALIA - SERIE A</b>\n"
            "⏰ <b>Hora:</b> 18:30 CEST | ⚔️ <b>Monza vs Cagliari</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 1.30 vs 1.05 | Under 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Monza HA 0.0 (Apuesta Sin Empate) [Cuota 1.62]\n"
            "• 🚩 <b>Córners totales:</b> Under 9.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Monza (4.1) vs Cagliari (3.2)\n"
            "• 🧤 <b>Paradas Portero Cagliari:</b> Over 3.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Monza busca hacerse fuerte ante un Cagliari que sufre bastante para sostener la posesión en desplazamientos lejanos. Los locales dominan el ritmo en la medular y conceden muy poco en juego aéreo. La opción del hándicap asiático nulo nos protege plenamente en caso de igualdad.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Monza HA 0.0 (Apuesta Sin Empate)\n"
            "🎲 <b>Índice de Confianza:</b> 86%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "code": "ITA-PAR-TOR",
        "text": (
            "🇮🇹 <b>ITALIA - SERIE A</b>\n"
            "⏰ <b>Hora:</b> 20:45 CEST | ⚔️ <b>Parma vs Torino</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 1.20 vs 1.40 | Over 2.0 Goles Totales\n"
            "• 🏆 <b>Pick Resultado:</b> Torino HA 0.0 (Apuesta Sin Empate) [Cuota 1.70 / Directo 2.40]\n"
            "• 🚩 <b>Córners totales:</b> Over 8.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Parma (3.6) vs Torino (4.5)\n"
            "• 🧤 <b>Paradas Portero Parma:</b> Over 3.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Torino se muestra como un conjunto tácticamente muy bien estructurado sin balón, capaz de asfixiar las bandas del Parma. El conjunto local tiende a dejar desajustes defensivos cuando adelanta sus líneas, algo que Torino sabrá explotar con sus delanteros centro.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Torino HA 0.0 (Apuesta Sin Empate)\n"
            "🎲 <b>Índice de Confianza:</b> 87%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "code": "POR-BRA-GIL",
        "text": (
            "🇵🇹 <b>PORTUGAL - PRIMEIRA LIGA</b>\n"
            "⏰ <b>Hora:</b> 21:15 CEST | ⚔️ <b>Braga vs Gil Vicente</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 2.10 vs 0.75 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Braga Directa [Cuota 1.53]\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.0 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Braga (6.4) vs Gil Vicente (2.8)\n"
            "• 🧤 <b>Paradas Portero Gil Vicente:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Braga cuenta con un potencial ofensivo netamente superior en su feudo, imprimiendo una presión muy alta desde el silbato inicial. Gil Vicente sufrirá encerrado en su propia área frente a la llegada constante por bandas del cuadro local.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Victoria Braga Directa (1.53)\n"
            "🎲 <b>Índice de Confianza:</b> 90%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "code": "ENG-TOT-COV",
        "text": (
            "🏴󠁧󠁢󠁥󠁮󠁧󠁿 <b>INGLATERRA - PREMIER LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 21:00 CEST | ⚔️ <b>Tottenham vs Coventry</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 2.40 vs 0.80 | Over 2.5 / Over 3.0 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Tottenham + Over 1.5 Goles [Cuota 1.53]\n"
            "• 🚩 <b>Córners totales:</b> Over 10.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 3.5 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Tottenham (7.1) vs Coventry (2.9)\n"
            "• 🧤 <b>Paradas Portero Coventry:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Tottenham despliega un bloque de ataque total con posesiones prolongadas e incursiones constantes por los costados. Coventry sufrirá un desgaste físico abrumador defendiendo en campo propio. Esperamos una victoria clara y holgada de los Spurs.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Victoria Tottenham Directa (1.53)\n"
            "🎲 <b>Índice de Confianza:</b> 91%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "code": "ESP-GET-RAY",
        "text": (
            "🇪🇸 <b>ESPAÑA - LALIGA EA SPORTS</b>\n"
            "⏰ <b>Hora:</b> 21:00 CEST | ⚔️ <b>Getafe vs Rayo Vallecano</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 1.05 vs 0.95 | Under 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Empate o Rayo Vallecano (HA 0.0) [Cuota 1.85 / Directo 2.60]\n"
            "• 🚩 <b>Córners totales:</b> Under 9.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 5.5 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Getafe (3.2) vs Rayo Vallecano (3.5)\n"
            "• 🧤 <b>Paradas Porteros:</b> Over 2.5 Paradas cada uno\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Derbi del sur de Madrid caracterizado por la intensidad física, juego directo y constantes faltas. Getafe propone un bloque rocoso que concede muy poco espacio, mientras que el Rayo busca transiciones veloces. La igualdad es máxima, por lo que respaldar la cobertura del Rayo en hándicap ofrece un valor excelente.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Rayo Vallecano HA 0.0 (Apuesta Sin Empate)\n"
            "🎲 <b>Índice de Confianza:</b> 86%\n\n"
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
