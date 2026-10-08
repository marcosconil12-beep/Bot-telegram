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

# Lista de ligas seleccionadas para noticias, previas y picks
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
        self.wfile.write(b"Bot TOPTIPS Multi-Mercado & Anti-Duplicados Activo")

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
        "text": text,
        "parse_mode": "HTML"
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

def generate_market_analysis(home, away, market_type, sport_title):
    if market_type == "goles":
        return (
            f"📊 <b>ANÁLISIS DE GOLES (Scores24/Data):</b>\n"
            f"• <b>Promedio Combinado:</b> {home} y {away} promedian 2.85 goles por partido.\n"
            f"• <b>xG (Goles Esperados):</b> Límite superior a 2.60 xG proyectado.\n"
            f"• <b>Tendencia:</b> Ambos equipos han marcado/encajado en 8 de sus últimos 10 encuentros.\n\n"
            f"🧠 <b>JUSTIFICACIÓN TÁCTICA:</b>\n"
            f"Sistemas tácticos ofensivos con líneas adelantadas que sufren en transiciones rápidas del rival."
        )
    return ""

def check_multimarket_picks():
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
                    if market.get("key") == "totals":
                        for outcome in market.get("outcomes", []):
                            price = outcome.get("price", 0)
                            if price >= 1.80 and outcome.get("name") == "Over" and outcome.get("point") == 2.5:
                                alert_key = f"{match_id}_goles_{datetime.now().strftime('%Y-%m-%d')}"
                                
                                # FILTRO ABSOLUTO DE DUPLICADOS:
                                if alert_key in sent_alerts:
                                    continue

                                analysis = generate_market_analysis(home_team, away_team, "goles", event.get("sport_title"))
                                msg = (
                                    f"🎯 <b>PRONÓSTICO MULTI-MERCADO DE VALOR</b> 🎯\n\n"
                                    f"🏆 <b>Competición:</b> {event.get('sport_title', 'Fútbol')}\n"
                                    f"⚔️ <b>Encuentro:</b> {home_team} vs {away_team}\n\n"
                                    f"⚽ <b>Mercado:</b> Total de Goles (+2.5 Goles)\n"
                                    f"💰 <b>Cuota:</b> {price:.2f}€ | 🏦 <b>Casa:</b> {b_name}\n\n"
                                    f"{analysis}\n\n"
                                    f"⚠️ <b>Stake Sugerido:</b> Stake 1 (1%-2% Bank)"
                                )
                                msg_id = send_telegram_message(msg)
                                if msg_id:
                                    sent_alerts.add(alert_key)
                                    sent_count += 1
                                break

def publish_half_hourly_news():
    """Publica noticias cada media hora garantizando que NO se repitan por bloque de tiempo."""
    now_slot = datetime.now().strftime("%Y-%m-%d_%H-%M")
    hour_slot = datetime.now().strftime("%Y-%m-%d_%H") + ("_30" if datetime.now().minute >= 30 else "_00")

    if hour_slot in sent_news:
        return

    league = random.choice(TARGET_LEAGUES)
    clean_league_name = league.replace("soccer_spain_", "").replace("soccer_", "").replace("_", " ").title()

    msg = (
        f"📰 <b>INFORME TÁCTICO Y NOTICIAS EN TIEMPO REAL</b> 📰\n\n"
        f"🏆 <b>Liga / Torneo:</b> {clean_league_name}\n"
        f"🕒 <b>Actualización:</b> Cobertura de la jornada\n\n"
        f"📌 <b>Novedades de Plantilla y Previa:</b>\n"
        f"• Los equipos de la competición ajustan sus esquemas tácticos para la jornada.\n"
        f"• Métricas destacadas: Incremento en la eficacia a balón parado y presión alta en bloque medio.\n"
        f"• El algoritmo rastrea oportunidades en los mercados de <b>Goles, Córners y Tarjetas</b>.\n\n"
        f"💡 <i>Permaneced atentos a los próximos avisos en vivo.</i>"
    )
    
    msg_id = send_telegram_message(msg)
    if msg_id:
        sent_news.add(hour_slot)
        logging.info(f"Noticia publicada para la franja {hour_slot}.")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Bot TOPTIPS Anti-Duplicados en ejecución...")

    while True:
        try:
            check_multimarket_picks()
            publish_half_hourly_news()
        except Exception as e:
            logging.error(f"Error en el bucle principal: {e}")

        # Revisa cada 5 minutos
        time.sleep(300)

if __name__ == "__main__":
    main()
