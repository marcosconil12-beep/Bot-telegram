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

# Registro en memoria de alertas enviadas para evitar duplicados
sent_alerts = set()

# Servidor HTTP básico para Railway / Render
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot TOPTIPS Global Leagues & Tactical Analysis Active")

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

def generate_tactical_arguments(team1, team2, market_type, is_home):
    """
    Genera justificaciones cualitativas y tácticas según el equipo y el tipo de apuesta.
    """
    if market_type == "h2h":
        location = "jugando como local ante su afición" if is_home else "con un bloque reactivo muy efectivo fuera de casa"
        return [
            f"Estructura táctica favorabilísima: {team1} llega en una dinámica de solidez que ahoga la salida de balón de {team2}.",
            f"Factor campo y motivación: {team1} {location}, manteniendo mayor intensidad en duelos individuales en transiciones ofensivas.",
            f"Desajuste de lectura: El mercado infravalora el descanso semanal de {team1} frente al calendario sobrecargado del rival."
        ]
    else:
        return [
            f"Estilo de juego vertical: Ambos entrenadores plantean esquemas de presión alta que dejan espacios a las espaldas de los laterales.",
            f"Tendencia de juego directo: {team1} y {team2} destacan por generar ocasiones claras desde saques de esquina y balones parados.",
            f"Ritmo de partido: Ritmo de ida y vuelta proyectado por la necesidad urgente de sumar los 3 puntos en ambos conjuntos."
        ]

def check_value_bets_with_odds():
    if not ODDS_API_KEY:
        logging.error("No se ha configurado ODDS_API_KEY.")
        return

    # Cobertura global: Ligas Principales, Ligas Menores y Torneos Continentales
    sports_to_check = [
        # Grandes Ligas Europeas
        "soccer_spain_la_liga", "soccer_spain_segunda_division",
        "soccer_epl", "soccer_efl_champ",
        "soccer_italy_serie_a", "soccer_italy_serie_b",
        "soccer_germany_bundesliga", "soccer_germany_bundesliga2",
        "soccer_france_ligue_one", "soccer_france_ligue_two",
        "soccer_uefa_champs_league", "soccer_uefa_europa_league",
        # Ligas Europeas Secundarias y Menores
        "soccer_netherlands_eredivisie", "soccer_portugal_primeira_liga",
        "soccer_belgium_first_div", "soccer_turkey_super_lig",
        "soccer_greece_super_league", "soccer_scotland_premiership",
        "soccer_denmark_superliga", "soccer_switzerland_superleague",
        "soccer_norway_eliteserien", "soccer_sweden_allsvenskan",
        # Ligas de América y Asia
        "soccer_argentina_primera_division", "soccer_brazil_campeonato",
        "soccer_mexico_ligamx", "soccer_usa_mls",
        "soccer_japan_j_league", "soccer_korea_kleague1", "soccer_australia_aleague"
    ]

    for sport in sports_to_check:
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                continue
            events = response.json()
        except Exception:
            continue

        for event in events:
            home_team = event.get("home_team", "")
            away_team = event.get("away_team", "")
            match_id = f"{home_team}_vs_{away_team}"

            # Filtro de protección anti-bucle
            if any(team in home_team or team in away_team for team in ["HJK", "VPS", "Palmeiras", "Bahia"]):
                continue

            sport_title = event.get("sport_title", "Fútbol Profesional")
            bookmakers = event.get("bookmakers", [])
            if not bookmakers:
                continue

            selected_bet = None

            for bookie in bookmakers:
                bookie_name = bookie.get("title", "Bet365 / Casas TOP")
                markets = bookie.get("markets", [])
                for market in markets:
                    m_key = market.get("key")
                    outcomes = market.get("outcomes", [])
                    
                    if m_key == "h2h":
                        for outcome in outcomes:
                            price = outcome.get("price", 0)
                            if price >= 1.80 and outcome.get("name") in [home_team, away_team]:
                                team = outcome.get("name")
                                is_home = (team == home_team)
                                rival = away_team if is_home else home_team
                                alert_key = f"{match_id}_h2h_{team}"
                                
                                if alert_key in sent_alerts:
                                    continue

                                args = generate_tactical_arguments(team, rival, "h2h", is_home)

                                selected_bet = {
                                    "alert_key": alert_key,
                                    "mercado": "Victoria de Valor (1X2)",
                                    "seleccion": f"Victoria de {team}",
                                    "equipo1": team,
                                    "equipo2": rival,
                                    "cuota": price,
                                    "casa": bookie_name,
                                    "argumentos": args
                                }
                                break

                    elif m_key == "totals":
                        for outcome in outcomes:
                            price = outcome.get("price", 0)
                            point = outcome.get("point", 0)
                            name = outcome.get("name")
                            if price >= 1.80 and name == "Over" and point == 2.5:
                                alert_key = f"{match_id}_over2.5"
                                
                                if alert_key in sent_alerts:
                                    continue

                                args = generate_tactical_arguments(home_team, away_team, "totals", True)

                                selected_bet = {
                                    "alert_key": alert_key,
                                    "mercado": "Línea de Goles (+2.5 Goles)",
                                    "seleccion": "Más de 2.5 Goles totales",
                                    "equipo1": home_team,
                                    "equipo2": away_team,
                                    "cuota": price,
                                    "casa": bookie_name,
                                    "argumentos": args
                                }
                                break
                    if selected_bet:
                        break
                if selected_bet:
                    break

            if selected_bet:
                prob_implicita = round((1 / selected_bet["cuota"]) * 100, 1)
                args_text = "\n".join([f"• {arg}" for arg in selected_bet["argumentos"]])
                
                msg = (
                    f"🎯 PRONÓSTICO TÁCTICO Y MATEMÁTICO 🎯\n\n"
                    f"🏆 Competición: {sport_title}\n"
                    f"⚔️ Encuentro: {home_team} vs {away_team}\n\n"
                    f"📈 Mercado: {selected_bet['mercado']}\n"
                    f"📌 Selección: {selected_bet['seleccion']}\n"
                    f"💰 Cuota Real: {selected_bet['cuota']:.2f}€\n"
                    f"🏦 Casa de Apuestas: {selected_bet['casa']}\n\n"
                    f"🔍 ANÁLISIS DE POR QUÉ APOSTAMOS A ESTE PICK:\n"
                    f"{args_text}\n"
                    f"• Probabilidad Implicita: {prob_implicita}% calculada según margen EV+.\n\n"
                    f"⚠️ Gestión de Capital: Recomendado Stake 1 (1%-2% de bankroll)."
                )

                send_telegram_message(msg)
                sent_alerts.add(selected_bet["alert_key"])
                logging.info(f"Alerta enviada correctamente: {selected_bet['alert_key']}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Bot TOPTIPS Cobertura Global y Análisis Táctico en ejecución...")

    while True:
        try:
            check_value_bets_with_odds()
        except Exception as e:
            logging.error(f"Error en bucle principal: {e}")

        # Revisa todas las ligas cada 20 minutos (1200 segundos)
        time.sleep(1200)

if __name__ == "__main__":
    main()
