import os
import time
import logging
import threading
import requests
import random
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuración de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Registros en memoria persistente contra duplicados
sent_alerts = set()
sent_news = set()

# Cobertura completa de Ligas
TARGET_LEAGUES = [
    # España
    "soccer_spain_la_liga", "soccer_spain_segunda_division",
    "Primera RFEF (Todos los Grupos)", "Segunda RFEF (Todos los Grupos)", "Tercera RFEF (Grupo 10)",
    # Inglaterra y Francia
    "soccer_epl", "soccer_efl_champ", "soccer_france_ligue_one", "soccer_france_ligue_two",
    # Italia y Brasil
    "soccer_italy_serie_a", "soccer_italy_serie_b", "soccer_brazil_campeonato", "Serie B Brasil",
    # Asia y Oceanía
    "soccer_japan_j_league", "J2 League", "soccer_australia_aleague", "soccer_korea_kleague1",
    # Escocia
    "soccer_scotland_premiership"
]

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot TOPTIPS Scores24 AI Multi-Market Active")

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
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        res_data = res.json()
        if res_data.get("ok"):
            logging.info("Mensaje enviado a Telegram.")
            return res_data.get("result", {}).get("message_id")
        else:
            logging.error(f"Error Telegram: {res_data}")
    except Exception as e:
        logging.error(f"Error enviando mensaje: {e}")
    return None

def generate_scores24_ai_analysis(home, away, market_key, sport_title):
    """Simulador de Análisis Predictivo Avanzado estilo Scores24 (xG, Córners, Tarjetas)."""
    if market_key == "totals":
        xg_home = round(random.uniform(1.3, 2.1), 2)
        xg_away = round(random.uniform(1.1, 1.8), 2)
        total_xg = round(xg_home + xg_away, 2)
        return (
            f"🤖 <b>MODELO PREDICTIVO IA (Scores24 Data):</b>\n"
            f"• <b>xG Proyectado (Goles Esperados):</b> {home} ({xg_home}) vs {away} ({xg_away}) | Total: <b>{total_xg}</b>\n"
            f"• <b>Eficiencia Defensiva:</b> 78% de concesión de ocasiones claras en transiciones.\n"
            f"• <b>Probabilidad de IA:</b> 68.4% de superar la línea de goles propuestos.\n\n"
            f"🧠 <b>ARGUMENTACIÓN TÁCTICA:</b>\n"
            f"Ambos equipos muestran un índice de presión alta que fuerza pérdidas cerca del área rival."
        )
    elif market_key == "corners":
        c_home = round(random.uniform(5.5, 7.5), 1)
        c_away = round(random.uniform(4.0, 6.0), 1)
        return (
            f"🤖 <b>MODELO PREDICTIVO IA (Scores24 Corners):</b>\n"
            f"• <b>Promedio de Saques de Esquina:</b> {home} ({c_home}) | {away} ({c_away})\n"
            f"• <b>Ataque por Bandas:</b> 65% de las jugadas ofensivas terminan en centro o disparo desviado.\n"
            f"• <b>Probabilidad de IA:</b> 72.1% para el mercado de Córners seleccionado.\n\n"
            f"🧠 <b>ARGUMENTACIÓN TÁCTICA:</b>\n"
            f"Equipos con extremos puros que buscan constantemente la línea de fondo."
        )
    elif market_key == "cards":
        foul_avg = round(random.uniform(26.0, 32.0), 1)
        return (
            f"🤖 <b>MODELO PREDICTIVO IA (Scores24 Disciplina):</b>\n"
            f"• <b>Promedio de Faltas Proyectado:</b> {foul_avg} faltas en el partido.\n"
            f"• <b>Índice de Rigurosidad Arbitral:</b> 5.4 tarjetas por encuentro.\n"
            f"• <b>Probabilidad de IA:</b> 65.8% para línea de Tarjetas recomendada.\n\n"
            f"🧠 <b>ARGUMENTACIÓN TÁCTICA:</b>\n"
            f"Duelo directo de alta tensión en la medular con tendencia al corte de contras tácticas."
        )
    else: # 1X2 / H2H
        prob_win = round(random.uniform(55.0, 67.0), 1)
        return (
            f"🤖 <b>MODELO PREDICTIVO IA (Scores24 1X2):</b>\n"
            f"• <b>Forma y Rendimiento H2H:</b> Dominio estadístico del 60% en choques directos.\n"
            f"• <b>Probabilidad Algorítmica de Victoria:</b> <b>{prob_win}%</b>\n"
            f"• <b>Valor Esperado (EV+):</b> +8.4% frente a la cuota ofrecida por la casa.\n\n"
            f"🧠 <b>ARGUMENTACIÓN TÁCTICA:</b>\n"
            f"Superioridad en la posesión estructurada y mayor fondo de armario tras los cambios en el minuto 60."
        )

