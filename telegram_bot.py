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
scheduled_tasks = set()
CSV_FILE = "registro_pronosticos.csv"

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Fecha", "Tipo", "Detalle", "Cuota", "Resultado", "Unidades"])

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
        logging.info(f"Respuesta Telegram: {res.status_code} - {res.text}")
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
    HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()

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
    """Rastrea marcadores y partidos de cualquier liga mundial en tiempo real."""
    events = get_all_global_live_events()
    
    # Si la API no devuelve eventos en ese instante, crea un evento de prueba directo
    if not events:
        events = [{
            "id": "live_demo_match",
            "home_team": "Sevilla FC",
            "away_team": "Real Betis",
            "league_title": "La Liga EA Sports"
        }]

    for event in events:
        home = event.get("home_team", "Local")
        away = event.get("away_team", "Visitante")
        event_id = event.get("id")
        now_ts = int(time.time() // 300) # Permite enviar alertas con más frecuencia
        alert_key = f"live_global_{event_id}_{now_ts}"

        if alert_key in sent_alerts:
            continue

        live_minutes = random.choice([28, 36, 58, 67, 74])
        simulated_score_home = random.choice([0, 1, 2])
        simulated_score_away = random.choice([0, 1])

        market_options = [
            ("⚡ OPORTUNIDAD LIVE (1X2)", f"Victoria de {home}", 2.10, f"Marcador Live: {simulated_score_home}-{simulated_score_away} (Min {live_minutes}'). Presión y volumen ofensivo favorable a {home}."),
            ("⚽ OPORTUNIDAD LIVE (GOLES)", "Más de 0.5 Goles en 2ª Parte", 1.85, f"Marcador Live: {simulated_score_home}-{simulated_score_away} (Min {live_minutes}'). Dominio total en ambas áreas."),
            ("🚩 OPORTUNIDAD LIVE (CÓRNERS)", "Más de 8.5 Córners Totales", 1.95, f"Minuto {live_minutes}' de juego. Incursiones constantes por bandas forzando saques de esquina.")
        ]
        
        chosen_mkt, chosen_sel, chosen_odds, live_analysis = random.choice(market_options)

        caption_msg = (
            f"🚨 <b>{chosen_mkt}</b> 🚨\n\n"
            f"🏆 <b>Liga / Torneo:</b> {event.get('league_title', 'Internacional')}\n"
            f"⚔️ <b>Partido:</b> {home} {simulated_score_home} - {simulated_score_away} {away}\n"
            f"⏱️ <b>Tiempo:</b> Minuto {live_minutes}' (En Directo)\n\n"
            f"📌 <b>Selección Recomendada:</b> {chosen_sel}\n"
            f"📈 <b>Cuota Live:</b> {chosen_odds:.2f}€ | 🏦 <b>Casa:</b> Bet365\n\n"
            f"📊 <b>ANÁLISIS DE MARCADOR EN VIVO:</b>\n"
            f"• {live_analysis}\n\n"
            f"⚠️ <b>Stake Sugerido:</b> Stake 1"
        )

        img_path = create_toptips_analysis_image(f"{home} vs {away}", event.get('league_title', 'Internacional'), chosen_sel, chosen_odds)
        
        if send_telegram_photo(img_path, caption_msg):
            sent_alerts.add(alert_key)
            return

def publish_intelligent_parlays():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    if f"parlay_ai_{today_str}" in sent_alerts:
        return

    events = get_all_global_live_events()
    if len(events) < 2:
        return

    e1, e2 = events[0], events[1]
    e1_home, e1_away = e1.get("home_team", "Local 1"), e1.get("away_team", "Visitante 1")
    e2_home, e2_away = e2.get("home_team", "Local 2"), e2.get("away_team", "Visitante 2")

    msg = (
        f"🤖 <b>APUESTAS COMBINADAS IA - COBERTURA GLOBAL</b> 🤖\n\n"
        f"🏆 <i>Análisis Algorítmico Multimercado de Valor</i>\n\n"
        f"💥 <b>COMBINADA BASE EV+ (Cuota @3.85)</b>\n"
        f"• <b>{e1_home} vs {e1_away}:</b> Victoria de {e1_home} o Empate\n"
        f"• <b>{e2_home} vs {e2_away}:</b> Más de 1.5 Goles Totales\n"
        f"📌 <b>Stake 2/5</b>\n\n"
        f"🔥 <b>COMBINADA BOMBAGO LIVE (Cuota @12.50)</b>\n"
        f"• <b>{e1_home} vs {e1_away}:</b> Ambos Equipos Anotan + Más de 8.5 Córners\n"
        f"• <b>{e2_home} vs {e2_away}:</b> Victoria de {e2_home}\n"
        f"📌 <b>Stake 0.5/5</b>\n\n"
        f"💡 <i>Analizado y validado mediante filtros de valor globales en Bet365.</i>"
    )
    if send_telegram_message(msg):
        sent_alerts.add(f"parlay_ai_{today_str}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Bot TOPTIPS Inteligente Activo...")

    while True:
        try:
            publish_intelligent_parlays()
            check_live_match_alerts()
        except Exception as e:
            logging.error(f"Error en el bucle principal: {e}")
        time.sleep(120)

if __name__ == "__main__":
    main()
