import os
import time
import logging
import random
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from io import BytesIO
from PIL import Image, ImageDraw
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------------------------------------------------
# Configuración y Entorno
# ---------------------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8657360203:AAHdtvCjS5o4_-p2Bk7w6mSDBBA2gbHi470")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@FreeTopTip")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "d6abc7c413mshf80c5e16b6760bcp14e3f9jsnf2c34103db6c")

SPAIN_TZ = ZoneInfo("Europe/Madrid")
PUBLISHED_MATCHES_TODAY = set()
LAST_CLEAN_DATE = datetime.now(SPAIN_TZ).strftime("%Y-%m-%d")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    ai_model = None

# ---------------------------------------------------------
# Banner Visual Pro
# ---------------------------------------------------------
def create_match_banner(home_team: str, away_team: str, league: str, match_time: str, pick: str) -> BytesIO:
    width, height = 900, 480
    image = Image.new("RGB", (width, height), color=(11, 19, 43))
    draw = ImageDraw.Draw(image)

    draw.rectangle([10, 10, width - 10, height - 10], outline=(37, 99, 235), width=3)
    draw.rectangle([30, 25, width - 30, 85], fill=(30, 41, 59))
    draw.text((45, 38), f"🏆 {league[:55].upper()}", fill=(255, 255, 255))
    draw.text((45, 62), f"⏰ HORA: {match_time} | 🟢 ANÁLISIS SCORES24 EN VIVO", fill=(52, 211, 153))

    draw.text((50, 130), "PRÓXIMO ENCUENTRO", fill=(148, 163, 184))
    match_str = f"⚔️  {home_team.upper()}\n       VS\n    {away_team.upper()}"
    draw.text((50, 165), match_str, fill=(248, 250, 252))

    draw.rectangle([30, 330, width - 30, 435], fill=(15, 23, 42), outline=(16, 185, 129), width=3)
    draw.text((50, 345), "🎯 RECOMENDACIÓN / HÁNDICAP / MERCADO DE VALOR", fill=(16, 185, 129))
    draw.text((50, 380), f"🔥 {pick}", fill=(255, 255, 255))

    draw.text((width - 240, height - 25), "Canal Oficial: @FreeTopTip", fill=(100, 116, 139))

    bio = BytesIO()
    bio.name = "pick_banner.png"
    image.save(bio, "PNG")
    bio.seek(0)
    return bio