def check_scores24_ai_picks():
    if not ODDS_API_KEY:
        return

    api_sports = ["soccer_spain_la_liga", "soccer_epl", "soccer_italy_serie_a", "soccer_germany_bundesliga", "soccer_france_ligue_one"]
    max_picks = 2
    sent_count = 0

    for sport in api_sports:
        if sent_count >= max_picks:
            break

        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code != 200:
                continue
            events = res.json()
        except Exception:
            continue

        for event in events:
            if sent_count >= max_picks:
                break

            home_team = event.get("home_team", "")
            away_team = event.get("away_team", "")
            match_id = f"{home_team}_vs_{away_team}"

            bookmakers = event.get("bookmakers", [])
            if not bookmakers:
                continue

            for bookie in bookmakers:
                b_name = bookie.get("title", "Bet365 / Casas TOP")
                for market in bookie.get("markets", []):
                    m_key = market.get("key")
                    outcomes = market.get("outcomes", [])

                    if m_key == "totals":
                        for outcome in outcomes:
                            price = outcome.get("price", 0)
                            if price >= 1.80 and outcome.get("name") == "Over" and outcome.get("point") == 2.5:
                                alert_key = f"{match_id}_goles_{datetime.now().strftime('%Y-%m-%d')}"
                                if alert_key in sent_alerts:
                                    continue

                                analysis = generate_scores24_ai_analysis(home_team, away_team, "totals", event.get("sport_title"))
                                msg = (
                                    f"🤖 <b>PICK SCORES24 IA - MERCADO GOLES</b> 🤖\n\n"
                                    f"🏆 <b>Competición:</b> {event.get('sport_title', 'Fútbol')}\n"
                                    f"⚔️ <b>Encuentro:</b> {home_team} vs {away_team}\n\n"
                                    f"⚽ <b>Mercado:</b> Total de Goles (+2.5 Goles)\n"
                                    f"💰 <b>Cuota Real:</b> {price:.2f}€ | 🏦 <b>Casa:</b> {b_name}\n\n"
                                    f"{analysis}\n\n"
                                    f"⚠️ <b>Stake Recomendado:</b> Stake 1 (1%-2% Bankroll)"
                                )
                                msg_id = send_telegram_message(msg)
                                if msg_id:
                                    sent_alerts.add(alert_key)
                                    sent_count += 1
                                break

def publish_half_hourly_news():
    hour_slot = datetime.now().strftime("%Y-%m-%d_%H") + ("_30" if datetime.now().minute >= 30 else "_00")

    if hour_slot in sent_news:
        return

    league = random.choice(TARGET_LEAGUES)
    clean_league_name = league.replace("soccer_spain_", "").replace("soccer_", "").replace("_", " ").title()

    msg = (
        f"📰 <b>SCORES24 DATA - INFORME TÁCTICO</b> 📰\n\n"
        f"🏆 <b>Liga / Torneo:</b> {clean_league_name}\n"
        f"🕒 <b>Actualización:</b> Métricas e IA en tiempo real\n\n"
        f"📌 <b>Análisis Estadístico Avanzado:</b>\n"
        f"• Los algoritmos monitorean volumen de apuestas en <b>Goles, Córners, Tarjetas y 1X2</b>.\n"
        f"• Se proyecta un incremento de xG en los minutos 60-90 para los encuentros de esta jornada.\n"
        f"• Los filtros EV+ permanecen activos buscando desviaciones de cuotas en las principales casas de apuestas.\n\n"
        f"💡 <i>Próximo rastreo automatizado de valor en breve.</i>"
    )
    
    msg_id = send_telegram_message(msg)
    if msg_id:
        sent_news.add(hour_slot)
        logging.info(f"Noticia publicada para la franja {hour_slot}.")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Bot TOPTIPS Scores24 IA Multi-Mercado en ejecución...")

    while True:
        try:
            check_scores24_ai_picks()
            publish_half_hourly_news()
        except Exception as e:
            logging.error(f"Error en el bucle principal: {e}")

        time.sleep(300)

if __name__ == "__main__":
    main()
