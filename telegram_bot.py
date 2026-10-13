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
import google.generativeai as genai

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
RAPIDAPI_KEY = clean_env("RAPIDAPI_KEY", "")
GEMINI_API_KEY = clean_env("GEMINI_API_KEY", "")
TELEGRAM_USERNAME = "Mark122"

SPAIN_TZ = ZoneInfo("Europe/Madrid")

CHANNEL_STATS = {
    "profit_units": +74.2,
    "yield_pct": 32.1
}

# Configuración de Gemini para análisis en primera persona
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    ai_model = None

# Feeds RSS deportivos gratuitos para noticias de última hora
RSS_FEEDS = [
    "https://as.com/rss/futbol/portada.xml",
    "https://e00-marca.uecdn.es/rss/futbol/champions-league.xml",
    "https://www.mundodeportivo.com/rss/futbol.xml"
]

def fetch_latest_sports_news():
    """Extrae noticias frescas de los RSS deportivos"""
    headlines = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:2]:
                title = entry.get("title", "").strip()
                if title and len(title) > 15:
                    headlines.append(f"• {title}")
        except Exception as e:
            logging.error(f"Error en RSS {feed_url}: {e}")
    if headlines:
        return "\n".join(headlines[:3])
    return "• Jornada vibrante en las principales ligas y competiciones internacionales."

def fetch_flashscore_global_matches():
    """Consulta Flashscore optimizada para gastar pocas peticiones al mes (aprox 15 al día)"""
    if not RAPIDAPI_KEY:
        return []
    
    url = "https://flashlive-sports.p.rapidapi.com/v1/events/list"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
    }
    params = {"sport_id": "1", "indent_days": "0", "locale": "es_ES"}
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=12)
        data = res.json()
        matches = []
        if "DATA" in data:
            for tournament in data["DATA"]:
                league_name = tournament.get("TOURNAMENT_NAME", "Liga Internacional")
                country = tournament.get("COUNTRY_NAME", "Global")
                events = tournament.get("EVENTS", [])
                for ev in events[:2]:
                    home = ev.get("HOME_NAME", "Local")
                    away = ev.get("AWAY_NAME", "Visitante")
                    time_timestamp = ev.get("START_TIME", int(time.time()))
                    match_time = datetime.fromtimestamp(time_timestamp, SPAIN_TZ).strftime('%H:%M')
                    matches.append({
                        "league": f"{country.upper()} - {league_name.upper()}",
                        "match": f"{home} vs {away}",
                        "time": f"{match_time} CEST"
                    })
        return matches[:12]
    except Exception as e:
        logging.error(f"Error consultando Flashscore: {e}")
        return []

def generate_ai_analysis(match_name, league_name):
    """Genera análisis profesional en primera persona usando Gemini"""
    if not ai_model:
        return f"He analizado detenidamente este {match_name} de {league_name}. Veo claros patrones de valor en los mercados de goles y saques de esquina según las estadísticas recientes."
    
    prompt = (
        f"Actúa como un tipster experto en apuestas deportivas llamado Mark. "
        f"Redacta un análisis profesional y directo en primera persona (ej: 'He analizado...', 'Veo valor en...') "
        f"para el partido {match_name} de la competición {league_name}. "
        f"Menciona claves tácticas, xG o tendencia de mercado en Bet365 en un párrafo corto y persuasivo."
    )
    try:
        response = ai_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logging.error(f"Error generando análisis con IA: {e}")
        return f"He revisado las estadísticas de este {match_name}. Las métricas ofensivas y el rendimiento reciente nos dejan cuotas muy atractivas para buscar valor."

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        res = requests.post(url, json=payload, timeout=15)
        return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error Telegram Message: {e}")
        return False

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}
            res = requests.post(url, data=data, files={"photo": photo}, timeout=20)
            return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error Telegram Photo: {e}")
        return False