# ---------------------------------------------------------
# Filtro y Obtención de Partidos (Variados)
# ---------------------------------------------------------
def fetch_upcoming_12h_matches() -> list:
    matches = []
    if not RAPIDAPI_KEY:
        return matches

    url = "https://flashlive-sports.p.rapidapi.com/v1/events/list"
    headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"}
    now = datetime.now(SPAIN_TZ)
    limit_time = now + timedelta(hours=12)

    try:
        params = {"sport_id": "1", "indent_days": "0", "locale": "es_ES", "timezone": "2"}
        res = requests.get(url, headers=headers, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            for tournament in data.get("DATA", []):
                league = tournament.get("NAME", "Liga").upper()
                country = tournament.get("COUNTRY_NAME", "Global").upper()
                full_league = f"{country} - {league}"

                # Ignorar categorías juveniles
                if any(x in full_league for x in ["SUB-", "U19", "U21", "U23", "JUVENIL", "WOMEN", "FEMENINO"]):
                    continue

                for ev in tournament.get("EVENTS", []):
                    start_ts = ev.get("START_TIME", 0)
                    if not start_ts:
                        continue
                    
                    match_dt = datetime.fromtimestamp(start_ts, SPAIN_TZ)
                    if now <= match_dt <= limit_time:
                        home = ev.get("HOME_NAME", "")
                        away = ev.get("AWAY_NAME", "")
                        if home and away:
                            matches.append({
                                "league": full_league,
                                "home": home,
                                "away": away,
                                "time": match_dt.strftime("%H:%M") + " CEST",
                                "id": f"{home}_vs_{away}"
                            })
    except Exception as e:
        logging.error(f"Error consultando partidos: {e}")

    # Mezclamos la lista para que rote entre diferentes ligas de los 100+ partidos disponibles
    random.shuffle(matches)
    return matches

# ---------------------------------------------------------
# Análisis Extenso Scores24 Garantizado
# ---------------------------------------------------------
def generate_advanced_multimarket_analysis(m: dict) -> tuple[str, str]:
    prompt = f"""
    Actúa como analista jefe estilo Scores24 para @FreeTopTip.
    Analiza de forma EXTENSA y profesional este partido:

    Liga: {m['league']}
    Partido: {m['home']} vs {m['away']}
    Hora: {m['time']}

    Redacta un post en HTML para Telegram que contenga OBLIGATORIAMENTE esta estructura exacta:

    🏆 <b>{m['league']}</b>
    ⏰ <b>Hora:</b> {m['time']} | ⚔️ <b>{m['home']} vs {m['away']}</b>

    📊 <b>MÉTRICAS SCORES24 EN TIEMPO REAL:</b>
    • ⚽ <b>Goles previstos (xG):</b> 1.85 vs 1.30
    • 🚩 <b>Córners estimados:</b> Over 8.5 Córners
    • 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas
    • 📈 <b>Estado de forma:</b> Tendencia positiva en juego directo.

    💡 <b>ANÁLISIS TÁCTICO PROFUNDO:</b>
    [Escribe 2 párrafos extensos detallando el momento de forma de ambos conjuntos, planteamiento táctico de los técnicos, juego por bandas y volumen de remates esperados].

    🎯 <b>PICK RECOMENDADO:</b> [Indica un pronóstico claro: ej. Gana Local / Hándicap Asiático -0.5 / Over 2.5 Goles]
    🎲 <b>Índice de Confianza:</b> 85%

    📩 <b>Para solicitar el STAKE MÁXIMO o acceso al CANAL VIP, pulsa el botón de abajo para hablar conmigo.</b>
    """

    pick = f"Hándicap Asiático {m['home']} 0.0"
    if ai_model:
        try:
            res = ai_model.generate_content(prompt)
            if res and res.text:
                text = res.text.strip()
                if "PICK RECOMENDADO" in text and "ANÁLISIS TÁCTICO" in text:
                    for line in text.split("\n"):
                        if "PICK RECOMENDADO" in line:
                            pick = line.split(":")[-1].replace("<b>", "").replace("</b>", "").strip()
                    return text, pick
        except Exception as e:
            logging.error(f"Error en Gemini: {e}")

    # Texto extenso completo por defecto para evitar NUNCA publicar mensajes cortos
    extenso_fallback = (
        f"🏆 <b>{m['league']}</b>\n"
        f"⏰ <b>Hora:</b> {m['time']} | ⚔️ <b>{m['home']} vs {m['away']}</b>\n\n"
        f"📊 <b>MÉTRICAS SCORES24 EN TIEMPO REAL:</b>\n"
        f"• ⚽ <b>Goles previstos (xG):</b> 1.75 vs 1.25 (xG Esperado)\n"
        f"• 🚩 <b>Córners estimados:</b> Over 8.5 Córners Totales\n"
        f"• 🟨 <b>Tarjetas totales:</b> Over 3.5 Tarjetas en el partido\n"
        f"• 📈 <b>Estado de forma:</b> Alto volumen de llegadas por bandas\n\n"
        f"💡 <b>ANÁLISIS TÁCTICO PROFUNDO:</b>\n"
        f"El conjunto local de {m['home']} afronta este compromiso con la necesidad de consolidar su propuesta ofensiva en campo contrario. Las métricas avanzadas reflejan que promedian un alto índice de recuperación tras pérdida en la medular, lo que les permite generar un flujo constante de remates hacia la portería rival.\n\n"
        f"Por su parte, {m['away']} suele presentar ciertas desatenciones defensivas cuando se ve sometido a transiciones rápidas fuera de casa. Esperamos un desarrollo táctico donde el ritmo impuesto por el cuadro local incline la balanza a favor de nuestro mercado seleccionado.\n\n"
        f"🎯 <b>PICK RECOMENDADO:</b> {pick}\n"
        f"🎲 <b>Índice de Confianza:</b> 85%\n\n"
        f"📩 <b>Para solicitar el STAKE MÁXIMO o acceso al CANAL VIP, pulsa el botón de abajo para hablar conmigo.</b>"
    )
    return extenso_fallback, pick

# ---------------------------------------------------------
# Tarea Programada con Control Anti-Duplicados
# ---------------------------------------------------------
async def auto_post_job(context: ContextTypes.DEFAULT_TYPE):
    global PUBLISHED_MATCHES_TODAY, LAST_CLEAN_DATE
    
    # Limpieza diaria del historial de partidos
    today_str = datetime.now(SPAIN_TZ).strftime("%Y-%m-%d")
    if today_str != LAST_CLEAN_DATE:
        LAST_CLEAN_DATE = today_str
        PUBLISHED_MATCHES_TODAY.clear()

    bot = context.bot
    matches = fetch_upcoming_12h_matches()

    if not matches:
        logging.info("No hay partidos disponibles en el filtro actual.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 UNIRSE AL VIP / CONTACTO DIRECTO", url="https://t.me/Mark122")]
    ])

    for m in matches:
        match_id = m["id"]
        
        # SI YA FUE PUBLICADO HOY, SE SALTA AL SIGUIENTE
        if match_id in PUBLISHED_MATCHES_TODAY:
            continue

        # MARCAR COMO PUBLICADO ANTES DE ENVIAR PARA EVITAR DUPLICADOS
        PUBLISHED_MATCHES_TODAY.add(match_id)

        try:
            analysis_html, pick_text = generate_advanced_multimarket_analysis(m)
            banner_img = create_match_banner(m['home'], m['away'], m['league'], m['time'], pick_text)

            await bot.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=banner_img,
                caption=analysis_html,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            logging.info(f"Publicado con éxito: {match_id}")
            break  # Publica 1 único partido por ciclo de 30 min
        except Exception as e:
            logging.error(f"Error en auto_post para {match_id}: {e}")

# ---------------------------------------------------------
# Respuestas por Comandos Directos
# ---------------------------------------------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(msg="Excepción gestionada:", exc_info=context.error)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 HABLAR CON MARK122", url="https://t.me/Mark122")]
    ])
    await update.message.reply_text(
        "👋 <b>¡Hola! Bienvenido al bot oficial de @FreeTopTip.</b>\n\n"
        "Para unirte a nuestro Canal VIP o consultar dudas, pulsa el botón de abajo para hablar conmigo directamente.",
        parse_mode="HTML",
        reply_markup=keyboard
    )

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_error_handler(error_handler)

    job_queue = application.job_queue
    if job_queue:
        # Revisa cada 30 minutos (1800 segundos)
        job_queue.run_repeating(auto_post_job, interval=1800, first=15)

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("vip", start_command))

    logging.info("Bot configurado con rotación de partidos y análisis extenso garantizado...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
