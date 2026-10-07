import os
import time
import logging
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuración de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
FOOTBALL_DATA_KEY = os.environ.get("FOOTBALL_DATA_KEY")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

API_URL = "https://api.football-data.org/v4/matches"
HEADERS = {
    "X-Auth-Token": FOOTBALL_DATA_KEY
}

# Servidor HTTP en segundo plano para Render
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("TELEGRAM_BOT_TOKEN o CHAT_ID no configurados.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, json=payload)
        res.raise_for_status()
    except Exception as e:
        logging.error(f"Error enviando mensaje a Telegram: {e}")

def get_live_fixtures():
    # Consulta los partidos que están en directo (status IN_PLAY o PAUSED)
    url = f"{API_URL}?status=IN_PLAY"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            return data.get("matches", [])
        else:
            logging.error(f"Error API Football-Data: {response.status_code}")
            return []
    except Exception as e:
        logging.error(f"Error consultando Football-Data: {e}")
        return []

def check_live_alerts():
    matches = get_live_fixtures()
    for match in matches:
        home_team = match["homeTeam"]["name"]
        away_team = match["awayTeam"]["name"]
        
        score = match.get("score", {}).get("fullTime", {})
        home_goals = score.get("home", 0) or 0
        away_goals = score.get("away", 0) or 0
        
        competition = match.get("competition", {}).get("name", "Liga")

        # Filtro: total de goles en el partido <= 1
        if (home_goals + away_goals) <= 1:
            msg = (
                f"🚨 <b>ALERTA EN DIRECTO</b> 🚨\n\n"
                f"🏆 <b>{competition}</b>\n"
                f"⚽ <b>{home_team} vs {away_team}</b>\n"
                f"📊 Marcador actual: {home_goals} - {away_goals}\n\n"
                f"🔥 ¡Oportunidad detectada!"
            )
            send_telegram_message(msg)

def main():
    # Servidor HTTP para evitar errores en Render
    threading.Thread(target=run_http_server, daemon=True).start()
    
    logging.info("Bot iniciado con Football-Data...")
    send_telegram_message("🤖 Bot actualizado a Football-Data y activo monitoreando partidos sin límites.")
    
    while True:
        try:
            check_live_alerts()
        except Exception as e:
            logging.error(f"Error en el bucle principal: {e}")
        
        # Revisa cada 3 minutos sin agotar el límite
        time.sleep(180)

if __name__ == "__main__":
    main()
