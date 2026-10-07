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
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

API_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": API_FOOTBALL_KEY
}

# Registro en memoria para no repetir alertas del mismo partido
sent_alerts = set()

# Servidor HTTP para cumplir el requisito de Render
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
        logging.info("Mensaje enviado con éxito a Telegram.")
    except Exception as e:
        logging.error(f"Error enviando mensaje a Telegram: {e}")

def get_live_fixtures():
    url = f"{API_URL}/fixtures?live=all"
    try:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        return data.get("response", [])
    except Exception as e:
        logging.error(f"Error consultando API-Football: {e}")
        return []

def check_live_alerts():
    fixtures = get_live_fixtures()
    logging.info(f"Partidos en vivo detectados por API-Football: {len(fixtures)}")
    
    for fix in fixtures:
        fixture_id = fix["fixture"]["id"]
        
        # Evitar enviar alerta duplicate si ya se notificó este partido
        if fixture_id in sent_alerts:
            continue

        elapsed = fix["fixture"]["status"]["elapsed"] or 0
        league_name = fix["league"]["name"]
        teams = fix["teams"]
        goals = fix["goals"]
        
        home_team = teams["home"]["name"]
        away_team = teams["away"]["name"]
        home_goals = goals["home"] or 0
        away_goals = goals["away"] or 0

        # Criterio: Minuto entre 30 y 75 y total de goles <= 1
        if 30 <= elapsed <= 75 and (home_goals + away_goals) <= 1:
            msg = (
                f"🚨 <b>ALERTA EN DIRECTO</b> 🚨\n\n"
                f"🏆 <b>{league_name}</b>\n"
                f"⚽ <b>{home_team} vs {away_team}</b>\n"
                f"⏱ Minuto: {elapsed}' | Resultado: {home_goals} - {away_goals}\n\n"
                f"🔥 ¡Oportunidad detectada para buscar gol!"
            )
            send_telegram_message(msg)
            sent_alerts.add(fixture_id)

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    
    logging.info("Bot configurado con API-Football iniciado...")
    
    while True:
        try:
            check_live_alerts()
        except Exception as e:
            logging.error(f"Error en el bucle principal: {e}")
        
        # Consultar cada 15 minutos (96 peticiones al día = 100% gratis)
        time.sleep(900)

if __name__ == "__main__":
    main()
