import os
import time
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO
from PIL import Image, ImageDraw
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------------------------------------------------
# Configuración
# ---------------------------------------------------------
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8657360203:AAHdtvCjS5o4_-p2Bk7w6mSDBBA2gbHi470")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@FreeTopTip")

SPAIN_TZ = ZoneInfo("Europe/Madrid")

# ---------------------------------------------------------
# Carga de Partidos Seleccionados "A la Carta"
# ---------------------------------------------------------
MATCH_ANALYSIS_LIST = [
    {
        "id": "depor_levante",
        "league": "ESPAÑA - LALIGA EA SPORTS",
        "home": "Deportivo de La Coruña",
        "away": "Levante",
        "time": "21:00 CEST",
        "pick_banner": "Over 4.5 Paradas Portero Levante",
        "caption": (
            "🏆 <b>ESPAÑA - LALIGA EA SPORTS</b>\n"
            "⏰ <b>Hora:</b> 21:00 CEST | ⚔️ <b>Deportivo vs Levante</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PROYECCIÓN:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 1.85 vs 1.15 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Deportivo Apuesta Sin Empate (HA 0.0)\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Deportivo (6.5) vs Levante (3.8)\n"
            "• 🧤 <b>Paradas Portero Levante:</b> Over 4.5 Paradas (Cuota 2.20)\n\n"
            "💡 <b>ANÁLISIS TÁCTICO SCORES24:</b>\n"
            "El Deportivo en Riazor sale habitualmente con un planteamiento de asedio constante desde los primeros minutos, cargando el área rival y promediando un volumen alto de disparos lejanos. El Levante acostumbra a replegar en bloque medio cuando juega fuera de casa, concediendo metros y obligando a su guardameta a intervenir constantemente.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Portero Levante Over 4.5 Paradas\n"
            "🎲 <b>Índice de Confianza:</b> 88%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "leganes_cordoba",
        "league": "ESPAÑA - SEGUNDA DIVISIÓN",
        "home": "Leganés",
        "away": "Córdoba",
        "time": "20:30 CEST",
        "pick_banner": "Leganés Gana / Hándicap Asiático 0.0",
        "caption": (
            "🏆 <b>ESPAÑA - SEGUNDA DIVISIÓN</b>\n"
            "⏰ <b>Hora:</b> 20:30 CEST | ⚔️ <b>Leganés vs Córdoba</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PROYECCIÓN:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 1.45 vs 0.90 | Under 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Leganés Victoria Directa (o HA 0.0)\n"
            "• 🚩 <b>Córners totales:</b> Over 8.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 5.5 Tarjetas (Árbitro severo)\n"
            "• 🎯 <b>Remates a puerta:</b> Leganés (5.2) vs Córdoba (3.1)\n"
            "• 🧤 <b>Paradas de Porteros:</b> Leganés (2.5) vs Córdoba (4.0)\n\n"
            "💡 <b>ANÁLISIS TÁCTICO SCORES24:</b>\n"
            "El Leganés en Butarque ha mostrado una solidez defensiva envidiable, concediendo muy poco espacio entre líneas. El Córdoba sufre bastante en sus salidas para generar peligro en juego posicional. Prevemos un duelo táctico cerrado donde la eficacia local decantará el partido.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Leganés Hándicap Asiático 0.0\n"
            "🎲 <b>Índice de Confianza:</b> 85%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "frosinone_sassuolo",
        "league": "ITALIA - SERIE A",
        "home": "Frosinone",
        "away": "Sassuolo",
        "time": "20:45 CEST",
        "pick_banner": "Over 2.5 Goles Totales",
        "caption": (
            "🏆 <b>ITALIA - SERIE A</b>\n"
            "⏰ <b>Hora:</b> 20:45 CEST | ⚔️ <b>Frosinone vs Sassuolo</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PROYECCIÓN:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 1.70 vs 1.85 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Ambos Anotan / Sassuolo HA 0.0\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.0 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Frosinone (4.8) vs Sassuolo (5.9)\n"
            "• 🧤 <b>Paradas Portero Frosinone:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO SCORES24:</b>\n"
            "El Sassuolo es uno de los equipos más verticales de Italia, proponiendo partidos de ida y vuelta con mucha carga ofensiva. El Frosinone en casa no se arruga y acepta el intercambio de golpes, lo que deja escenarios idóneos para ver goles en ambas porterías y un alto volumen de remates.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Over 2.5 Goles Totales\n"
            "🎲 <b>Índice de Confianza:</b> 87%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "eintracht_colonia",
        "league": "ALEMANIA - BUNDESLIGA",
        "home": "Eintracht Frankfurt",
        "away": "Colonia",
        "time": "20:30 CEST",
        "pick_banner": "Victoria Eintracht Frankfurt",
        "caption": (
            "🏆 <b>ALEMANIA - BUNDESLIGA</b>\n"
            "⏰ <b>Hora:</b> 20:30 CEST | ⚔️ <b>Eintracht Frankfurt vs Colonia</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PROYECCIÓN:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 2.20 vs 0.95 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Eintracht Frankfurt (1.75)\n"
            "• 🚩 <b>Córners totales:</b> Over 10.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 3.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Frankfurt (7.1) vs Colonia (3.0)\n"
            "• 🧤 <b>Paradas Portero Colonia:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO SCORES24:</b>\n"
            "El Eintracht imprime una intensidad altísima en el Deutsche Bank Park, explotando las bandas con sus carrileros. El Colonia sufre enormemente en desplazamientos defensivos ante equipos de nivel europeo. La cuota 1.75 por la victoria local tiene un valor cuantitativo excelente.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Victoria Eintracht Frankfurt (1.75)\n"
            "🎲 <b>Índice de Confianza:</b> 90%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "lemans_toulouse",
        "league": "FRANCIA - LIGUE 1",
        "home": "Le Mans",
        "away": "Toulouse",
        "time": "20:45 CEST",
        "pick_banner": "Toulouse Apuesta Sin Empate (HA 0.0)",
        "caption": (
            "🏆 <b>FRANCIA - LIGUE 1</b>\n"
            "⏰ <b>Hora:</b> 20:45 CEST | ⚔️ <b>Le Mans vs Toulouse</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PROYECCIÓN:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 1.05 vs 1.65 | Over 1.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Toulouse Apuesta Sin Empate (HA 0.0)\n"
            "• 🚩 <b>Córners totales:</b> Over 8.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.0 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Le Mans (3.5) vs Toulouse (5.2)\n"
            "• 🧤 <b>Paradas Portero Le Mans:</b> Over 3.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO SCORES24:</b>\n"
            "El Toulouse llega con mayor rodaje físico y jerarquía individual para dominar la posesión en el centro del campo. Le Mans intentará replegarse y salir a la contra, pero la presión alta visitante terminará decantando las ocasiones claras hacia el bando del Toulouse.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Toulouse Apuesta Sin Empate (HA 0.0)\n"
            "🎲 <b>Índice de Confianza:</b> 86%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "burnley_wolves",
        "league": "INGLATERRA - CHAMPIONSHIP",
        "home": "Burnley",
        "away": "Wolverhampton",
        "time": "21:00 CEST",
        "pick_banner": "Over 8.5 Córners / Burnley HA 0.0",
        "caption": (
            "🏆 <b>INGLATERRA - CHAMPIONSHIP</b>\n"
            "⏰ <b>Hora:</b> 21:00 CEST | ⚔️ <b>Burnley vs Wolverhampton</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PROYECCIÓN:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 1.50 vs 1.40 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Burnley Apuesta Sin Empate (HA 0.0)\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Burnley (5.0) vs Wolves (4.8)\n"
            "• 🧤 <b>Paradas Portero Burnley:</b> Over 3.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO SCORES24:</b>\n"
            "Partidazo inglés de viernes. Los Wolves imponen un juego directo y vertical que genera constantes saques de esquina, mientras que el Burnley en su feudo se muestra sumamente rocoso y efectivo tras recuperar el balón en medio campo. Encuentro muy parejo ideal para buscar saques de esquina o hándicap cubierto.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Over 8.5 Córners / Burnley HA 0.0\n"
            "🎲 <b>Índice de Confianza:</b> 87%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    }
]

# ---------------------------------------------------------
# Banner Visual Pro
# ---------------------------------------------------------
def create_match_banner(home_team: str, away_team: str, league: str, match_time: str, pick: str) -> BytesIO:
    width, height = 900, 480
    image = Image.new("RGB", (width, height), color=(11, 19, 43))
    draw = ImageDraw.Draw(image)

    draw.rectangle([10, 10, width - 10, height - 10], outline=(37, 99, 235), width=3)
    draw.rectangle([30, 25, width - 30, 85], fill=(30, 41, 59))
    draw.text((45, 38), f"🏆 {league[:50].upper()}", fill=(255, 255, 255))
    draw.text((45, 62), f"⏰ HORA: {match_time} | 🟢 ANÁLISIS SCORES24 EN VIVO", fill=(52, 211, 153))

    draw.text((50, 130), "PRÓXIMO ENCUENTRO SELECCIONADO", fill=(148, 163, 184))
    match_str = f"⚔️  {home_team.upper()}\n       VS\n    {away_team.upper()}"
    draw.text((50, 165), match_str, fill=(248, 250, 252))

    draw.rectangle([30, 330, width - 30, 435], fill=(15, 23, 42), outline=(16, 185, 129), width=3)
    draw.text((50, 345), "🎯 RECOMENDACIÓN SCORES24 / APUESTA DE VALOR", fill=(16, 185, 129))
    draw.text((50, 380), f"🔥 {pick[:45]}", fill=(255, 255, 255))

    draw.text((width - 240, height - 25), "Canal Oficial: @FreeTopTip", fill=(100, 116, 139))

    bio = BytesIO()
    bio.name = "pick_banner.png"
    image.save(bio, "PNG")
    bio.seek(0)
    return bio

# ---------------------------------------------------------
# Tarea de Publicación Automática
# ---------------------------------------------------------
async def publish_selected_matches(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    logging.info("Iniciando publicación inmediata de partidos analizados...")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 UNIRSE AL VIP / CONTACTO DIRECTO", url="https://t.me/Mark122")]
    ])

    for match in MATCH_ANALYSIS_LIST:
        try:
            banner_img = create_match_banner(
                match['home'], match['away'], match['league'], match['time'], match['pick_banner']
            )

            await bot.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=banner_img,
                caption=match['caption'],
                parse_mode="HTML",
                reply_markup=keyboard
            )
            logging.info(f"Publicado con éxito: {match['id']}")
            time.sleep(4)  # Pausa de seguridad entre publicaciones
        except Exception as e:
            logging.error(f"Error publicando {match['id']}: {e}")

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
        # Ejecuta la publicación de todos los picks a los 5 segundos de arrancar
        job_queue.run_once(publish_selected_matches, when=5)

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("vip", start_command))

    logging.info("Bot en marcha. Publicación de partidos programada...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
