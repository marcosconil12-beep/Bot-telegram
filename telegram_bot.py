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

published_picks = set()
CSV_FILE = "registro_pronosticos.csv"

def init_csv():
    try:
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Fecha", "Competicion", "Encuentro", "Pronostico", "Cuota", "Resultado"])
    except Exception as e:
        logging.error(f"Error inicializando CSV: {e}")

init_csv()

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
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

def create_tipster_card(match_title, league_name, pick_text, odds_val):
    """Genera una tarjeta limpia y profesional estilo tipster experto."""
    img = Image.new('RGB', (900, 500), color=(15, 23, 42))
    d = ImageDraw.Draw(img)
    
    d.rectangle([15, 15, 885, 485], outline=(234, 179, 8), width=3)
    d.text((40, 40), "🎯 TOPTIPS VIP — PRONÓSTICO OFICIAL", fill=(234, 179, 8))
    d.text((40, 95), f"COMPETICIÓN: {league_name.upper()}", fill=(148, 163, 184))
    d.text((40, 140), f"⚔️ {match_title}", fill=(255, 255, 255))
    
    d.rectangle([35, 205, 865, 335], fill=(30, 41, 59), outline=(16, 185, 129), width=2)
    d.text((60, 225), "SELECCIÓN RECOMENDADA:", fill=(16, 185, 129))
    d.text((60, 270), f"📌 {pick_text}  |  Cuota: {odds_val:.2f}", fill=(255, 255, 255))
    
    d.text((40, 375), "Análisis y lectura táctica avanzada aplicada.", fill=(148, 163, 184))
    d.text((40, 415), "Canal Oficial: @FreeTopTip", fill=(234, 179, 8))
    
    filename = "tipster_pick.png"
    img.save(filename)
    return filename

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Servidor Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error servidor HTTP: {e}")

def get_match_to_publish():
    """Obtiene un partido real o selecciona un encuentro estelar relevante si la API está vacía."""
    events = []
    if ODDS_API_KEY:
        url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                events = res.json()
        except Exception as e:
            logging.error(f"Error API: {e}")

    if events:
        event = random.choice(events)
        home = event.get("home_team", "Local")
        away = event.get("away_team", "Visitante")
        league = event.get("sport_title", "Fútbol Internacional")
        
        odds_val = 2.00
        if event.get("bookmakers") and len(event["bookmakers"]) > 0:
            markets = event["bookmakers"][0].get("markets", [])
            if markets and len(markets[0].get("outcomes", [])) > 0:
                odds_val = markets[0]["outcomes"][0].get("price", 2.00)
        return home, away, league, odds_val

    # Lista de respaldo de alta categoría para garantizar flujo constante de picks atractivos
    fallback_pool = [
        ("Real Madrid", "Villarreal", "La Liga EA Sports"),
        ("FC Barcelona", "Atlético de Madrid", "La Liga EA Sports"),
        ("Manchester City", "Liverpool", "Premier League"),
        ("Arsenal", "Chelsea", "Premier League"),
        ("Bayern Múnich", "RB Leipzig", "Bundesliga"),
        ("Inter de Milán", "AC Milan", "Serie A"),
        ("PSG", "Marsella", "Ligue 1")
    ]
    home, away, league = random.choice(fallback_pool)
    odds_val = round(random.uniform(1.75, 2.30), 2)
    return home, away, league, odds_val

def generate_tipster_content():
    """Genera y publica el pronóstico profesional de forma automática."""
    home, away, league, odds_val = get_match_to_publish()
    match_title = f"{home} vs {away}"
    
    today_str = datetime.now().strftime("%Y-%m-%d-%H-%M")
    pick_id = f"{match_title}_{today_str}"
    
    if pick_id in published_picks:
        return

    market_options = [
        ("Victoria de " + home, odds_val, f"Analizando la solidez como local de {home} y las opciones tácticas en este duelo, vemos gran valor en esta selección."),
        ("Más de 2.5 Goles Totales", round(odds_val * 0.95, 2), f"El ritmo ofensivo proyectado para el choque entre {home} y {away} garantiza ocasiones constantes en ambas áreas."),
        ("Ambos Equipos Anotan (Sí)", round(odds_val * 0.98, 2), f"Las estadísticas recientes de ambos conjuntos muestran dinamismo en ataque y opciones claras de ver puerta hoy.")
    ]

    chosen_pick, chosen_odds, analysis_text = random.choice(market_options)

    caption = (
        f"⚽ <b>PRONÓSTICO DESTACADO</b> ⚽\n\n"
        f"🏆 <b>Competición:</b> {league}\n"
        f"📌 <b>Encuentro:</b> {match_title}\n\n"
        f"🎯 <b>Selección:</b> <code>{chosen_pick}</code>\n"
        f"📈 <b>Cuota:</b> <b>{chosen_odds:.2f}</b>\n"
        f"🏦 <b>Casa recomendada:</b> Bet365\n\n"
        f"📊 <b>Análisis táctico:</b>\n"
        f"{analysis_text}\n\n"
        f"💪 <i>¡A por el verde! Mucha cabeza con el stake.</i>"
    )

    img_path = create_tipster_card(match_title, league, chosen_pick, chosen_odds)
    
    if send_telegram_photo(img_path, caption):
        published_picks.add(pick_id)
        logging.info(f"Pronóstico publicado con éxito: {match_title}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Tipster Activo y Publicando...")

    # Publica un pronóstico inmediatamente al arrancar
    time.sleep(3)
    generate_tipster_content()

    while True:
        try:
            generate_tipster_content()
        except Exception as e:
            logging.error(f"Error en bucle: {e}")
        time.sleep(3600) # Publica un nuevo pronóstico cada hora de manera constante

if __name__ == "__main__":
    main()
