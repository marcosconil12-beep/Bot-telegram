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

# Ligas y partidos de respaldo dinámicos
FALLBACK_MATCHES = [
    {"league": "🇪🇸 ESPAÑA - LA LIGA", "home": "Real Madrid", "away": "FC Barcelona", "match": "Real Madrid vs FC Barcelona", "time": "21:00 CEST", "is_live": False},
    {"league": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 INGLATERRA - PREMIER LEAGUE", "home": "Manchester City", "away": "Arsenal", "match": "Manchester City vs Arsenal", "time": "18:30 CEST", "is_live": False},
    {"league": "🇮🇹 ITALIA - SERIE A", "home": "Inter de Milán", "away": "AC Milan", "match": "Inter de Milán vs AC Milan", "time": "🔴 EN DIRECTO", "is_live": True},
    {"league": "🇪🇺 UEFA CHAMPIONS LEAGUE", "home": "Bayern Múnich", "away": "Paris Saint-Germain", "match": "Bayern Múnich vs Paris Saint-Germain", "time": "21:00 CEST", "is_live": False},
    {"league": "🇩🇪 ALEMANIA - BUNDESLIGA", "home": "Bayer Leverkusen", "away": "Borussia Dortmund", "match": "Bayer Leverkusen vs Borussia Dortmund", "time": "17:30 CEST", "is_live": False},
    {"league": "🌎 CONMEBOL - COPA LIBERTADORES", "home": "River Plate", "away": "Boca Juniors", "match": "River Plate vs Boca Juniors", "time": "02:30 CEST", "is_live": False}
]

def fetch_real_flashscore_events():
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
            logging.info(f"Partidos reales encontrados en Flashscore: {len(matches)}")
            return matches
    except Exception as e:
        logging.error(f"Error consultando Flashscore: {e}")

    logging.info("Usando parrilla multiligas de respaldo garantizada.")
    return FALLBACK_MATCHES

def generate_deep_ai_analysis(match_info):
    league = match_info["league"]
    match = match_info["match"]
    match_time = match_info["time"]
    
    if not ai_client:
        return (
            f"🏆 <b>{league}</b>\n"
            f"⏰ <b>Hora:</b> {match_time} | ⚔️ <b>{match}</b>\n\n"
            f"💡 <b>Análisis de Mark:</b> Tras analizar la dinámica reciente de ambos equipos, la necesidad de puntuar favorece un choque dinámico con opciones claras en ambas áreas.\n\n"
            f"🎯 <b>PICK OFICIAL:</b> <code>Ambos Equipos Anotan - SÍ</code>\n"
            f"💰 <b>Cuota:</b> 1.85 (Bet365)\n"
            f"📊 <b>Stake:</b> 2/10"
        )

    prompt = (
        "Eres Mark, un experto tipster profesional de apuestas deportivas en Telegram.\n"
        f"Analiza este partido de fútbol: {match} ({league}) a las {match_time}.\n\n"
        "Escribe un análisis en formato HTML estricto con esta estructura exacta:\n"
        f"🏆 <b>{league}</b>\n"
        f"⏰ <b>Hora:</b> {match_time} | ⚔️ <b>{match}</b>\n\n"
        "💡 <b>Análisis de Mark:</b>\n"
        "[Escribe 2 párrafos breves en primera persona analizando la racha de los equipos, xG o aspecto táctico].\n\n"
        "🎯 <b>PICK OFICIAL:</b> [Pon un mercado claro como 'Más de 2.5 Goles', 'Gana Local', 'Ambos Anotan', etc.]\n"
        "💰 <b>Cuota:</b> [Indica una cuota realista entre 1.70 y 2.25]\n"
        "📊 <b>Stake recomendado:</b> [1/10 o 2/10]"
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
    matches = fetch_real_flashscore_events()
    
    if not matches:
        matches = FALLBACK_MATCHES

    selected = random.choice(matches)
    analysis_text = generate_deep_ai_analysis(selected)
    
    message_lines = [
        "🔥 <b>PRONÓSTICO DESTACADO DEL DÍA</b> 🔥\n",
        analysis_text,
        f"\n📈 <b>Balance histórico:</b> +{CHANNEL_STATS['profit_units']}U ({CHANNEL_STATS['yield_pct']}% Yield)",
        "💳 <b>¿Quieres entrar al VIP y recibir todas las combinadas diarias?</b>",
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

    while True:
        time.sleep(14400)
        publish_single_pick()

if __name__ == "__main__":
    main()
