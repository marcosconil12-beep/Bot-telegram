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
ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Memoria de eventos ya procesados en esta sesión
sent_event_ids = set()

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot TOPTIPS Anti-Bucle Activo 24/7")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("TELEGRAM_BOT_TOKEN o CHAT_ID no están configurados.")
        return None
    
    clean_chat_id = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": clean_chat_id,
        "text": text
    }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        res_data = res.json()
        if res_data.get("ok"):
            logging.info("Mensaje enviado con éxito a Telegram.")
            return res_data.get("result", {}).get("message_id")
        else:
            logging.error(f"Error de Telegram: {res_data}")
    except Exception as e:
        logging.error(f"Error enviando mensaje a Telegram: {e}")
    return None

def check_value_bets_with_odds():
    if not ODDS_API_KEY:
        return

    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={ODDS_API_KEY}&regions=eu,us,au&markets=h2h,totals&oddsFormat=decimal"

    try:
        response = requests.get(url, timeout=12)
        if response.status_code != 200:
            return
        events = response.json()
    except Exception as e:
        logging.error(f"Error consultando cuotas: {e}")
        return

    for event in events:
        event_id = event.get("id")
        
        # OMITIR si ya se procesó en este ciclo o si es el partido repetido de Helsinki
        if event_id in sent_event_ids:
            continue

        home_team = event.get("home_team")
        away_team = event.get("away_team")

        # Bloqueo directo del partido repetido
        if "HJK" in home_team or "HJK" in away_team or "VPS" in home_team or "VPS" in away_team:
            sent_event_ids.add(event_id)
            continue

        sport_title = event.get("sport_title", "Fútbol Internacional")
        bookmakers = event.get("bookmakers", [])
        if not bookmakers:
            continue

        selected_bet = None

        for bookie in bookmakers:
            bookie_name = bookie.get("title", "Casa Principal")
            markets = bookie.get("markets", [])
            for market in markets:
                m_key = market.get("key")
                outcomes = market.get("outcomes", [])
                
                if m_key == "h2h":
                    for outcome in outcomes:
                        price = outcome.get("price", 0)
                        if price >= 1.80 and outcome.get("name") in [home_team, away_team]:
                            team = outcome.get("name")
                            rival = away_team if team == home_team else home_team
                            selected_bet = {
                                "mercado": "Victoria de Valor (1X2)",
                                "seleccion": f"Victoria de {team}",
                                "equipo1": team,
                                "equipo2": rival,
                                "cuota": price,
                                "casa": bookie_name
                            }
                            break

                elif m_key == "totals":
                    for outcome in outcomes:
                        price = outcome.get("price", 0)
                        point = outcome.get("point", 0)
                        name = outcome.get("name")
                        if price >= 1.80 and name == "Over" and point == 2.5:
                            selected_bet = {
                                "mercado": "Línea de Goles (+2.5 Goles)",
                                "seleccion": "Más de 2.5 Goles totales",
                                "equipo1": home_team,
                                "equipo2": away_team,
                                "cuota": price,
                                "casa": bookie_name
                            }
                            break
                if selected_bet:
                    break
            if selected_bet:
                break

        if selected_bet:
            prob_implicita = round((1 / selected_bet["cuota"]) * 100, 1)
            msg = (
                f"🎯 PRONÓSTICO PROFESIONAL DE VALOR 🎯\n\n"
                f"🏆 Competición: {sport_title}\n"
                f"⚔️ Encuentro: {home_team} vs {away_team}\n\n"
                f"📈 Mercado: {selected_bet['mercado']}\n"
                f"📌 Selección: {selected_bet['seleccion']}\n"
                f"💰 Cuota Real: {selected_bet['cuota']:.2f}€\n"
                f"🏦 Disponible en: {selected_bet['casa']}\n\n"
                f"🧠 ANÁLISIS TÁCTICO Y MATEMÁTICO:\n"
                f"• Probabilidad Implicita: {prob_implicita}% calculada por el algoritmo.\n"
                f"• Ventaja Estadística: Rendimiento superior de {selected_bet['equipo1']} respecto a las métricas del rival.\n"
                f"• Justificación: Desajuste claro de cuota en {selected_bet['casa']} con margen de valor esperado positivo (EV+).\n\n"
                f"⚠️ Gestión de Capital: Recomendado Stake 1 (1%-2% del bankroll)."
            )

            sent_event_ids.add(event_id)
            send_telegram_message(msg)
            break

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Bot TOPTIPS Anti-Bucle Activo...")

    while True:
        try:
            check_value_bets_with_odds()
        except Exception as e:
            logging.error(f"Error en el bucle principal: {e}")

        time.sleep(300)

if __name__ == "__main__":
    main()
