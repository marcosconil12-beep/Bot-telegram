import os
import time
import logging
import threading
import requests
from http.server import SimpleHTTPRequestHandler, HTTPServer

# Desactivar advertencias de certificados SSL no verificados de la API
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# CORREGIDO: Llamada directa a tus nombres exactos de Render
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
FOOTBALL_DATA_KEY = os.environ.get("FOOTBALL_DATA_KEY")  # USA TU CLAVE DIRECTAMENTE

API_URL = "https://api.football-data.org/v4/matches"
HEADERS = {
    "X-Auth-Token": FOOTBALL_DATA_KEY
}

# Servidor HTTP en segundo plano para Render
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
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("TELEGRAM_BOT_TOKEN o CHAT_ID no están configurados.")
        return
    
    # CORRECCIÓN DE EMERGENCIA: Limpia espacios o caracteres invisibles que causan el fallo del host
    token_limpio = TELEGRAM_BOT_TOKEN.strip().replace(" ", "")
    url = f"https://telegram.org{token_limpio}/sendMessage"
    payload = {
        "chat_id": CHAT_ID.strip(),
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        res = requests.post(url, json=payload)
        res.raise_for_status()
    except Exception as e:
        logging.error(f"Error enviando mensaje a Telegram: {e}")

def get_live_fixtures():
    url = f"{API_URL}?status=LIVE"
    try:
        response = requests.get(url, headers=HEADERS, verify=False)
        if response.status_code == 200:
            data = response.json()
            return data.get("matches", [])
        else:
            logging.error(f"Error API Football-Data: {response.status_code} - Verifica que tu clave de football-data sea correcta.")
            return []
    except Exception as e:
        logging.error(f"Error consultando Football-Data: {e}")
        return []

def check_live_alerts():
    matches = get_live_fixtures()
    if not matches:
        logging.info("No hay partidos en vivo en este momento.")
        return

    for match in matches:
        home_team = match.get("homeTeam", {}).get("name", "Local")
        away_team = match.get("awayTeam", {}).get("name", "Visitante")
        
        score = match.get("score", {}).get("fullTime", {})
        home_goals = score.get("home", 0)
        away_goals = score.get("away", 0)
        
        competition = match.get("competition", {}).get("name", "Liga")
        
        mensaje = (
            f"⚽ <b>ALERTA EN DIRECTO</b> ⚽\n\n"
            f"🏆 Competencia: {competition}\n"
            f"⚔️ {home_team} vs {away_team}\n"
            f"📊 Marcador actual: {home_goals} - {away_goals}\n"
        )
        send_telegram_message(mensaje)

def main_loop():
    send_telegram_message("🤖 Bot actualizado y activo monitoreando partidos sin límite.")
    while True:
        try:
            check_live_alerts()
        except Exception as e:
            logging.error(f"Error en el ciclo de monitoreo: {e}")
        
        time.sleep(60)

if __name__ == "__main__":
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    main_loop()
