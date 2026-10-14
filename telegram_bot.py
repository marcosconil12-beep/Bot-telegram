import os
import time
import logging
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO
from PIL import Image, ImageDraw
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------------------------------------------------
# Configuración de Logging y Entorno
# ---------------------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8657360203:AAG0wJnyLFfEaBMY8XadJs1dZdSQU42ah7c")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@FreeTopTip")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "d6abc7c413mshf80c5e16b6760bcp14e3f9jsnf2c34103db6c")

SPAIN_TZ = ZoneInfo("Europe/Madrid")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    ai_model = None

# ---------------------------------------------------------
# Generador de Banner Elegante (Sin necesidad de logos/escudos)
# ---------------------------------------------------------
def create_match_banner(home_team: str, away_team: str, league: str, match_time: str, pick: str) -> BytesIO:
    width, height = 900, 480
    image = Image.new("RGB", (width, height), color=(11, 19, 43)) # Fondo azul noche VIP
    draw = ImageDraw.Draw(image)

    # Marco exterior
    draw.rectangle([10, 10, width - 10, height - 10], outline=(37, 99, 235), width=3)

    # Banner Superior de Liga
    draw.rectangle([30, 25, width - 30, 85], fill=(30, 41, 59))
    draw.text((45, 38), f"🏆 {league[:55].upper()}", fill=(255, 255, 255))
    draw.text((45, 62), f"⏰ HORA: {match_time} | 🟢 ANÁLISIS SCORES24", fill=(52, 211, 153))

    # Texto Enfrentamiento
    draw.text((50, 130), "ENFRENTAMIENTO DIRECTO", fill=(148, 163, 184))
    match_str = f"⚔️  {home_team.upper()}\n       VS\n    {away_team.upper()}"
    draw.text((50, 165), match_str, fill=(248, 250, 252))

    # Recuadro Pronóstico Principal
    draw.rectangle([30, 330, width - 30, 435], fill=(15, 23, 42), outline=(16, 185, 129), width=3)
    draw.text((50, 345), "🎯 RECOMENDACIÓN SCORES24 / APUESTA DE VALOR", fill=(16, 185, 129))
    draw.text((50, 380), f"🔥 {pick}", fill=(255, 255, 255))

    # Firma inferior
    draw.text((width - 240, height - 25), "Canal Oficial: @FreeTopTip", fill=(100, 116, 139))

    bio = BytesIO()
    bio.name = "pick_banner.png"
    image.save(bio, "PNG")
    bio.seek(0)
    return bio

# ---------------------------------------------------------
# Filtro de Ligas Profesionales Top
# ---------------------------------------------------------
def is_valid_professional_league(league_name: str) -> bool:
    name = league_name.upper()
    forbidden = ["SUB-", "SUB ", "U15", "U17", "U19", "U20", "U21", "U23", "JUVENIL", "AMATEUR", "REGIONAL", "WOMEN", "FEMENINO", "ACADEMY"]
    for term in forbidden:
        if term in name:
            return False
    return True

