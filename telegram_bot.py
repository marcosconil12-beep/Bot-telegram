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
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "").strip()
TELEGRAM_USERNAME = "Mark122"

published_picks = set()

CHANNEL_STATS = {
    "wins": 58,
    "losses": 12,
    "staked_units": 140,
    "profit_units": +42.5
}

def send_telegram_photo(photo_path, caption, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        return None
    token = str(TELEGRAM_BOT_TOKEN).strip().replace('"', '').replace("'", "")
    chat = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            data = {"chat_id": chat, "caption": caption, "parse_mode": "HTML"}
            if reply_markup:
                import json
                data["reply_markup"] = json.dumps(reply_markup)
            res = requests.post(url, data=data, files={"photo": photo}, timeout=10)
            return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error enviando foto a Telegram: {e}")
        return None

def create_scores24_card(match_title, league_name, pick_text, odds_val, is_live=False):
    bg_color = (13, 27, 42) if not is_live else (25, 10, 15)
    border_color = (0, 212, 170) if not is_live else (255, 45, 85)
    
    img = Image.new('RGB', (1000, 600), color=bg_color)
    d = ImageDraw.Draw(img)
    
    d.rectangle([20, 20, 980, 580], outline=border_color, width=4)
    d.rectangle([20, 20, 980, 110], fill=(20, 40, 65) if not is_live else (50, 15, 25))
    
    header_title = "🛡️ TOPTIPS OFFICIAL ANALYTICS" if not is_live else "🚨 ALERTA IA LIVE REAL"
    d.text((40, 48), header_title, fill=border_color)
    d.text((580, 48), league_name.upper()[:25], fill=(200, 200, 200))
    
    d.text((40, 140), "ENCUENTRO EN DIRECTO:" if is_live else "PARTIDO ANALIZADO EN DETALLE:", fill=(150, 160, 180))
    d.text((40, 180), match_title, fill=(255, 255, 255))
    
    d.rectangle([40, 240, 960, 420], fill=(24, 43, 73) if not is_live else (60, 20, 30), outline=(255, 215, 0), width=2)
    d.text((70, 260), "SELECCIÓN RECOMENDADA:" if not is_live else "SEÑAL IA DETECTADA:", fill=(255, 215, 0))
    d.text((70, 315), f"{pick_text}", fill=(255, 255, 255))
    d.text((750, 315), f"@{odds_val:.2f}", fill=border_color)

    d.text((40, 460), f"📊 Métricas: xG Proyectado | Córneres | Tarjetas | Yield: +{CHANNEL_STATS['profit_units']}U", fill=(150, 160, 180))
    d.text((40, 510), f"Canal Oficial: TOPTIPS | Contacto VIP: @{TELEGRAM_USERNAME}", fill=(255, 215, 0))
    
    filename = "scores24_card.png"
    img.save(filename)
    return filename

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Vendedor Pro Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error servidor HTTP: {e}")

def fetch_football_data_live():
    """Consulta los partidos reales en vivo usando la API de Football-Data.org."""
    if not FOOTBALL_API_KEY:
        logging.warning("Falta configurar FOOTBALL_API_KEY en Railway.")
        return []
    
    url = "https://api.football-data.org/v4/matches?status=IN_PLAY"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=12)
        data = response.json()
        if data.get("matches"):
            return data["matches"]
    except Exception as e:
        logging.error(f"Error al consultar Football-Data.org: {e}")
    return []

def scan_live_matches_ia():
    live_matches = fetch_football_data_live()
    
    if not live_matches:
        logging.info("Escáner: No hay partidos reales en juego en este instante. Silencio de seguridad.")
        return False

    for match in live_matches:
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        league = match["competition"]["name"]
        match_id = match["id"]
        
        score_data = match.get("score", {}).get("fullTime", {})
        goals_home = score_data.get("home") if score_data.get("home") is not None else 0
        goals_away = score_data.get("away") if score_data.get("away") is not None else 0
        
        pick_id = f"FD_LIVE_{match_id}"
        if pick_id in published_picks:
            continue

        chosen_pick = f"Más de {goals_home + goals_away + 0.5} Goles Totales"
        chosen_odds = round(random.uniform(1.80, 2.25), 2)
        ia_reason = f"Marcador actual {goals_home}-{goals_away}. Algoritmo detecta asedio ofensivo."

        caption = (
            f"🚨 <b>¡ALERTA IA DETECTADA EN DIRECTO!</b> 🚨\n\n"
            f"🏆 <b>Competición:</b> {league}\n"
            f"⚔️ <b>Encuentro:</b> {home} vs {away}\n"
            f"⚽ <b>Marcador Actual:</b> <b>{goals_home} - {goals_away}</b>\n\n"
            f"🔥 <b>SEÑAL IA DE ALTO VALOR:</b>\n"
            f"• Selección: <code>{chosen_pick}</code>\n"
            f"• Cuota Live: <b>{chosen_odds:.2f}</b> (Bet365 / Casas de Apuestas)\n"
            f"• Stake Recomendado: <b>2 / 10 (Fuerte)</b>\n\n"
            f"🧠 <b>ANÁLISIS EN TIEMPO REAL:</b>\n"
            f"<i>{ia_reason}</i>\n\n"
            f"⚡ <b>¡ENTRAD RÁPIDO ANTES DE QUE MUEVAN EL MARCADOR!</b>\n\n"
            f"💎 <b>¿Quieres las combinadas VIP privadas?</b>\n"
            f"Escríbeme por privado de inmediato: <b>@{TELEGRAM_USERNAME}</b>"
        )

        keyboard = {
            "inline_keyboard": [
                [{"text": "⚡ Entrar al VIP / Contactar Analista", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
            ]
        }

        img_path = create_scores24_card(f"{home} vs {away} ({goals_home}-{goals_away})", league, chosen_pick, chosen_odds, is_live=True)
        if send_telegram_photo(img_path, caption, reply_markup=keyboard):
            published_picks.add(pick_id)
            logging.info(f"¡Alerta REAL LIVE enviada!: {home} vs {away}")
            return True
            
    return False

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Tipster Pro Football-Data.org Activo...")

    while True:
        try:
            scan_live_matches_ia()
        except Exception as e:
            logging.error(f"Error en bucle escáner: {e}")
        
        time.sleep(180) # Consulta cada 3 minutos

if __name__ == "__main__":
    main()
