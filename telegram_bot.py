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
# Lista de Pronósticos UEFA Champions League
# ---------------------------------------------------------
MATCH_PICKS = [
    {
        "code": "UCL-FEN-SLA",
        "text": (
            "🇪🇺 <b>UEFA CHAMPIONS LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 18:45 CEST | ⚔️ <b>Fenerbahçe vs Slavia Praga</b>\n\n"
            "📊 <b>CÓDIGO DE SEGUIMIENTO:</b> <code>UCL-FEN-SLA</code>\n\n"
            "• ⚽ <b>xG Proyectado:</b> 1.80 vs 0.95 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Fenerbahçe Directa [Cuota 1.61]\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Fenerbahçe (5.8) vs Slavia Praga (3.1)\n"
            "• 🧤 <b>Paradas Portero Slavia:</b> Over 3.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El ambiente en Estambul será un factor determinante desde el minuto uno. El Fenerbahçe en su feudo impone un ritmo de juego altísimo con presión asfixiante sobre la salida rival. El Slavia Praga sufre enormemente cuando no logra tener posesiones largas para respirar. Con la cuota 1.61, la victoria local tiene un valor métrico claro."
        )
    },
    {
        "code": "UCL-SAB-DOR",
        "text": (
            "🇪🇺 <b>UEFA CHAMPIONS LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 18:45 CEST | ⚔️ <b>Sabah FK vs Borussia Dortmund</b>\n\n"
            "📊 <b>CÓDIGO DE SEGUIMIENTO:</b> <code>UCL-SAB-DOR</code>\n\n"
            "• ⚽ <b>xG Proyectado:</b> 0.50 vs 2.65 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Borussia Dortmund HA -1.5 [Cuota 1.75]\n"
            "• 🚩 <b>Córners totales:</b> Over 8.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Under 4.0 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Sabah (2.1) vs Dortmund (7.2)\n"
            "• 🧤 <b>Paradas Portero Sabah:</b> Over 5.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Diferencia de plantilla abismal. El Dortmund desplegará su potencial ofensivo buscando resolver el encuentro por la vía rápida para evitar complicaciones a domicilio. Sabah se replegará en bloque bajo pero concederá múltiples ocasiones claras. Entramos al hándicap asiático buscando un triunfo por dos o más goles de diferencia."
        )
    },
    {
        "code": "UCL-LIV-VIL",
        "text": (
            "🇪🇺 <b>UEFA CHAMPIONS LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 21:00 CEST | ⚔️ <b>Liverpool vs Villarreal</b>\n\n"
            "📊 <b>CÓDIGO DE SEGUIMIENTO:</b> <code>UCL-LIV-VIL</code>\n\n"
            "• ⚽ <b>xG Proyectado:</b> 2.25 vs 1.05 | Over 2.5 / Over 3.0 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Liverpool + Over 1.5 Goles [Cuota 1.72]\n"
            "• 🚩 <b>Córners totales:</b> Over 10.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 3.5 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Liverpool (6.9) vs Villarreal (3.4)\n"
            "• 🧤 <b>Paradas Portero Villarreal:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Anfield en noches europeas no perdona. El Liverpool saldrá a volcarse por las bandas explotando la velocidad de sus extremos. El Villarreal intentará pausar el partido a través de la posesión, pero sufrirá ante la presión tras pérdida de los 'Reds'. La victoria local combinada con goles ofrece el mejor equilibrio riesgo/beneficio."
        )
    },
    {
        "code": "UCL-MCI-AEK",
        "text": (
            "🇪🇺 <b>UEFA CHAMPIONS LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 21:00 CEST | ⚔️ <b>Manchester City vs AEK Atenas</b>\n\n"
            "📊 <b>CÓDIGO DE SEGUIMIENTO:</b> <code>UCL-MCI-AEK</code>\n\n"
            "• ⚽ <b>xG Proyectado:</b> 3.10 vs 0.40 | Over 3.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Manchester City HA -2.5 [Cuota 1.85]\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners Totales (Mayoría City)\n"
            "• 🟨 <b>Tarjetas totales:</b> Under 3.5 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Man City (8.5) vs AEK Atenas (1.8)\n"
            "• 🧤 <b>Paradas Portero AEK:</b> Over 5.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Monólogo total del Manchester City en el Etihad Stadium. Los de Guardiola encerrarán al conjunto griego en su propio balcón del área durante los 90 minutos. El volumen de centros y disparos lejanos será masivo. Buscamos una goleada abultada del equipo ciudadano."
        )
    },
    {
        "code": "UCL-NAP-BOD",
        "text": (
            "🇪🇺 <b>UEFA CHAMPIONS LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 21:00 CEST | ⚔️ <b>Nápoles vs Bodo/Glimt</b>\n\n"
            "📊 <b>CÓDIGO DE SEGUIMIENTO:</b> <code>UCL-NAP-BOD</code>\n\n"
            "• ⚽ <b>xG Proyectado:</b> 2.05 vs 0.85 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Nápoles Directa [Cuota 1.61]\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.0 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Nápoles (6.1) vs Bodo/Glimt (2.9)\n"
            "• 🧤 <b>Paradas Portero Bodo:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El Bodo/Glimt fuera de su césped artificial pierde drásticamente su competitividad europea. El Nápoles en el Diego Armando Maradona impondrá una intensidad física inasumible para el conjunto noruego. A cuota 1.61, el triunfo napolitano es una de las apuestas más sólidas del bloque."
        )
    },
    {
        "code": "UCL-OPO-PSV",
        "text": (
            "🇪🇺 <b>UEFA CHAMPIONS LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 21:00 CEST | ⚔️ <b>Oporto vs PSV Eindhoven</b>\n\n"
            "📊 <b>CÓDIGO DE SEGUIMIENTO:</b> <code>UCL-OPO-PSV</code>\n\n"
            "• ⚽ <b>xG Proyectado:</b> 1.70 vs 1.35 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Ambos Equipos Anotan (BTTS) [Cuota 1.65]\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Oporto (5.1) vs PSV (4.6)\n"
            "• 🧤 <b>Paradas Porteros:</b> Over 3.5 Paradas cada uno\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Encuentro sumamente abierto en el Estádio do Dragão. El Oporto ataca con ímpetu apoyado por su afición pero deja desajustes a la espalda de sus centrales. Por su parte, el PSV mantiene una propuesta súper vertical que genera gol con relativa facilidad pero concede atrás."
        )
    },
    {
        "code": "UCL-PSG-BAR",
        "text": (
            "🇪🇺 <b>UEFA CHAMPIONS LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 21:00 CEST | ⚔️ <b>PSG vs Barcelona</b>\n\n"
            "📊 <b>CÓDIGO DE SEGUIMIENTO:</b> <code>UCL-PSG-BAR</code>\n\n"
            "• ⚽ <b>xG Proyectado:</b> 1.85 vs 1.80 | Over 2.5 / Over 3.0 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Ambos Equipos Anotan + Over 2.5 Goles [Cuota 1.70]\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 5.0 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> PSG (5.5) vs Barcelona (5.3)\n"
            "• 🧤 <b>Paradas Porteros:</b> Over 3.5 Paradas cada guardameta\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El gran choque de la jornada europea en el Parque de los Príncipes. Cuotas 100% igualadas a 2.45 en el mercado 1X2. Ambos entrenadores apuestan por presionar arriba y tirar la línea defensiva muy adelantada. Veremos un intercambio constante de golpes donde el gol en ambas porterías está asegurado."
        )
    },
    {
        "code": "UCL-ROM-SLO",
        "text": (
            "🇪🇺 <b>UEFA CHAMPIONS LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 21:00 CEST | ⚔️ <b>Roma vs Slovan Bratislava</b>\n\n"
            "📊 <b>CÓDIGO DE SEGUIMIENTO:</b> <code>UCL-ROM-SLO</code>\n\n"
            "• ⚽ <b>xG Proyectado:</b> 2.70 vs 0.35 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Roma HA -1.5 [Cuota 1.55]\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Under 3.5 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Roma (7.4) vs Slovan Bratislava (1.9)\n"
            "• 🧤 <b>Paradas Portero Slovan:</b> Over 5.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "La Roma no puede tropezar en el Olímpico ante el rival más débil del grupo. Los italianos saldrán con un ritmo abrumador desde el minuto inicial para sentenciar el choque antes del descanso. El hándicap asiático a favor de la Roma nos ofrece una cobertura de altísima seguridad."
        )
    },
    {
        "code": "UCL-STU-ATM",
        "text": (
            "🇪🇺 <b>UEFA CHAMPIONS LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 21:00 CEST | ⚔️ <b>VfB Stuttgart vs Atlético de Madrid</b>\n\n"
            "📊 <b>CÓDIGO DE SEGUIMIENTO:</b> <code>UCL-STU-ATM</code>\n\n"
            "• ⚽ <b>xG Proyectado:</b> 1.25 vs 1.65 | Over 2.0 Goles Totales\n"
            "• 🏆 <b>Pick Resultado:</b> Atlético de Madrid HA 0.0 (Apuesta Sin Empate) [Cuota 1.55 / Directo 2.05]\n"
            "• 🚩 <b>Córners totales:</b> Over 8.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas Totales\n"
            "• 🎯 <b>Remates a puerta:</b> Stuttgart (3.8) vs Atlético de Madrid (4.7)\n"
            "• 🧤 <b>Paradas Portero Stuttgart:</b> Over 3.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El conjunto de Simeone sabe competir como nadie en escenarios exigentes de Alemania. El Stuttgart propone un fútbol asociativo pero sufre en transiciones defensivas cuando pierde el balón en la medular. Nos cubrimos con el hándicap asiático nulo a favor del Atlético a cuota de valor."
        )
    }
]

# ---------------------------------------------------------
# Tarea de Publicación Automática
# ---------------------------------------------------------
async def publish_picks(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    logging.info("Enviando publicaciones completas de Champions League...")

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
