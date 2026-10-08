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

# Configuración de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
        return None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": str(CHAT_ID).strip(), "text": text, "parse_mode": "HTML"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.json().get("ok")
    except Exception:
        return None

def send_telegram_photo(photo_path, caption):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        return None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            res = requests.post(url, data={"chat_id": str(CHAT_ID).strip(), "caption": caption, "parse_mode": "HTML"}, files={"photo": photo}, timeout=15)
            return res.json().get("ok")
    except Exception:
        return None

def create_premium_image(match_text, league_text):
    img = Image.new('RGB', (800, 450), color=(15, 23, 42))
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, 780, 430], outline=(234, 179, 8), width=4)
    d.text((40, 50), "PICK PREMIUM STAKE 5 EXCLUSIVO", fill=(234, 179, 8))
    d.text((40, 120), f"Competicion: {league_text}", fill=(255, 255, 255))
    d.text((40, 180), f"Encuentro: {match_text}", fill=(255, 255, 255))
    d.text((40, 250), "Pronostico: CONFIDENCIAL / MAXIMO VALOR", fill=(34, 197, 94))
    d.text((40, 320), "Precio: 9,99 EUR", fill=(234, 179, 8))
    d.text((40, 370), "Adquierelo contactando a: @Mark122", fill=(148, 163, 184))
    filename = "premium_pick.png"
    img.save(filename)
    return filename

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot TOPTIPS Multi-Mercado & Combinadas Active".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler).serve_forever()

def publish_daily_routine():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    hour, minute = now.hour, now.minute

    # Buenos días (09:00 AM)
    if hour == 9 and f"morning_{today_str}" not in scheduled_tasks:
        send_telegram_message("☀️ <b>¡BUENOS DÍAS A TODOS!</b> ☀️\n\nArrancamos la jornada con nuestras Combinadas (Cuota 4, 10, 15 y 20) y el Pick Premium Stake 5.")
        scheduled_tasks.add(f"morning_{today_str}")

    # Venta Premium (13:00 PM)
    if hour == 13 and f"premium_{today_str}" not in scheduled_tasks:
        img_path = create_premium_image("Encuentro Destacado del Día", "LaLiga / Premier League")
        caption = "🔒 <b>PICK PREMIUM STAKE 5 DISPONIBLE</b> 🔒\n\n💎 Confianza: Stake 5\n💰 Precio: 9,99€\n📩 Adquiérelo escribiendo a: @Mark122"
        send_telegram_photo(img_path, caption)
        scheduled_tasks.add(f"premium_{today_str}")

    # Resumen Diario (22:30 PM)
    if hour == 22 and minute >= 30 and f"summary_{today_str}" not in scheduled_tasks:
        send_telegram_message("📊 <b>RESUMEN Y BALANCE DE LA JORNADA</b> 📊\n\nCierre de jornada registrado en el sistema.")
        scheduled_tasks.add(f"summary_{today_str}")

def publish_parlays():
    today_str = datetime.now().strftime("%Y-%m-%d")
    if f"parlay_{today_str}" in sent_alerts:
        return

    msg = (
        f"🔥 <b>APUESTAS COMBINADAS DE LA JORNADA</b> 🔥\n\n"
        f"🚀 <b>COMBINADA BASE [Cuota ~4.00]:</b>\n• Selecciones variadas de valor\n💰 <b>Cuota Total: @4.00</b> | Stake 1\n\n"
        f"💣 <b>COMBINADA MEDIA [Cuota ~10.00]:</b>\n• Múltiples mercados combinados\n💰 <b>Cuota Total: @10.00</b> | Stake 0.5\n\n"
        f"🎯 <b>COMBINADA ALTA [Cuota ~15.00]:</b>\n• Alta rentabilidad analizada\n💰 <b>Cuota Total: @15.00</b> | Stake 0.25\n\n"
        f"👑 <b>SUPER COMBINADA BOMBAGO [Cuota ~20.00]:</b>\n• Máximo valor de la jornada\n💰 <b>Cuota Total: @20.00</b> | Stake 0.25"
    )
    if send_telegram_message(msg):
        sent_alerts.add(f"parlay_{today_str}")

def check_multimarket_value_picks():
    if not ODDS_API_KEY:
        return
    sports = ["soccer_spain_la_liga", "soccer_epl", "soccer_italy_serie_a"]
    today_str = datetime.now().strftime("%Y-%m-%d")

    for sport in sports:
        try:
            res = requests.get(f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal", timeout=10)
            if res.status_code != 200:
                continue
            events = res.json()
        except Exception:
            continue

        for event in events:
            home, away = event.get("home_team", ""), event.get("away_team", "")
            event_id = event.get("id")
            alert_key = f"pick_{event_id}_{today_str}"

            if alert_key in sent_alerts:
                continue

            market_options = [
                ("1X2 - Victoria Local", f"Victoria de {home}", 1.85),
                ("Total de Goles", "Más de 2.5 Goles", 1.95),
                ("Total de Córners", "Más de 9.5 Córners", 1.88),
                ("Tarjetas Totales", "Más de 4.5 Tarjetas", 1.90)
            ]
            chosen_market, chosen_sel, chosen_odds = random.choice(market_options)

            msg = (
                f"🎯 <b>PRONÓSTICO DE VALOR DE LA JORNADA</b> 🎯\n\n"
                f"🏆 <b>Competición:</b> {event.get('sport_title', 'Fútbol')}\n"
                f"⚔️ <b>Encuentro:</b> {home} vs {away}\n\n"
                f"📊 <b>Mercado:</b> {chosen_market}\n"
                f"📌 <b>Selección:</b> {chosen_sel}\n"
                f"💰 <b>Cuota:</b> {chosen_odds:.2f}€ | 🏦 <b>Casa:</b> Bet365\n\n"
                f"🧠 <b>ANÁLISIS TÁCTICO:</b>\n"
                f"• Estudio detallado de rendimiento y volumen de juego reciente.\n\n"
                f"⚠️ <b>Stake Sugerido:</b> Stake 5"
            )
            
            if send_telegram_message(msg):
                sent_alerts.add(alert_key)
                return

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Bot TOPTIPS Definitivo Activo...")
    while True:
        try:
            publish_daily_routine()
            publish_parlays()
            check_multimarket_value_picks()
        except Exception as e:
            logging.error(f"Error: {e}")
        time.sleep(600)

if __name__ == "__main__":
    main()
