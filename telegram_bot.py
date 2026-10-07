import os
import time
import logging
import threading
import requests
from http.server import SimpleHTTPRequestHandler, HTTPServer

# Desactivar advertencias de certificados SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Variables de entorno de Render
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
FOOTBALL_DATA_KEY = os.environ.get("FOOTBALL_DATA_KEY")

API_URL = "https://football-data.org"
HEADERS = {
    "X-Auth-Token": str(FOOTBALL_DATA_KEY).strip() if FOOTBALL_DATA_KEY else ""
}

class SimpleHTTPRequestHandlerCustom(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandlerCustom)
    logging.info(f"Servidor HTTP corriendo en el puerto {port}")
    server.serve_forever()

def get_live_fixtures():
    if not FOOTBALL_DATA_KEY:
        return []
    url = f"{API_URL}?status=LIVE"
    try:
        response = requests.get(url, headers=HEADERS, verify=False)
        if response.status_code == 200:
            return response.json().get("matches", [])
        return []
    except Exception:
        return []

def check_live_alerts():
    matches = get_live_fixtures()
    for match in matches:
        home_team = match.get("homeTeam", {}).get("name", "Local")
        away_team = match.get("awayTeam", {}).get("name", "Visitante")
        score = match.get("score", {}).get("fullTime", {})
        home_goals = score.get("home", 0)
        away_goals = score.get("away", 0)
        competition = match.get("competition", {}).get("name", "Liga")
        
        mensaje_partido = (
            f"⚽ <b>ALERTA EN DIRECTO</b> ⚽\n\n"
            f"🏆 Competencia: {competition}\n"
            f"⚔️ {home_team} vs {away_team}\n"
            f"📊 Marcador actual: {home_goals} - {away_goals}\n"
        )
        # Envío directo simplificado
        url = "https://telegram.org"
        requests.post(url, json={"chat_id": str(CHAT_ID).strip(), "text": mensaje_partido, "parse_mode": "HTML"})

def main_loop():
    # ENVÍO INMEDIATO AL ARRANCAR (Sin funciones intermedias)
    url_directa = "https://telegram.org"
    payload_arranque = {
        "chat_id": str(CHAT_ID).strip(),
        "text": "🤖 Bot actualizado y activo monitoreando partidos sin límite.",
        "parse_mode": "HTML"
    }
    
    try:
        logging.info("Forzando envío de mensaje de arranque a Telegram...")
        r = requests.post(url_directa, json=payload_arranque)
        logging.info(f"Respuesta de Telegram: {r.status_code} - {r.text}")
    except Exception as e:
        logging.error(f"Error crítico en envío directo: {e}")

    while True:
        try:
            check_live_alerts()
        except Exception as e:
            logging.error(f"Error en el ciclo de monitoreo: {e}")
        time.sleep(90)

if __name__ == "__main__":
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    main_loop()
