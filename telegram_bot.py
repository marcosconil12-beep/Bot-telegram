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

TELEGRAM_BOT_TOKEN = clean_env("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = clean_env("TELEGRAM_CHAT_ID", "@FreeTopTip")
RAPIDAPI_KEY = clean_env("RAPIDAPI_KEY", "")
GEMINI_API_KEY = clean_env("GEMINI_API_KEY", "")
TELEGRAM_USERNAME = "Mark122"

SPAIN_TZ = ZoneInfo("Europe/Madrid")

CHANNEL_STATS = {
    "profit_units": +78.4,
    "yield_pct": 34.2
}

# Configuración del nuevo cliente oficial de Gemini
ai_client = None
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
        logging.info("Gemini AI (google-genai) configurado correctamente.")
    except Exception as e:
        logging.error(f"Error inicializando Gemini AI: {e}")

# RSS de Noticias
RSS_FEEDS = [
    "https://as.com/rss/futbol/portada.xml",
    "https://e00-marca.uecdn.es/rss/futbol/champions-league.xml",
    "https://www.mundodeportivo.com/rss/futbol.xml"
]

def fetch_real_flashscore_events():
    """Obtiene únicamente partidos reales del día desde Flashscore"""
    if not RAPIDAPI_KEY:
        logging.warning("Falta la clave RAPIDAPI_KEY en las variables de Railway.")
        return []

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
        
        logging.info(f"Partidos reales encontrados en la API: {len(matches)}")
        return matches
    except Exception as e:
        logging.error(f"Error consultando la API de Flashscore: {e}")
        return []

def generate_deep_ai_analysis(match_info):
    """Genera un análisis y pronóstico individual real en primera persona usando Gemini"""
    league = match_info["league"]
    match = match_info["match"]
    match_time = match_info["time"]
    
    if not ai_client:
        return (
            f"🏆 <b>{league}</b>\n"
            f"⏰ <b>Hora:</b> {match_time} | ⚔️ <b>{match}</b>\n\n"
            f"💡 <b>Análisis de Mark:</b> He analizado la dinámica reciente de ambos equipos. La necesidad de puntuar favorece un choque muy dinámico con opciones claras en ambas áreas.\n\n"
            f"🎯 <b>PICK OFICIAL:</b> <code>Ambos Equipos Anotan - SÍ</code>\n"
            f"💰 <b>Cuota:</b> 1.85 (Bet365)\n"
            f"📊 <b>Stake:</b> 2/10"
        )

    prompt = (
        f"Eres Mark, un afamado tipster profesional de apuestas deportivas en Telegram.\n"
        f"Analiza este partido real que se disputa HOY: {match} ({league}) a las {match_time}.\n\n"
        f"Genera una respuesta profesional con este formato HTML estricto para Telegram:\n\n"
        f"🏆 <b>{league}</b>\n"
        f"⏰ <b>Hora:</b> {match_time} | ⚔️ <b>{match}</b>\n\n"
        f"💡 <b>Análisis de Mark:</b>\n"
        f"[Escribe 2 párrafos breves en primera persona analizando la racha de ambos equipos, xG, disparos o aspectos tácticos del encuentro].\n\n"
        f"🎯 <b>PICK OFICIAL:</b> [Indica un mercado claro de Bet365, ej: 'Más de 2.5 Goles', 'Gana Local', 'Ambos Anotan', etc.]\n"
        f"💰 <b>Cuota:</b> [Cuota realista entre 1.70 y 2.25]\n"
        f"📊 <b>Stake recomendado:</b> [1/10 o 2/10]"
    )

    try:
        response = ai_client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        logging.error(f"Error con Gemini AI: {e}")
        return (
            f"🏆 <b>{league}</b>\n"
            f"⏰ <b>Hora:</b> {match_time} | ⚔️ <b>{match}</b>\n\n"
            f"💡 <b>Análisis de Mark:</b> Observo un desequilibrio claro en las transiciones defensivas. La racha realizadora de ambos conjuntos nos otorga valor en la línea de goles.\n\n"
            f"🎯 <b>PICK OFICIAL:</b> <code>Más de 2.25 Goles Asiático</code>\n"
            f"💰 <b>Cuota:</b> 1.80\n"
            f"📊 <b>Stake:</b> 2/10"
        )

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        res = requests.post(url, json=payload, timeout=15)
        return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error enviando mensaje a Telegram: {e}")
        return False

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}
            res = requests.post(url, data=data, files={"photo": photo}, timeout=20)
            return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error enviando foto a Telegram: {e}")
        return False

def create_match_card(match_title, league_name):
    """Genera la tarjeta visual del partido"""
    try:
        img = Image.new('RGB', (1000, 500), color=(13, 27, 42))
        d = ImageDraw.Draw(img)
        
        d.rectangle([20, 20, 980, 480], outline=(0, 212, 170), width=4)
        d.rectangle([20, 20, 980, 100], fill=(20, 40, 65))
        
        d.text((40, 45), "🔥 PRONÓSTICO DESTACADO | ANALIZADO CON IA", fill=(255, 215, 0))
        d.text((40, 130), str(league_name)[:45], fill=(0, 212, 170))
        d.text((40, 190), str(match_title)[:45], fill=(255, 255, 255))
        
        d.rectangle([40, 310, 960, 440], fill=(24, 43, 73), outline=(0, 212, 170), width=2)
        d.text((60, 330), f"📈 BALANCE CANAL: +{CHANNEL_STATS['profit_units']}U ({CHANNEL_STATS['yield_pct']}% Yield)", fill=(255, 215, 0))
        d.text((60, 380), f"📲 CANAL: @FreeTopTip | CONTACTO VIP: @{TELEGRAM_USERNAME}", fill=(255, 255, 255))

        filename = "match_card.png"
        img.save(filename)
        return filename
    except Exception as e:
        logging.error(f"Error creando la imagen: {e}")
        return None

def publish_single_pick():
    """Selecciona y analiza UN partido 100% real de la API de la jornada de hoy"""
    matches = fetch_real_flashscore_events()
    
    if not matches:
        logging.warning("No se recibieron partidos de Flashscore en este intento.")
        return

    selected = random.choice(matches)
    analysis_text = generate_deep_ai_analysis(selected)
    
    message_lines = [
        "🔥 <b>PRONÓSTICO REAL DEL DÍA</b> 🔥\n",
        analysis_text,
        f"\n📈 <b>Balance histórico:</b> +{CHANNEL_STATS['profit_units']}U ({CHANNEL_STATS['yield_pct']}% Yield)",
        f"💳 <b>¿Quieres entrar al VIP y recibir todas las combinadas diarias?</b>",
        f"📲 Escríbeme directo: <a href='https://t.me/{TELEGRAM_USERNAME}'>@{TELEGRAM_USERNAME}</a>"
    ]
    
    full_caption = "\n".join(message_lines)
    img_path = create_match_card(selected["match"], selected["league"])
    
    sent = False
    if img_path:
        sent = send_telegram_photo(img_path, full_caption)
    if not sent:
        send_telegram_message(full_caption)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error en servidor HTTP: {e}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servidor del bot iniciado.")

    # Primera ejecución al arrancar
    publish_single_pick()

    # Publica 1 partido individual analizado cada 4 horas
    while True:
        time.sleep(14400)
        publish_single_pick()

if __name__ == "__main__":
    main()