def create_summary_card(date_str):
    try:
        img = Image.new('RGB', (1000, 500), color=(13, 27, 42))
        d = ImageDraw.Draw(img)
        
        d.rectangle([20, 20, 980, 480], outline=(0, 212, 170), width=4)
        d.rectangle([20, 20, 980, 100], fill=(20, 40, 65))
        
        d.text((40, 40), f"🔥 ANÁLISIS GLOBAL DE LIGAS | {date_str}", fill=(255, 215, 0))
        d.text((40, 120), "EUROPA, LATINOAMÉRICA & ASIA (BET365)", fill=(0, 212, 170))
        d.text((40, 170), "• Inteligencia Artificial en primera persona aplicada al mercado.", fill=(200, 200, 200))
        d.text((40, 210), "• Cobertura multiligas con estadísticas de valor y xG.", fill=(200, 200, 200))
        d.text((40, 250), "• Noticias de última hora sincronizadas vía RSS.", fill=(200, 200, 200))

        d.rectangle([40, 310, 960, 440], fill=(24, 43, 73), outline=(0, 212, 170), width=2)
        d.text((60, 330), f"📈 RENDIMIENTO: +{CHANNEL_STATS['profit_units']}U ({CHANNEL_STATS['yield_pct']}% Yield)", fill=(255, 215, 0))
        d.text((60, 380), f"📲 CANAL: @FreeTopTip | VIP: @{TELEGRAM_USERNAME}", fill=(255, 255, 255))

        filename = "summary_card.png"
        img.save(filename)
        return filename
    except Exception as e:
        logging.error(f"Error creando tarjeta: {e}")
        return None

def publish_global_report():
    now_spain = datetime.now(SPAIN_TZ)
    date_str = now_spain.strftime('%d/%m/%Y')
    
    news_text = fetch_latest_sports_news()
    matches = fetch_flashscore_global_matches()
    
    if not matches:
        matches = [
            {"league": "🇪🇺 UEFA CHAMPIONS LEAGUE", "match": "Arsenal vs Lille", "time": "21:00 CEST"},
            {"league": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 INGLATERRA - CHAMPIONSHIP", "match": "Bristol City vs Blackburn", "time": "20:45 CEST"},
            {"league": "🌎 CONMEBOL - COPA SUDAMERICANA", "match": "Boca Juniors vs Vasco da Gama", "time": "02:30 CEST"}
        ]

    lines = []
    lines.append(f"📊 <b>INFORME EXPERTO Y MERCADOS ({date_str})</b> 📊\n")
    lines.append("📰 <b>NOTICIAS DESTACADAS DE LA JORNADA:</b>")
    lines.append(f"<i>{news_text}</i>\n")
    lines.append("⚽ <b>ANÁLISIS DE PARTIDOS DESTACADOS (IA):</b>")

    selected_matches = random.sample(matches, min(3, len(matches)))
    
    for m in selected_matches:
        analysis = generate_ai_analysis(m["match"], m["league"])
        lines.append(
            f"\n🏆 <b>{m['league']}</b>\n"
            f"⏰ <b>{m['time']}</b> | ⚔️ <b>{m['match']}</b>\n"
            f"💡 <i>{analysis}</i>\n"
        )

    lines.append(f"\n📈 <b>Balance Global:</b> +{CHANNEL_STATS['profit_units']}U ({CHANNEL_STATS['yield_pct']}% Yield)")
    lines.append(f"💳 <b>¿Quieres recibir las combinadas VIP exclusivas?</b>")
    lines.append(f"📲 Escríbeme al privado: <a href='https://t.me/{TELEGRAM_USERNAME}'>@{TELEGRAM_USERNAME}</a>")

    caption = "\n".join(lines)
    img_path = create_summary_card(date_str)

    sent = False
    if img_path:
        sent = send_telegram_photo(img_path, caption)
    if not sent:
        send_telegram_message(caption)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Global IA Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error servidor HTTP: {e}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servidor bot iniciado correctamente.")

    publish_global_report()

    while True:
        time.sleep(14400)
        publish_global_report()

if __name__ == "__main__":
    main()
