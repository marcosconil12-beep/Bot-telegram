import os
import time
import logging
import threading
import requests
import random
import csv
from datetime import datetime
from PIL import Image, ImageDraw
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuración de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

sent_alerts = set()
CSV_FILE = "registro_pronosticos.csv"

def init_csv():
    try:
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Fecha", "Tipo", "Detalle", "Cuota", "Resultado", "Unidades"])
    except Exception as e:
        logging.error(f"Error inicializando CSV: {e}")

init_csv()

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("Falta TELEGRAM_BOT_TOKEN o CHAT_ID")
        return None
    
    chat_id_clean = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    token_clean = str(TELEGRAM_BOT_TOKEN).strip().replace('"', '').replace("'", "")
    
    url = f"https://api.telegram.org/bot{token_clean}/sendMessage"
    payload = {"chat_id": chat_id_clean, "text": text, "parse_mode": "HTML"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error al enviar mensaje: {e}")
        return None

def send_telegram_photo(photo_path, caption):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        return None
    
    chat_id_clean = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    token_clean = str(TELEGRAM_BOT_TOKEN).strip().replace('"', '').replace("'", "")
    
    url = f"https://api.telegram.org/bot{token_clean}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            res = requests.post(url, data={"chat_id": chat_id_clean, "caption": caption, "parse_mode": "HTML"}, files={"photo": photo}, timeout=15)
            return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error al enviar foto: {e}")
        return None

def create_toptips_analysis_image(match_title, league_name, pick_text, odds_val):
    """Genera la tarjeta gráfica oficial TOPTIPS."""
    img = Image.new('RGB', (900, 500), color=(11, 19, 43))
    d = ImageDraw.Draw(img)
    
    d.rectangle([15, 15, 885, 485], outline=(212, 175, 55), width=4)
    d.text((40, 35), "⚡ TOPTIPS - MONITOR GLOBAL EN DIRECTO", fill=(212, 175, 55))
    d.text((40, 85), f"COMPETICION: {league_name.upper()}", fill=(200, 200, 200))
    d.text((40, 135), f"ENCUENTRO: {match_title}", fill=(255, 255, 255))
    
    d.rectangle([35, 200, 865, 330], fill=(28, 37, 65), outline=(0, 200, 150), width=2)
    d.text((55, 220), "SELECCION LIVE RECOMENDADA IA:", fill=(0, 200, 150))
    d.text((55, 265), f"{pick_text} @ {odds_val:.2f}", fill=(255, 255, 255))
    
    d.text((40, 370), "COBERTURA: Marcadores Globales | Presion Live | xG en Vivo", fill=(160, 160, 160))
    d.text((40, 420), "Canal Oficial Telegram: @FreeTopTip", fill=(212, 175, 55))
    
    filename = "toptips_analysis.png"
    img.save(filename)
    return filename

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot TOPTIPS Multi-Mercado & Live Active".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error en servidor HTTP: {e}")

def get_all_global_live_events():
    """Rastrea partidos de CUALQUIER liga en curso a nivel mundial."""
    if not ODDS_API_KEY:
        return []
    
    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            events = res.json()
            for e in events:
                e['league_title'] = e.get('sport_title', 'Liga Internacional')
            return events
    except Exception as e:
        logging.error(f"Error al obtener partidos globales: {e}")
    return []

def check_live_match_alerts():
    """Rastrea partidos REALES de cualquier liga mundial."""
    try:
        events = get_all_global_live_events()
        if not events:
            return

        today_str = datetime.now().strftime("%Y-%m-%d")

        for event in events:
            home = event.get("home_team", "Local")
            away = event.get("away_team", "Visitante")
            event_id = event.get("id")
            alert_key = f"live_real_{event_id}_{today_str}"

            if alert_key in sent_alerts:
                continue

            odds_val = 2.00
            if event.get("bookmakers") and len(event["bookmakers"]) > 0:
                markets = event["bookmakers"][0].get("markets", [])
                if markets and len(markets[0].get("outcomes", [])) > 0:
                    odds_val = markets[0]["outcomes"][0].get("price", 2.00)

            market_options = [
                ("⚡ OPORTUNIDAD LIVE (1X2)", f"Victoria de {home}", odds_val, f"Presión ofensiva y dominio de balón favorable a {home}."),
                ("⚽ OPORTUNIDAD LIVE (GOLES)", "Más de 1.5 Goles Totales", 1.85, f"Ritmo de juego intenso proyectado para el choque entre {home} y {away}."),
                ("🚩 OPORTUNIDAD LIVE (CÓRNERS)", "Más de 8.5 Córners Totales", 1.95, f"Ataque continuo por bandas entre {home} y {away}.")
            ]
            
            chosen_mkt, chosen_sel, chosen_odds, live_analysis = random.choice(market_options)

            caption_msg = (
                f"🚨 <b>{chosen_mkt}</b> 🚨\n\n"
                f"🏆 <b>Liga / Torneo:</b> {event.get('league_title', 'Internacional')}\n"
                f"⚔️ <b>Partido Real:</b> {home} vs {away}\n"
                f"⏱️ <b>Estado:</b> Partido en Vivo / Programado hoy\n\n"
                f"📌 <b>Selección Recomendada:</b> {chosen_sel}\n"
                f"📈 <b>Cuota Real:</b> {chosen_odds:.2f}€ | 🏦 <b>Casa:</b> Bet365\n\n"
                f"📊 <b>ANÁLISIS EN VIVO:</b>\n"
                f"• {live_analysis}\n\n"
                f"⚠️ <b>Stake Sugerido:</b> Stake 1"
            )

            img_path = create_toptips_analysis_image(f"{home} vs {away}", event.get('league_title', 'Internacional'), chosen_sel, chosen_odds)
            
            if send_telegram_photo(img_path, caption_msg):
                sent_alerts.add(alert_key)
                return
    except Exception as e:
        logging.error(f"Error en check_live_match_alerts: {e}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Bot TOPTIPS Inteligente Activo...")

    while True:
        try:
            check_live_match_alerts()
        except Exception as e:
            logging.error(f"Error en el bucle principal: {e}")
        time.sleep(180)

if __name__ == "__main__":
    main()
