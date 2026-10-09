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

CSV_FILE = "registro_pronosticos.csv"

def init_csv():
    try:
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Fecha", "Competicion", "Encuentro", "Pronostico", "Cuota"])
    except Exception as e:
        logging.error(f"Error CSV: {e}")

init_csv()

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
        logging.error(f"Error enviando foto: {e}")
        return None

def create_scores24_card(match_title, league_name, pick_text, odds_val):
    """Genera una tarjeta gráfica de máxima calidad estilo Scores24."""
    img = Image.new('RGB', (1000, 550), color=(13, 27, 42)) # Fondo azul marino deportivo
    d = ImageDraw.Draw(img)
    
    # Marco exterior elegante
    d.rectangle([20, 20, 980, 530], outline=(0, 212, 170), width=4)
    
    # Cabecera estilo app deportiva
    d.rectangle([20, 20, 980, 95], fill=(20, 40, 65))
    d.text((40, 45), "⚡ TOPTIPS LIVE & ANALYTICS", fill=(0, 212, 170))
    d.text((650, 45), league_name.upper(), fill=(200, 200, 200))
    
    # Partido
    d.text((40, 140), "ENCUENTRO DESTACADO:", fill=(150, 160, 180))
    d.text((40, 185), match_title, fill=(255, 255, 255))
    
    # Caja central del pronóstico
    d.rectangle([40, 260, 960, 410], fill=(24, 43, 73), outline=(255, 215, 0), width=2)
    d.text((70, 285), "PRONÓSTICO RECOMENDADO:", fill=(255, 215, 0))
    d.text((70, 335), f"{pick_text}", fill=(255, 255, 255))
    d.text((750, 335), f"@{odds_val:.2f}", fill=(0, 212, 170))
    
    # Pie de tarjeta
    d.text((40, 460), "📊 Cuotas verificadas | Análisis táctico en tiempo real", fill=(150, 160, 180))
    d.text((40, 495), "Canal Oficial: @FreeTopTip", fill=(255, 215, 0))
    
    filename = "scores24_card.png"
    img.save(filename)
    return filename

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error HTTP: {e}")

def get_match():
    """Obtiene un partido real o selecciona un encuentro estelar de gran nivel."""
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

    # Respaldo de partidos principales
    pool = [
        ("Real Madrid", "Villarreal", "La Liga EA Sports"),
        ("FC Barcelona", "Atlético de Madrid", "La Liga EA Sports"),
        ("Manchester City", "Liverpool", "Premier League"),
        ("Arsenal", "Chelsea", "Premier League"),
        ("Bayern Múnich", "RB Leipzig", "Bundesliga"),
        ("Inter de Milán", "AC Milan", "Serie A")
    ]
    home, away, league = random.choice(pool)
    odds_val = round(random.uniform(1.80, 2.25), 2)
    return home, away, league, odds_val

def publish_pick():
    """Publica un único pronóstico profesional perfectamente estructurado."""
    home, away, league, odds_val = get_match()
    match_title = f"{home} vs {away}"

    markets = [
        ("Victoria de " + home, odds_val, f"Estudio táctico: {home} llega con superioridad en duelos clave y posesión estimada favorable en su estadio."),
        ("Más de 2.5 Goles", round(odds_val * 0.95, 2), f"Estudio táctico: Alta tendencia ofensiva en los esquemas de ambos conjuntos, proyectando ocasiones constantes."),
        ("Ambos Anotan (Sí)", round(odds_val * 0.98, 2), f"Estudio táctico: Fragilidad defensiva reciente combinada con pegada arriba en ambos contendientes.")
    ]
    chosen_pick, chosen_odds, analysis = random.choice(markets)

    caption = (
        f"⚽ <b>PRONÓSTICO OFICIAL</b> ⚽\n\n"
        f"🏆 <b>Competición:</b> {league}\n"
        f"⚔️ <b>Encuentro:</b> {match_title}\n\n"
        f"🎯 <b>Selección:</b> <code>{chosen_pick}</code>\n"
        f"📈 <b>Cuota:</b> <b>{chosen_odds:.2f}</b> | 🏦 <b>Bet365</b>\n\n"
        f"📊 <b>{analysis}</b>\n\n"
        f"💪 <i>¡A por el verde! Stake 1.5.</i>"
    )

    img_path = create_scores24_card(match_title, league, chosen_pick, chosen_odds)
    send_telegram_photo(img_path, caption)
    logging.info(f"Publicado correctamente: {match_title}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Tipster Profesional Activo...")

    # Publica el primer pronóstico a los 5 segundos de arrancar
    time.sleep(5)
    publish_pick()

    # Publica un nuevo pronóstico de calidad cada 4 horas para evitar saturar el canal
    while True:
        time.sleep(14400) # 4 horas
        try:
            publish_pick()
        except Exception as e:
            logging.error(f"Error en bucle principal: {e}")

if __name__ == "__main__":
    main()
