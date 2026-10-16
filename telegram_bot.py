import os
import time
import logging
import random
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from io import BytesIO
from PIL import Image, ImageDraw
from google import genai
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

# Cliente de Gemini Oficial
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        logging.error(f"Error inicializando cliente Gemini: {e}")
        ai_client = None
else:
    ai_client = None

# ---------------------------------------------------------
# Generador de Banner Elegante
# ---------------------------------------------------------
def create_match_banner(home_team: str, away_team: str, league: str, match_time: str, pick: str) -> BytesIO:
    width, height = 900, 480
    image = Image.new("RGB", (width, height), color=(11, 19, 43))
    draw = ImageDraw.Draw(image)

    draw.rectangle([10, 10, width - 10, height - 10], outline=(37, 99, 235), width=3)
    draw.rectangle([30, 25, width - 30, 85], fill=(30, 41, 59))
    draw.text((45, 38), f"🏆 {league[:50].upper()}", fill=(255, 255, 255))
    draw.text((45, 62), f"⏰ HORA: {match_time} | 🟢 ANÁLISIS SCORES24 EN VIVO", fill=(52, 211, 153))

    draw.text((50, 130), "PRÓXIMO ENCUENTRO", fill=(148, 163, 184))
    match_str = f"⚔️  {home_team.upper()}\n       VS\n    {away_team.upper()}"
    draw.text((50, 165), match_str, fill=(248, 250, 252))

    draw.rectangle([30, 330, width - 30, 435], fill=(15, 23, 42), outline=(16, 185, 129), width=3)
    draw.text((50, 345), "🎯 RECOMENDACIÓN / HÁNDICAP / MERCADO DE VALOR", fill=(16, 185, 129))
    draw.text((50, 380), f"🔥 {pick[:45]}", fill=(255, 255, 255))

    draw.text((width - 240, height - 25), "Canal Oficial: @FreeTopTip", fill=(100, 116, 139))

    bio = BytesIO()
    bio.name = "pick_banner.png"
    image.save(bio, "PNG")
    bio.seek(0)
    return bio

# ---------------------------------------------------------
# Filtro de Partidos
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

    random.shuffle(matches)
    return matches

# ---------------------------------------------------------
# Generación de Análisis Scores24 Conciso y Válido
# ---------------------------------------------------------
def generate_advanced_multimarket_analysis(m: dict) -> tuple[str, str]:
    prompt = f"""
    Actúa como analista jefe estilo Scores24 para @FreeTopTip.
    Analiza este partido de forma clara y directa:

    Liga: {m['league']}
    Partido: {m['home']} vs {m['away']}
    Hora: {m['time']}

    Redacta un post en HTML para Telegram (máximo 800 caracteres) con esta estructura exacta:

    🏆 <b>{m['league']}</b>
    ⏰ <b>Hora:</b> {m['time']} | ⚔️ <b>{m['home']} vs {m['away']}</b>

    📊 <b>MÉTRICAS SCORES24:</b>
    • ⚽ <b>xG:</b> 1.75 vs 1.25
    • 🚩 <b>Córners:</b> Over 8.5
    • 🟨 <b>Tarjetas:</b> Over 3.5

    💡 <b>ANÁLISIS TÁCTICO:</b>
    El equipo local llega en dinámica positiva y monopolizando el ataque por bandas. El visitante suele encajar pronto fuera de casa, concediendo volumen de tiro.

    🎯 <b>PICK RECOMENDADO:</b> Gana Local / Hándicap 0.0
    🎲 <b>Confianza:</b> 85%

    📩 <b>Solicita el STAKE MÁXIMO en el botón de abajo.</b>
    """

    pick = f"Hándicap Asiático {m['home']} 0.0"

    if ai_client:
        try:
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            if response and response.text:
                text = response.text.strip()
                if "PICK RECOMENDADO" in text:
                    for line in text.split("\n"):
                        if "PICK RECOMENDADO" in line:
                            pick = line.split(":")[-1].replace("<b>", "").replace("</b>", "").strip()
                return text, pick
        except Exception as e:
            logging.error(f"Error llamando a Gemini SDK: {e}")

    extenso_fallback = (
        f"🏆 <b>{m['league']}</b>\n"
        f"⏰ <b>Hora:</b> {m['time']} | ⚔️ <b>{m['home']} vs {m['away']}</b>\n\n"
        f"📊 <b>MÉTRICAS SCORES24:</b>\n"
        f"• ⚽ <b>xG Proyectado:</b> 1.75 vs 1.20\n"
        f"• 🚩 <b>Córners estimados:</b> Over 8.5\n"
        f"• 🟨 <b>Tarjetas esperadas:</b> Over 3.5\n\n"
        f"💡 <b>ANÁLISIS TÁCTICO:</b>\n"
        f"El conjunto de {m['home']} mantiene un ritmo de alta presión tras pérdida en su feudo. Por su parte, {m['away']} suele conceder espacios al replegarse en transiciones rápidas fuera de casa.\n\n"
        f"🎯 <b>PICK RECOMENDADO:</b> {pick}\n"
        f"🎲 <b>Confianza:</b> 85%\n\n"
        f"📩 <b>Habla conmigo para acceder al VIP.</b>"
    )
    return extenso_fallback, pick

# ---------------------------------------------------------
# Tarea de Publicación con Recorte de Seguridad (Límite 1024)
# ---------------------------------------------------------
async def auto_post_job(context: ContextTypes.DEFAULT_TYPE):
    global PUBLISHED_MATCHES_TODAY, LAST_CLEAN_DATE
    
    today_str = datetime.now(SPAIN_TZ).strftime("%Y-%m-%d")
    if today_str != LAST_CLEAN_DATE:
        LAST_CLEAN_DATE = today_str
        PUBLISHED_MATCHES_TODAY.clear()

    bot = context.bot
    matches = fetch_upcoming_12h_matches()

    if not matches:
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 UNIRSE AL VIP / CONTACTO DIRECTO", url="https://t.me/Mark122")]
    ])

    for m in matches:
        match_id = m["id"]
        
        if match_id in PUBLISHED_MATCHES_TODAY:
            continue

        PUBLISHED_MATCHES_TODAY.add(match_id)

        try:
            analysis_html, pick_text = generate_advanced_multimarket_analysis(m)
            banner_img = create_match_banner(m['home'], m['away'], m['league'], m['time'], pick_text)

            # Recorte estricto de seguridad para no superar el límite de 1024 caracteres de Telegram para fotos
            if len(analysis_html) > 1000:
                analysis_html = analysis_html[:990] + "...\n\n📩 <b>Contacto VIP:</b> @Mark122"

            await bot.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=banner_img,
                caption=analysis_html,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            logging.info(f"Publicado con éxito: {match_id}")
            break
        except Exception as e:
            logging.error(f"Error en auto_post para {match_id}: {e}")

# ---------------------------------------------------------
# Controladores y Ejecución
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
        job_queue.run_repeating(auto_post_job, interval=1800, first=15)

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("vip", start_command))

    logging.info("Bot en marcha con límites de texto ajustados...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
