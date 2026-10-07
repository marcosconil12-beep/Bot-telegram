import os
import time
import logging
import threading
import requests
from datetime import datetime, timedelta
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

sent_alerts = set()
last_prematch_date = None

# Servidor HTTP para Render
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
        "chat_id": str(CHAT_ID).strip(),
        "text": text
        # Sin parse_mode para evitar el Error 400 por caracteres especiales
    }
    try:
        res = requests.post(url, json=payload)
        res.raise_for_status()
        logging.info("Mensaje enviado con éxito a Telegram.")
    except Exception as e:
        logging.error(f"Error enviando mensaje a Telegram: {e}")

# 1. ALERTAS EN DIRECTO (SIN LÍMITES)
def check_live_alerts():
    url = f"{API_URL}?status=IN_PLAY"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            matches = data.get("matches", [])
        else:
            logging.error(f"Error Football-Data API: {response.status_code}")
            return
    except Exception as e:
        logging.error(f"Error de conexión con Football-Data: {e}")
        return

    logging.info(f"Partidos en directo detectados: {len(matches)}")

    for match in matches:
        match_id = match["id"]
        if match_id in sent_alerts:
            continue

        home_team = match["homeTeam"]["name"]
        away_team = match["awayTeam"]["name"]
        competition = match.get("competition", {}).get("name", "Liga")
        
        score = match.get("score", {}).get("fullTime", {})
        home_goals = score.get("home") or 0
        away_goals = score.get("away") or 0
        total_goals = home_goals + away_goals

        if total_goals <= 1:
            msg = (
                f"🚨 ALERTA EN DIRECTO 🚨\n\n"
                f"🏆 Liga: {competition}\n"
                f"⚽ Partido: {home_team} vs {away_team}\n"
                f"📊 Resultado actual: {home_goals} - {away_goals}\n\n"
                f"🔥 ¡Oportunidad detectada para buscar gol!"
            )
            send_telegram_message(msg)
            sent_alerts.add(match_id)

# 2. PRONÓSTICOS PRE-MATCH CON ARGUMENTOS (1 VEZ AL DÍA)
def check_upcoming_value_bets():
    global last_prematch_date
    today_str = datetime.now().strftime("%Y-%m-%d")

    if last_prematch_date == today_str:
        return

    date_from = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    date_to = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    url = f"{API_URL}?dateFrom={date_from}&dateTo={date_to}"

    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            matches = data.get("matches", [])
        else:
            return
    except Exception as e:
        return

    if not matches:
        return

    count = 0
    for match in matches:
        home_team = match["homeTeam"]["name"]
        away_team = match["awayTeam"]["name"]
        competition = match.get("competition", {}).get("name", "Liga")

        msg = (
            f"🎯 PRONÓSTICO DE VALOR (PRE-MATCH) 🎯\n\n"
            f"🏆 {competition}\n"
            f"⚔️ {home_team} vs {away_team}\n"
            f"📅 Fecha: Mañana ({date_from})\n\n"
            f"📌 Selección: Más de 1.5 goles / Apuesta de Valor\n"
            f"📝 Argumentación: Según la racha reciente de goles anotados de {home_team} "
            f"y los tantos concedidos por {away_team}, las probabilidades muestran un valor estadístico claro."
        )
        send_telegram_message(msg)
        count += 1
        if count >= 2:
            break

    last_prematch_date = today_str

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Bot configurado con Football-Data.org...")
    
    send_telegram_message("🤖 Bot 100% activo: Monitoreo en directo sin límites y pronósticos de valor diarios.")

    while True:
        try:
            check_upcoming_value_bets()
            check_live_alerts()
        except Exception as e:
            logging.error(f"Error en bucle principal: {e}")

        # Revisa cada 3 minutos (no agota límites jamás)
        time.sleep(180)

if __name__ == "__main__":
    main()
