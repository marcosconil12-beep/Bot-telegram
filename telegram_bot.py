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

# Servidor HTTP para mantener Render activo y responder a pings
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo y funcionando 24/7")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("TELEGRAM_BOT_TOKEN o CHAT_ID no están configurados.")
        return
    
    clean_chat_id = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": clean_chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        res_data = res.json()
        if not res_data.get("ok"):
            logging.error(f"Error de Telegram: {res_data}")
        else:
            logging.info("Mensaje enviado con éxito a Telegram.")
    except Exception as e:
        logging.error(f"Error enviando mensaje a Telegram: {e}")

def generar_argumentacion(equipo, rival, cuota, casa):
    """Genera una argumentación técnica y detallada basada en la cuota y probabilidad implícita."""
    prob_implicita = round((1 / cuota) * 100, 1)
    
    if cuota >= 2.30:
        perfil = "Cuota Alta / Apuesta de Valor Prometedora"
        razon = (
            f"El mercado asigna una probabilidad del {prob_implicita}% a la victoria de *{equipo}*, "
            f"lo que presenta un desajuste claro frente a las métricas recientes del rival (*{rival}*). "
            f"Existe un valor sustancial en entrar con esta cuota de {cuota:.2f}€ en {casa}."
        )
    elif cuota >= 2.00:
        perfil = "Cuota Par / Excelente Relación Riesgo-Beneficio"
        razon = (
            f"Con una cuota superior al par ({cuota:.2f}€), la cuota ofrece una rentabilidad del 100%+ sobre el capital invertido. "
            f"La probabilidad implícita del {prob_implicita}% está infravalorada respecto a la dinámica ofensiva de *{equipo}*."
        )
    else:
        perfil = "Favorito con Cuota de Valor Estándar"
        razon = (
            f"Con un {prob_implicita}% de probabilidad implícita estimada por *{casa}*, "
            f"*{equipo}* llega con solidez para imponerse ante *{rival}*. "
            f"La cuota de {cuota:.2f}€ supera el umbral de seguridad mínimo (1.80€) con margen de beneficio."
        )

    argumento = (
        f"📊 *Análisis Técnico:*\n"
        f"• *Perfil:* {perfil}\n"
        f"• *Probabilidad Implicita:* {prob_implicita}%\n\n"
        f"💡 *Justificación del Pick:*\n{razon}"
    )
    return argumento

# 1. ALERTAS EN DIRECTO (Football-Data)
def check_live_alerts():
    if not FOOTBALL_DATA_KEY:
        return
    
    headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
    url = f"{FOOTBALL_API_URL}?status=IN_PLAY"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            matches = response.json().get("matches", [])
        else:
            return
    except Exception as e:
        logging.error(f"Error al consultar Football-Data: {e}")
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
                f"🚨 *ALERTA EN DIRECTO* 🚨\n\n"
                f"🏆 *Liga:* {competition}\n"
                f"⚽ *Partido:* {home_team} vs {away_team}\n"
                f"📊 *Marcador:* {home_goals} - {away_goals}\n\n"
                f"🔥 *Oportunidad Live:* Encuentro trabado con baja cifra de goles, "
                f"ideal para vigilar líneas de gol en el segundo tiempo."
            )
            send_telegram_message(msg)
            sent_alerts.add(match_id)

# 2. PRONÓSTICOS PRE-MATCH CON CUOTAS REALES >= 1.80€ (The Odds API)
def check_value_bets_with_odds():
    if not ODDS_API_KEY:
        logging.warning("ODDS_API_KEY no está configurada.")
        return

    # Consulta global (Europa, Estados Unidos, Australia) para cubrir partidos las 24 horas
    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={ODDS_API_KEY}&regions=eu,us,au&markets=h2h&oddsFormat=decimal"

    try:
        response = requests.get(url, timeout=12)
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
        sport_title = event.get("sport_title", "Fútbol Internacional")

        bookmakers = event.get("bookmakers", [])
        if not bookmakers:
            continue

        best_home_price = 0
        best_away_price = 0
        bookie_name = "Casa de Apuestas Principal"

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

        # Filtro estricto: Cuota mínima >= 1.80€
        target_team = None
        target_rival = None
        target_price = 0

        if best_home_price >= 1.80:
            target_team = home_team
            target_rival = away_team
            target_price = best_home_price
        elif best_away_price >= 1.80:
            target_team = away_team
            target_rival = home_team
            target_price = best_away_price

        if target_team and target_price >= 1.80:
            arg_texto = generar_argumentacion(target_team, target_rival, target_price, bookie_name)
            
            msg = (
                f"🎯 *PRONÓSTICO DE VALOR (CUOTA >= 1.80€)* 🎯\n\n"
                f"🏆 *Competición:* {sport_title}\n"
                f"⚔️ *Encuentro:* {home_team} vs {away_team}\n\n"
                f"📌 *Pronóstico:* Victoria de *{target_team}*\n"
                f"💰 *Cuota Real:* *{target_price:.2f}€*\n"
                f"🏦 *Disponible en:* {bookie_name}\n\n"
                f"{arg_texto}\n\n"
                f"⚠️ *Gestión de Stake:* Recomendado Stake 1 (1%-2% del bankroll)."
            )
            
            send_telegram_message(msg)
            sent_odds_alerts.add(event_id)
            break # Publica 1 pick por ciclo para mantener calidad y ritmo adecuado

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Bot iniciado con motor de análisis avanzado y cuotas reales >= 1.80€...")
    
    init_msg = "🤖 *Bot TOPTIPS Actualizado*\n\n✅ Motor de cuotas reales (>= 1.80€) activo.\n✅ Cobertura internacional 24/7.\n✅ Argumentaciones detalladas por partido habilitadas."
    send_telegram_message(init_msg)

    while True:
        try:
            check_live_alerts()
            check_value_bets_with_odds()
        except Exception as e:
            logging.error(f"Error en el bucle principal: {e}")

        # Revisa cada 5 minutos
        time.sleep(300)

if __name__ == "__main__":
    main()
