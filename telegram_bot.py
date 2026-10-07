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

# URL REAL DE LA API DE FÚTBOL
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

def send_telegram_message(text):
    if not CHAT_ID:
        logging.error("TELEGRAM_CHAT_ID no está configurado.")
        return
    
    # URL REAL DE TELEGRAM CON TU TOKEN
    url_telegram = "https://telegram.org"
    payload = {
        "chat_id": str(CHAT_ID).strip(),
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        res = requests.post(url_telegram, json=payload)
        logging.info(f"Respuesta envío Telegram: {res.status_code}")
    except Exception as e:
        logging.error(f"Error enviando mensaje a Telegram: {e}")

def get_live_fixtures():
    url_futbol = f"{API_URL}?status=LIVE"
    try:
        response = requests.get(url_futbol, headers=HEADERS, verify=False)
        if response.status_code == 200:
            return response.json().get("matches", [])
        else:
            logging.error(f"API Fútbol respondió con código: {response.status_code}")
            return []
    except Exception as e:
        logging.error(f"Error conectando a la API de fútbol: {e}")
        return []

def check_live_alerts():
    matches = get_live_fixtures()
    if not matches:
        logging.info("No se encontraron partidos en vivo en esta consulta.")
        return

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
        send_telegram_message(mensaje_partido)

def main_loop():
    # Mandamos el aviso de arranque inmediatamente a tu canal
    time.sleep(2)
    send_telegram_message("🤖 Bot actualizado y activo monitoreando partidos sin límite.")
    
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
