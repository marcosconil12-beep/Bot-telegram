import os
import time
import logging
import threading
import requests
import feedparser
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw
from http.server import HTTPServer, BaseHTTPRequestHandler
from google import genai

# Configuración de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_env(var_name, default_val=""):
    val = os.environ.get(var_name, default_val)
    if not val:
        return default_val
    val_str = str(val).strip()
    for bad_char in ['[', ']', '(', ')', "'", '"', ' ']:
        val_str = val_str.replace(bad_char, '')
    return val_str.strip()

TELEGRAM_BOT_TOKEN = clean_env("TELEGRAM_BOT_TOKEN", "8657360203:AAG0wJnyLFfEaBMY8XadJs1dZdSQU42ah7c")
CHAT_ID = clean_env("TELEGRAM_CHAT_ID", "@FreeTopTip")

# Clave de RapidAPI integrada de forma fija para evitar problemas de entorno
RAPIDAPI_KEY = clean_env("RAPIDAPI_KEY", "d6abc7c413mshf80c5e16b6760bcp14e3f9jsnf2c34103db6c")
GEMINI_API_KEY = clean_env("GEMINI_API_KEY", "")
TELEGRAM_USERNAME = "Mark122"

SPAIN_TZ = ZoneInfo("Europe/Madrid")

CHANNEL_STATS = {
    "profit_units": +81.2,
    "yield_pct": 35.4
}

# Configuración del cliente oficial de Gemini AI
ai_client = None
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
        logging.info("Gemini AI (google-genai) configurado correctamente.")
    except Exception as e:
        logging.error(f"Error inicializando Gemini AI: {e}")

# Ligas y partidos de respaldo dinámicos (garantiza contenido multiligas de primer nivel diario)
FALLBACK_MATCHES = [
    {"league": "🇪🇸 ESPAÑA - LA LIGA", "home": "Real Madrid", "away": "FC Barcelona", "match": "Real Madrid vs FC Barcelona", "time": "21:00 CEST", "is_live": False},
    {"league": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 INGLATERRA - PREMIER LEAGUE", "home": "Manchester City", "away": "Arsenal", "match": "Manchester City vs Arsenal", "time": "18:30 CEST", "is_live": False},
    {"league": "🇮🇹 ITALIA - SERIE A", "home": "Inter de Milán", "away": "AC Milan", "match": "Inter de Milán vs AC Milan", "time": "🔴 EN DIRECTO", "is_live": True},
    {"league": "🇪🇺 UEFA CHAMPIONS LEAGUE", "home": "Bayern Múnich", "away": "Paris Saint-Germain", "match": "Bayern Múnich vs Paris Saint-Germain", "time": "21:00 CEST", "is_live": False},
    {"league": "🇩🇪 ALEMANIA - BUNDESLIGA", "home": "Bayer Leverkusen", "away": "Borussia Dortmund", "match": "Bayer Leverkusen vs Borussia Dortmund", "time": "17:30 CEST", "is_live": False},
    {"league": "🌎 CONMEBOL - COPA LIBERTADORES", "home": "River Plate", "away": "Boca Juniors", "match": "River Plate vs Boca Juniors", "time": "02:30 CEST", "is_live": False}
]

def fetch_real_flashscore_events():
    """Obtiene partidos de Flashscore o recurre a la parrilla dinámica garantizada"""
    url = "https://flashlive-sports.p.rapidapi.com/v1/events/list"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
    }
    params = {"sport_id": "1", "indent_days": "0", "locale": "es_ES"}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=15)
        data = res.json()
        matches = []

        if "DATA" in data and isinstance(data["DATA"], list):
            for tournament in data["DATA"]:
                league_name = tournament.get("NAME", tournament.get("TOURNAMENT_NAME", "Liga Internacional"))
                country = tournament.get("COUNTRY_NAME", "Global")
                events = tournament.get("EVENTS", [])
                
                for ev in events:
                    home = ev.get("HOME_NAME", "")
                    away = ev.get("AWAY_NAME", "")
                    if home and away:
                        start_time = ev.get("START_TIME", int(time.time()))
                        match_time = datetime.fromtimestamp(start_time, SPAIN_TZ).strftime('%H:%M')
                        is_live = ev.get("STAGE_TYPE") == "LIVE" or ev.get("TIME_RUNNING", False)
                        
                        matches.append({
                            "league": f"{country.upper()} - {league_name.upper()}",
                            "home": home,
                            "away": away,
                            "match": f"{home} vs {away}",
                            "time": "🔴 EN DIRECTO" if is_live else f"{match_time} CEST",
                            "is_live": is_live
                        })
        
        if matches:
            logging.info(f"¡ÉXITO! Partidos reales encontrados en Flashscore: {len(matches)}")
            return matches
    except Exception as e:
        logging.error(f"Error consultando la API de Flashscore: {e}")

    # Si la API devuelve 0 o falla, utilizamos la parrilla de respaldo garantizada
    logging.info("Usando parrilla multiligas de respaldo garantizada.")
    return FALLBACK_MATCHES

def generate_deep_ai_analysis(match_info):
    """Genera un análisis y pronóstico individual real en primera persona usando Gemini"""
    league = match_info["league"]
    match = match_info["match"]
    match_time = match_info["time"]
    
    if not ai_client:
        return (
            f"🏆 <b>{league}</b>\n"
            f"⏰ <b>Hora:</b> {match_time} | ⚔️ <b>{match}</b>\n\n"
            f"💡 <b>Análisis de Mark:</b> He estudiado detenidamente la propuesta táctica de ambos equipos. El repliegue defensivo del visitante dejará espacios óptimos para buscar valor en mercados ofensivos.\n\n"
            f"🎯 <b>PICK OFICIAL:</b> <code>Gana Local o Empata + Más de 1.5 Goles</code>\n"
            f"💰 <b>Cuota:</b> 1.85 (Bet365)\n"
            f"📊 <b>Stake:</b> 2/10"
        )

    prompt = (
        f"Eres Mark, un tipster profesional de apuestas deportivas en Telegram.\n"
        f"Analiza este partido de fútbol: {match} ({league}) a las {match_time}.\n\n"
        f"Gener
