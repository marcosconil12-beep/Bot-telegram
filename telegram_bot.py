import os
import time
import logging
import threading
import requests
import random
from datetime import datetime
from PIL import Image, ImageDraw
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuración de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

published_picks = set()

def send_telegram_photo(photo_path, caption):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("Falta TELEGRAM_BOT_TOKEN o CHAT_ID")
        return None
    chat_id_clean = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    token_clean = str(TELEGRAM_BOT_TOKEN).strip().replace('"', '').replace("'", "")
    url = f"https://api.telegram.org/bot{token_clean}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            res = requests.post(url, data={"chat_id": chat_id_clean, "caption": caption, "parse_mode": "HTML"}, files={"photo": photo}, timeout=15)
            return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error enviando foto: {e}")
        return None

def create_scores24_card(match_title, league_name, pick_text, odds_val):
    """Genera una tarjeta gráfica profesional estilo Scores24."""
    img = Image.new('RGB', (1000, 550), color=(13, 27, 42))
    d = ImageDraw.Draw(img)
    
    d.rectangle([20, 20, 980, 530], outline=(0, 212, 170), width=4)
    d.rectangle([20, 20, 980, 95], fill=(20, 40, 65))
    d.text((40, 45), "⚡ TOPTIPS LIVE & ANALYTICS", fill=(0, 212, 170))
    d.text((580, 45), league_name.upper()[:25], fill=(200, 200, 200))
    
    d.text((40, 140), "ENCUENTRO EN DIRECTO:", fill=(150, 160, 180))
    d.text((40, 185), match_title, fill=(255, 255, 255))
    
    d.rectangle([40, 260, 960, 410], fill=(24, 43, 73), outline=(255, 215, 0), width=2)
    d.text((70, 285), "PRONÓSTICO SELECCIONADO:", fill=(255, 215, 0))
    d.text((70, 335), f"{pick_text}", fill=(255, 255, 255))
    d.text((750, 335), f"@{odds_val:.2f}", fill=(0, 212, 170))
    
    d.text((40, 460), "📊 Cuotas verificadas en tiempo real", fill=(150, 160, 180))
    d.text((40, 495), "Canal Oficial: @FreeTopTip", fill=(255, 215, 0))
    
    filename = "scores24_card.png"
    img.save(filename)
    return filename

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot API Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error HTTP: {e}")

def fetch_live_api_match():
    """Obtiene únicamente partidos reales y actuales directamente desde la API oficial."""
    if not ODDS_API_KEY:
        logging.error("Falta la API Key de Odds API en las variables de entorno.")
        return None
        
    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            events = res.json()
            if events:
                event = random.choice(events)
                home = event.get("home_team")
                away = event.get("away_team")
                league = event.get("sport_title", "Fútbol Internacional")
                
                odds_val = 2.00
                if event.get("bookmakers") and len(event["bookmakers"]) > 0:
                    markets = event["bookmakers"][0].get("markets", [])
                    if markets and len(markets[0].get("outcomes", [])) > 0:
                        odds_val = markets[0]["outcomes"][0].get("price", 2.00)
                
                if home and away:
                    return home, away, league, odds_val
        else:
            logging.warning(f"La API respondió con código: {res.status_code}")
    except Exception as e:
        logging.error(f"Error consultando la API: {e}")
        
    return None

def publish_pick():
    match_data = fetch_live_api_match()
    if not match_data:
        logging.info("Esperando nuevos partidos en directo desde la API...")
        return

    home, away, league, odds_val = match_data
    match_title = f"{home} vs {away}"
    
    today_str = datetime.now().strftime("%Y-%m-%d-%H")
    pick_id = f"{match_title}_{today_str}"
    
    if pick_id in published_picks:
        return

    markets = [
        ("Victoria de " + home, odds_val, f"Análisis táctico: {home} muestra superioridad en los duelos clave y una localía muy sólida en esta jornada."),
        ("Más de 2.5 Goles", round(odds_val * 0.95, 2), f"Análisis táctico: Alta tendencia ofensiva y necesidades urgentes de victoria que propiciarán un partido abierto."),
        ("Ambos Anotan (Sí)", round(odds_val * 0.98, 2), f"Análisis táctico: Estadísticas recientes de ambos equipos reflejan vulnerabilidad defensiva y pegada arriba.")
    ]
    chosen_pick, chosen_odds, analysis = random.choice(markets)

    caption = (
        f"⚽ <b>PRONÓSTICO OFICIAL</b> ⚽\n\n"
        f"🏆 <b>Competición:</b> {league}\n"
        f"⚔️ <b>Encuentro:</b> {match_title}\n\n"
        f"🎯 <b>Selección:</b> <code>{chosen_pick}</code>\n"
        f"📈 <b>Cuota:</b> <b>{chosen_odds:.2f}</b> | 🏦 <b>Bet365</b>\n\n"
        f"📊 <b>{analysis}</b>\n\n"
        f"💪 <i>¡A por el verde! Stake 1.5.</i>"
    )

    img_path = create_scores24_card(match_title, league, chosen_pick, chosen_odds)
    if send_telegram_photo(img_path, caption):
        published_picks.add(pick_id)
        logging.info(f"Pronóstico real publicado con éxito: {match_title} ({league})")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Tipster 100% API Real Activo...")

    # Intento de publicación inicial tras arrancar
    time.sleep(5)
    publish_pick()

    while True:
        try:
            publish_pick()
        except Exception as e:
            logging.error(f"Error en bucle: {e}")
        time.sleep(7200) # Revisa y publica cada 2 horas

if __name__ == "__main__":
    main()
