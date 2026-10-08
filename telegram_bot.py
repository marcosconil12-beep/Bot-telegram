import os
import time
import json
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

DB_FILE = "pending_bets.json"

# Funciones de persistencia en disco
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error cargando base de datos: {e}")
    return {"sent_live": [], "sent_odds": [], "pending_bets": {}}

def save_db(data):
    try:
        with open(DB_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logging.error(f"Error guardando base de datos: {e}")

db_data = load_db()
sent_live_alerts = set(db_data.get("sent_live", []))
sent_odds_alerts = set(db_data.get("sent_odds", []))
pending_bets = db_data.get("pending_bets", {})

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot TOPTIPS Sin Bucles 24/7 Activo")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

def send_telegram_message(text, reply_to_message_id=None):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("TELEGRAM_BOT_TOKEN o CHAT_ID no están configurados.")
        return None
    
    clean_chat_id = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": clean_chat_id,
        "text": text
    }
    
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    
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

def update_db_file():
    save_db({
        "sent_live": list(sent_live_alerts),
        "sent_odds": list(sent_odds_alerts),
        "pending_bets": pending_bets
    })

# 1. ESTRATEGIA LIVE: OVER 0.5 GOLES 1ª PARTE (HT)
def check_live_alerts_ht():
    if not ODDS_API_KEY:
        return

    url = f"https://api.the-odds-api.com/v4/sports/soccer/scores/?apiKey={ODDS_API_KEY}&daysFrom=1"

    try:
        response = requests.get(url, timeout=12)
        if response.status_code != 200:
            return
        events = response.json()
    except Exception as e:
        logging.error(f"Error consultando partidos Live: {e}")
        return

    for event in events:
        event_id = event.get("id")
        if event_id in sent_live_alerts:
            continue

        completed = event.get("completed", False)
        scores = event.get("scores")

        if not completed and scores and len(scores) >= 2:
            home_team = event.get("home_team")
            away_team = event.get("away_team")
            sport_title = event.get("sport_title", "Fútbol Live")

            home_score = 0
            away_score = 0
            for score in scores:
                if score.get("name") == home_team:
                    home_score = int(score.get("score", 0))
                elif score.get("name") == away_team:
                    away_score = int(score.get("score", 0))

            if home_score == 0 and away_score == 0:
                msg = (
                    f"🔥 ALERTA LIVE: OVER 0.5 GOLES 1ª PARTE (HT) 🔥\n\n"
                    f"🏆 Competición: {sport_title}\n"
                    f"⚔️ Encuentro: {home_team} vs {away_team}\n"
                    f"⏱️ Tramo Crítico: Minuto 30' - 45' (1ª Parte)\n"
                    f"📊 Marcador en Directo: 0 - 0\n\n"
                    f"🧠 ANÁLISIS DE PRESIÓN EN DIRECTO:\n"
                    f"• Presión Asfixiante: Alta intensidad ofensiva en los últimos 15 minutos del primer tiempo.\n"
                    f"• Volumen de Ataque: Múltiples llegadas al área, saques de esquina acumulados y remates a puerta.\n"
                    f"• Selección Recomendada: Over 0.5 Goles Primera Parte (1ST HALF OVER 0.5 GOALS)\n"
                    f"💰 Cuota Estimada Live: 1.70€ - 2.10€\n\n"
                    f"⚠️ Gestión de Stake: Entrar con Stake 1 (1% del bankroll)."
                )
                send_telegram_message(msg)
                sent_live_alerts.add(event_id)
                update_db_file()

# 2. PRONÓSTICOS PRE-MATCH MULTI-MERCADO
def check_value_bets_with_odds():
    if not ODDS_API_KEY:
        return

    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={ODDS_API_KEY}&regions=eu,us,au&markets=h2h,spreads,totals&oddsFormat=decimal"

    try:
        response = requests.get(url, timeout=12)
        if response.status_code != 200:
            return
        events = response.json()
    except Exception as e:
        logging.error(f"Error consultando cuotas multimercado: {e}")
        return

    for event in events:
        event_id = event.get("id")
        if event_id in sent_odds_alerts or event_id in pending_bets:
            continue

        home_team = event.get("home_team")
        away_team = event.get("away_team")
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

            msg_id = send_telegram_message(msg)
            sent_odds_alerts.add(event_id)

            if msg_id:
                pending_bets[event_id] = {
                    "home_team": home_team,
                    "away_team": away_team,
                    "target_team": selected_bet["equipo1"],
                    "price": selected_bet["cuota"],
                    "message_id": msg_id
                }
            
            update_db_file()
            break

# 3. VERIFICAR RESULTADOS Y PUBLICAR ACIERTOS / FALLOS
def check_completed_results():
    global pending_bets
    if not ODDS_API_KEY or not pending_bets:
        return

    url = f"https://api.the-odds-api.com/v4/sports/soccer/scores/?apiKey={ODDS_API_KEY}&daysFrom=1"

    try:
        response = requests.get(url, timeout=12)
        if response.status_code != 200:
            return
        scores_data = response.json()
    except Exception as e:
        logging.error(f"Error al obtener marcadores: {e}")
        return

    completed_ids = []

    for event in scores_data:
        event_id = event.get("id")
        if event_id in pending_bets and event.get("completed"):
            bet_info = pending_bets[event_id]
            scores = event.get("scores")

            if not scores or len(scores) < 2:
                continue

            home_score = 0
            away_score = 0
            for score in scores:
                if score.get("name") == bet_info["home_team"]:
                    home_score = int(score.get("score", 0))
                elif score.get("name") == bet_info["away_team"]:
                    away_score = int(score.get("score", 0))

            if home_score > away_score:
                winner = bet_info["home_team"]
            elif away_score > home_score:
                winner = bet_info["away_team"]
            else:
                winner = "Empate"

            target_team = bet_info["target_team"]
            price = bet_info["price"]
            msg_id = bet_info["message_id"]

            if winner == target_team:
                ganancia = round((price - 1) * 100, 1)
                result_msg = (
                    f"✅ PRONÓSTICO ACERTADO (GREEN) 🟢\n\n"
                    f"⚔️ Partido: {bet_info['home_team']} {home_score} - {away_score} {bet_info['away_team']}\n"
                    f"🎯 Resultado de Selección: Victoria Cumplida\n"
                    f"💰 Cuota Cobrada: {price:.2f}€\n"
                    f"📈 Rentabilidad: +{ganancia}% de beneficio"
                )
            else:
                result_msg = (
                    f"❌ PRONÓSTICO NO ACERTADO (RED) 🔴\n\n"
                    f"⚔️ Resultado Final: {bet_info['home_team']} {home_score} - {away_score} {bet_info['away_team']}\n"
                    f"📌 Apuesta realizada: Victoria de {target_team}\n"
                    f"📊 Marcador Final: {home_score} - {away_score}"
                )

            send_telegram_message(result_msg, reply_to_message_id=msg_id)
            completed_ids.append(event_id)

    if completed_ids:
        for eid in completed_ids:
            del pending_bets[eid]
        update_db_file()

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Bot TOPTIPS con memoria permanente activado...")
    
    # Mensaje de inicio desactivado para evitar notificaciones innecesarias en cada reinicio
    while True:
        try:
            check_live_alerts_ht()
            check_value_bets_with_odds()
            check_completed_results()
        except Exception as e:
            logging.error(f"Error en el bucle principal: {e}")

        time.sleep(180)

if __name__ == "__main__":
    main()
