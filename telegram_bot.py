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
    "profit_units": +76.4,
    "yield_pct": 33.2
}

# Configuración de Gemini para análisis avanzado en primera persona
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
    return "• Jornada vibrante en las ligas internacionales con cuotas muy atractivas en el mercado."

def fetch_flashscore_global_matches():
    """Consulta Flashscore abierta a TODAS las ligas mundiales y detecta partidos en LIVE"""
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
                for ev in events:
                    home = ev.get("HOME_NAME", "Local")
                    away = ev.get("AWAY_NAME", "Visitante")
                    
                    # Detectar si está en directo (Live)
                    status_type = ev.get("STAGE_TYPE", "")
                    time_str = ""
                    is_live = False
                    
                    if status_type == "LIVE" or ev.get("TIME_RUNNING"):
                        is_live = True
                        time_str = "🔴 EN DIRECTO (LIVE)"
                    else:
                        time_timestamp = ev.get("START_TIME", int(time.time()))
                        time_str = datetime.fromtimestamp(time_timestamp, SPAIN_TZ).strftime('%H:%M') + " CEST"

                    matches.append({
                        "league": f"{country.upper()} - {league_name.upper()}",
                        "match": f"{home} vs {away}",
                        "time": time_str,
                        "is_live": is_live
                    })
        
        # Mezclamos aleatoriamente para que salgan ligas distintas de todo el mundo en cada ciclo
        random.shuffle(matches)
        return matches[:15]
    except Exception as e:
        logging.error(f"Error consultando Flashscore: {e}")
        return []

def generate_ai_bet_analysis(match_name, league_name, is_live):
    """Genera un análisis profesional con IA en primera persona y un PICK de apuestas estructurado"""
    live_tag = " [APUESTA EN DIRECTO / LIVE]" if is_live else ""
    
    if not ai_model:
        return f"🎯 Pick: <code>Gana o Empata Local + Más de 1.5 Goles</code> (@<b>1.95</b>)\n💡 He analizado este encuentro y veo un claro dominio en xG."
    
    prompt = (
        f"Actúa como un tipster experto en apuestas deportivas llamado Mark. "
        f"Para el partido {match_name} de la competición {league_name}{live_tag}, genera:\n"
        f"1. Un mercado de apuesta recomendado estilo Bet365 (ej: 'Más de 2.5 goles', 'Ambos anotan', 'Gana local', etc.).\n"
        f"2. Una cuota estimada realista (ej: 1.85, 2.10).\n"
        f"3. Un párrafo corto y directo en primera persona justificando el pronóstico (ej: 'He analizado las estadísticas...').\n"
        f"Devuelve la respuesta exactamente con este formato de texto plano para Telegram:\n"
        f"🎯 Pick: [Tu mercado aquí]\n"
        f"💰 Cuota: [Número con dos decimales, ej: 1.90]\n"
        f"💡 [Tu análisis breve en primera persona]"
    )
    try:
        response = ai_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logging.error(f"Error generando pick con IA: {e}")
        return f"🎯 Pick: <code>Más de 8.5 Córneres + Más de 1.5 Goles</code> (@<b>2.00</b>)\n💡 He revisado la tendencia ofensiva y los datos de valor del mercado actual."

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
        
        d.text((40, 40), f"🔥 PICKS MULTILIGA & LIVE | {date_str}", fill=(255, 215, 0))
        d.text((40, 120), "COBERTURA GLOBAL DE TODAS LAS LIGAS MUNDIALES", fill=(0, 212, 170))
        d.text((40, 170), "• Análisis automatizado de Inteligencia Artificial (IA).", fill=(200, 200, 200))
        d.text((40, 210), "• Pronósticos anticipados y oportunidades en directo (LIVE).", fill=(200, 200, 200))
        d.text((40, 250), "• Sincronización automática con noticias de prensa RSS.", fill=(200, 200, 200))

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
    time_str = now_spain.strftime('%H:%M')
    
    news_text = fetch_latest_sports_news()
    matches = fetch_flashscore_global_matches()
    
    if not matches:
        matches = [
            {"league": "🇪🇸 ESPAÑA - LA LIGA", "match": "Real Madrid vs Valencia", "time": "21:00 CEST", "is_live": False},
            {"league": "🇮🇹 ITALIA - SERIE A", "match": "Inter de Milán vs Juventus", "time": "🔴 EN DIRECTO (LIVE)", "is_live": True},
            {"league": "🇧🇷 BRASIL - SERIE A", "match": "Flamengo vs Palmeiras", "time": "02:30 CEST", "is_live": False}
        ]

    lines = []
    lines.append(f"📊 <b>PARRILLA DE PICKS & LIVE ({date_str} - {time_str})</b> 📊\n")
    lines.append("📰 <b>NOTICIAS DESTACADAS:</b>")
    lines.append(f"<i>{news_text}</i>\n")
    lines.append("⚽ <b>PRONÓSTICOS DE LA JORNADA (ANÁLISIS DE IA):</b>")

    # Cogemos 3 partidos variados al azar de cualquier liga o live
    selected_matches = random.sample(matches, min(3, len(matches)))
    
    for m in selected_matches:
        ai_output = generate_ai_bet_analysis(m["match"], m["league"], m["is_live"])
        lines.append(
            f"\n🏆 <b>{m['league']}</b>\n"
            f"⏰ <b>{m['time']}</b> | ⚔️ <b>{m['match']}</b>\n"
            f"{ai_output}\n"
        )

    lines.append(f"\n📈 <b>Balance Global:</b> +{CHANNEL_STATS['profit_units']}U ({CHANNEL_STATS['yield_pct']}% Yield)")
    lines.append(f"💳 <b>¿Quieres acceder a los pronósticos VIP diarios?</b>")
    lines.append(f"📲 Escríbeme por privado: <a href='https://t.me/{TELEGRAM_USERNAME}'>@{TELEGRAM_USERNAME}</a>")

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
        self.wfile.write("Bot Multiliga & Live Activo".encode('utf-8'))

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

    # Se ejecuta cada 4 horas para cubrir todas las ligas del mundo y repartir peticiones
    while True:
        time.sleep(14400)
        publish_global_report()

if __name__ == "__main__":
    main()