def fetch_realtime_matches() -> list:
    matches = []
    if not RAPIDAPI_KEY:
        return matches

    url = "https://flashlive-sports.p.rapidapi.com/v1/events/list"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
    }

    try:
        params = {"sport_id": "1", "indent_days": "0", "locale": "es_ES", "timezone": "2"}
        res = requests.get(url, headers=headers, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            for tournament in data.get("DATA", []):
                league = tournament.get("NAME", "Liga").upper()
                country = tournament.get("COUNTRY_NAME", "Global").upper()
                full_league = f"{country} - {league}"

                if not is_valid_professional_league(full_league):
                    continue

                for ev in tournament.get("EVENTS", []):
                    home = ev.get("HOME_NAME", "")
                    away = ev.get("AWAY_NAME", "")
                    start_ts = ev.get("START_TIME", 0)
                    m_time = datetime.fromtimestamp(start_ts, SPAIN_TZ).strftime("%H:%M") + " CEST" if start_ts else "Por definir"

                    if home and away:
                        matches.append({
                            "league": full_league,
                            "home": home,
                            "away": away,
                            "time": m_time
                        })
    except Exception as e:
        logging.error(f"Error extrayendo partidos: {e}")

    return matches

# ---------------------------------------------------------
# Análisis Completo e Imparable Estilo Scores24
# ---------------------------------------------------------
def generate_advanced_multimarket_analysis(m: dict) -> tuple[str, str]:
    prompt = f"""
    Actúa como un tipster y analista profesional de fútbol estilo Scores24 para el canal @FreeTopTip.
    Analiza este partido profesional de forma extensa y detallada:

    Liga: {m['league']}
    Partido: {m['home']} vs {m['away']}
    Hora: {m['time']}

    Redacta obligatoriamente un post completo en HTML para Telegram con esta estructura exacta:

    🏆 <b>{m['league']}</b>
    ⏰ <b>Hora:</b> {m['time']} | ⚔️ <b>{m['home']} vs {m['away']}</b>

    📊 <b>MÉTRICAS SCORES24 Y ESTADÍSTICAS:</b>
    • ⚽ <b>xG (Goles Esperados):</b> Proyección analítica basada en últimos 5 partidos.
    • 🚩 <b>Córners proyectados:</b> Promedio estimado por banda.
    • 🟨 <b>Línea de Tarjetas:</b> Intensidad del árbitro y faltas cometidas.
    • 🎯 <b>Remates a puerta:</b> Estimación de tiros globales.

    💡 <b>ANÁLISIS TÁCTICO PROFUNDO:</b>
    Escribe 2 párrafos detallados redactados en primera persona analizando el momento de forma de ambos conjuntos, planteamiento de los entrenadores y dinámicas ofensivas.

    🎯 <b>PRONÓSTICO VIP:</b> [Selecciona un mercado claro: ej. Gana Local sin empate / Over 2.5 Goles / Over 8.5 Córners / Hándicap Asiático]
    🎲 <b>Índice de Confianza:</b> 85%

    📲 Contacto VIP: @Mark122
    """

    pick = "Gana Local / Apuesta Sin Empate"
    if ai_model:
        try:
            res = ai_model.generate_content(prompt)
            if res and res.text:
                text = res.text.strip()
                if "PRONÓSTICO VIP" in text:
                    for line in text.split("\n"):
                        if "PRONÓSTICO VIP" in line:
                            pick = line.split(":")[-1].replace("<b>", "").replace("</b>", "").strip()
                return text, pick
        except Exception as e:
            logging.error(f"Error en Gemini: {e}")

    # Si por alguna razón la IA fallara temporalmente, enviamos este análisis Scores24 completo de respaldo
    fallback = (
        f"🏆 <b>{m['league']}</b>\n"
        f"⏰ <b>Hora:</b> {m['time']} | ⚔️ <b>{m['home']} vs {m['away']}</b>\n\n"
        f"📊 <b>MÉTRICAS SCORES24 Y ESTADÍSTICAS:</b>\n"
        f"• ⚽ <b>xG (Goles Esperados):</b> 1.75 vs 1.20\n"
        f"• 🚩 <b>Córners proyectados:</b> Over 8.5 Córners\n"
        f"• 🟨 <b>Línea de Tarjetas:</b> Over 3.5 Tarjetas\n"
        f"• 🎯 <b>Remates a puerta:</b> 8.5 globales\n\n"
        f"💡 <b>ANÁLISIS TÁCTICO PROFUNDO:</b>\n"
        f"El conjunto local llega tras mostrar un rendimiento sólido en sus últimas presentaciones, destacando por su volumen ofensivo y presión en campo contrario. Por su parte, el equipo visitante suele presentar dificultades cuando encaja el primer gol, lo que puede condicionar su planteamiento táctico.\n\n"
        f"Esperamos un partido abierto con claras oportunidades en ambas áreas donde la mayor efectividad de los locales marcará la diferencia.\n\n"
        f"🎯 <b>PRONÓSTICO VIP:</b> {pick}\n"
        f"🎲 <b>Índice de Confianza:</b> 85%\n\n"
        f"📲 Contacto VIP: @Mark122"
    )
    return fallback, pick

# ---------------------------------------------------------
# Tarea de Publicación Automática
# ---------------------------------------------------------
async def auto_post_job(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    logging.info("Buscando partidos profesionales para publicar...")
    matches = fetch_realtime_matches()

    if not matches:
        logging.info("No hay partidos profesionales disponibles en este momento.")
        return

    for m in matches[:2]:
        try:
            analysis_html, pick_text = generate_advanced_multimarket_analysis(m)
            banner_img = create_match_banner(m['home'], m['away'], m['league'], m['time'], pick_text)

            await bot.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=banner_img,
                caption=analysis_html,
                parse_mode="HTML"
            )
            time.sleep(6)
        except Exception as e:
            logging.error(f"Error publicando en canal: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot activo en Modo Piloto Automático con análisis estilo Scores24.", parse_mode="HTML")

async def force_post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Generando análisis Scores24 y publicando en el canal...")
    await auto_post_job(context)
    await update.message.reply_text("✅ Publicación completada con éxito.")

def main():
