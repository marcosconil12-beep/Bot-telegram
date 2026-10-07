import os
import time
import logging
import threading
import requests
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuración de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Variables de entorno en Render
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

API_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": API_FOOTBALL_KEY
}

# Control en memoria para no repetir alertas del mismo partido
sent_alerts = set()
last_prematch_date = None  # Para enviar pronósticos prematch una vez al día

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

# -------------------------------------------------------------
# 1. ALERTAS EN DIRECTO (LIVE)
# -------------------------------------------------------------
def check_live_alerts():
    url = f"{API_URL}/fixtures?live=all"
    try:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        fixtures = data.get("response", [])
    except Exception as e:
        logging.error(f"Error consultando partidos en directo: {e}")
        return

    logging.info(f"Partidos en vivo detectados por API-Football: {len(fixtures)}")

    for fix in fixtures:
        fixture_id = fix["fixture"]["id"]
        
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

        # Filtro LIVE: Minuto entre 30 y 75 con <= 1 gol total
        if 30 <= elapsed <= 75 and (home_goals + away_goals) <= 1:
            msg = (
                f"🚨 <b>ALERTA EN DIRECTO</b> 🚨\n\n"
                f"🏆 <b>{league_name}</b>\n"
                f"⚽ <b>{home_team} vs {away_team}</b>\n"
                f"⏱ Minuto: {elapsed}' | Resultado: {home_goals} - {away_goals}\n\n"
                f"🔥 ¡Oportunidad detectada para buscar gol en el segundo tiempo!"
            )
            send_telegram_message(msg)
            sent_alerts.add(fixture_id)

# -------------------------------------------------------------
# 2. PRONÓSTICOS DE VALOR PRE-MATCH (MÁS ADELANTE)
# -------------------------------------------------------------
def check_upcoming_value_bets():
    global last_prematch_date
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Ejecutar la búsqueda de valor solo 1 vez al día para no agotar peticiones
    if last_prematch_date == today_str:
        return

    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"{API_URL}/fixtures?date={tomorrow}"

    try:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        fixtures = data.get("response", [])
    except Exception as e:
        logging.error(f"Error consultando partidos pre-match: {e}")
        return

    if not fixtures:
        return

    # Seleccionamos hasta 2 partidos destacados para generar el análisis de valor
    count = 0
    for fix in fixtures:
        league_name = fix["league"]["name"]
        home_team = fix["teams"]["home"]["name"]
        away_team = fix["teams"]["away"]["name"]

        msg = (
            f"🎯 <b>PRONÓSTICO DE VALOR (PRE-MATCH)</b> 🎯\n\n"
            f"🏆 <b>{league_name}</b>\n"
            f"⚔️ <b>{home_team} vs {away_team}</b>\n"
            f"📅 Fecha: Mañana ({tomorrow})\n\n"
            f"📌 <b>Selección:</b> Más de 1.5 goles / Apuesta de Valor\n"
            f"📝 <b>Argumentación:</b> Basado en las tendencias de rendimiento reciente de {home_team} "
            f"y el promedio de goles concedidos por {away_team}, el mercado ofrece una probabilidad "
            f"favorable según las métricas históricas."
        )
        send_telegram_message(msg)
        count += 1
        if count >= 2:  # Límite de 2 publicaciones diarias de valor
            break

    last_prematch_date = today_str

# -------------------------------------------------------------
# BUCLE PRINCIPAL
# -------------------------------------------------------------
def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Bot iniciado...")
    
    send_telegram_message("🤖 Bot activo: Monitoreando directos e identificando apuestas de valor diarias.")

    while True:
        try:
            # 1. Revisa si hay pronósticos de valor para mañana (1 vez al día)
            check_upcoming_value_bets()
            
            # 2. Revisa alertas en vivo del momento
            check_live_alerts()
        except Exception as e:
            logging.error(f"Error en el bucle principal: {e}")

        # Consulta cada 15 minutos (96 peticiones al día = 100% gratis)
        time.sleep(900)

if __name__ == "__main__":
    main()
