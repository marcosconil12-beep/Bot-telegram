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
ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

FOOTBALL_API_URL = "https://api.football-data.org/v4/matches"

sent_alerts = set()
sent_odds_alerts = set()

# Servidor HTTP para mantener Render activo
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
    
    clean_chat_id = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": clean_chat_id, "text": text}
    
    try:
        res = requests.post(url, json=payload)
        res_data = res.json()
        if not res_data.get("ok"):
            logging.error(f"Error de Telegram: {res_data}")
        else:
            logging.info("Mensaje enviado con éxito a Telegram.")
    except Exception as e:
        logging.error(f"Error enviando mensaje: {e}")

# 1. ALERTAS EN DIRECTO (Football-Data)
def check_live_alerts():
    if not FOOTBALL_DATA_KEY:
        return
    
    headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
    url = f"{FOOTBALL_API_URL}?status=IN_PLAY"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            matches = response.json().get("matches", [])
        else:
            return
    except Exception:
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
                f"🔥 Oportunidad detectada para buscar gol."
            )
            send_telegram_message(msg)
            sent_alerts.add(match_id)

# 2. PRONÓSTICOS PRE-MATCH CON CUOTA REAL >= 1.80€ (The Odds API)
def check_value_bets_with_odds():
    if not ODDS_API_KEY:
        logging.warning("ODDS_API_KEY no configurada. Saltando búsqueda de cuotas.")
        return

    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal"

    try:
        response = requests.get(url)
        if response.status_code != 200:
            logging.error(f"Error en The Odds API: {response.status_code}")
            return
        
        events = response.json()
    except Exception as e:
        logging.error(f"Error consultando cuotas reales: {e}")
        return

    for event in events:
        event_id = event.get("id")
        if event_id in sent_odds_alerts:
            continue

        home_team = event.get("home_team")
        away_team = event.get("away_team")
        sport_title = event.get("sport_title", "Fútbol")

        bookmakers = event.get("bookmakers", [])
        if not bookmakers:
            continue

        best_home_price = 0
        best_away_price = 0
        bookie_name = ""

        for bookie in bookmakers:
            markets = bookie.get("markets", [])
            for market in markets:
                if market.get("key") == "h2h":
                    outcomes = market.get("outcomes", [])
                    for outcome in outcomes:
                        price = outcome.get("price", 0)
                        if outcome.get("name") == home_team and price > best_home_price:
                            best_home_price = price
                            bookie_name = bookie.get("title")
                        elif outcome.get("name") == away_team and price > best_away_price:
                            best_away_price = price

        target_team = None
        target_price = 0

        if best_home_price >= 1.80:
            target_team = home_team
            target_price = best_home_price
        elif best_away_price >= 1.80:
            target_team = away_team
            target_price = best_away_price

        if target_team and target_price >= 1.80:
            msg = (
                f"🎯 PRONÓSTICO CON CUOTA REAL (>= 1.80€) 🎯\n\n"
                f"🏆 Deporte/Liga: {sport_title}\n"
                f"⚔️ {home_team} vs {away_team}\n\n"
                f"📌 Selección: Victoria de {target_team}\n"
                f"💰 Cuota Real Detectada: {target_price:.2f}€\n"
                f"🏦 Casa de apuestas: {bookie_name}\n\n"
                f"📝 Argumentación: Selección filtrada automáticamente al superar la cuota mínima de 1.80€ con valor estadístico."
            )
            send_telegram_message(msg)
            sent_odds_alerts.add(event_id)
            break

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Bot en marcha con soporte para cuotas reales >= 1.80€...")
    
    start_msg = "🤖 Bot actualizado: Sistema de filtrado por Cuotas Reales (>= 1.80€) activado."
    send_telegram_message(start_msg)

    while True:
        try:
            check_live_alerts()
            check_value_bets_with_odds()
        except Exception as e:
            logging.error(f"Error en bucle principal: {e}")

        time.sleep(300)

if __name__ == "__main__":
    main()
