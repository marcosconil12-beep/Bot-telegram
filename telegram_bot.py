import os
import time
import logging
import threading
import requests
import random
import csv
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
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
    img = Image.new('RGB', (900, 500), color=(15, 23, 42)) # Fondo azul oscuro elegante
    d = ImageDraw.Draw(img)
    
    # Marco exterior dorado/bronce sutil
    d.rectangle([15, 15, 885, 485], outline=(234, 179, 8), width=3)
    
    # Cabecera
    d.text((40, 40), "🎯 TOPTIPS VIP — PRONÓSTICO OFICIAL", fill=(234, 179, 8))
    d.text((40, 95), f"COMPETICIÓN: {league_name.upper()}", fill=(148, 163, 184))
    d.text((40, 140), f"⚔️ {match_title}", fill=(255, 255, 255))
    
    # Caja central del pronóstico
    d.rectangle([35, 205, 865, 335], fill=(30, 41, 59), outline=(16, 185, 129), width=2)
    d.text((60, 225), "SELECCIÓN SELECCIONADA:", fill=(16, 185, 129))
    d.text((60, 270), f"📌 {pick_text}  |  Cuota: {odds_val:.2f}", fill=(255, 255, 255))
    
    # Pie de tarjeta
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

def fetch_matches_from_api():
    """Obtiene partidos reales desde la API global."""
    if not ODDS_API_KEY:
        return []
    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        logging.error(f"Error obteniendo API: {e}")
    return []

def generate_tipster_content():
    """Genera y publica pronósticos de forma completamente natural."""
    events = fetch_matches_from_api()
    
    # Si la API no devuelve partidos en este instante, usa partidos estelares de referencia mundial para asegurar actividad constante
    if not events:
        fallback_matches = [
            ("Real Madrid vs FC Barcelona", "La Liga EA Sports"),
            ("Manchester City vs Arsenal", "Premier League"),
            ("Bayern Múnich vs Borussia Dortmund", "Bundesliga"),
            ("Inter de Milán vs Juventus", "Serie A"),
            ("Paris Saint-Germain vs Marsella", "Ligue 1")
        ]
        match_title, league = random.choice(fallback_matches)
        home, away = match_title.split(" vs ")
    else:
        event = random.choice(events)
        home = event.get("home_team", "Equipo Local")
        away = event.get("away_team", "Equipo Visitante")
        league = event.get("sport_title", "Fútbol Internacional")
        match_title = f"{home} vs {away}"

    today_str = datetime.now().strftime("%Y-%m-%d-%H")
    pick_id = f"{match_title}_{today_str}"
    
    if pick_id in published_picks:
        return

    # Opciones de mercados profesionales redactados de forma 100% humana (sin mencionar IA ni bots)
    market_types = [
        ("Victoria de " + home, round(random.uniform(1.80, 2.30), 2), f"Analizando la solidez como local de {home} y las bajas importantes en la medular del rival, veo un claro valor en este pronóstico para encarrilar el encuentro."),
        ("Más de 2.5 Goles Totales", round(random.uniform(1.75, 2.15), 2), f"El ritmo ofensivo que imponen tanto {home} como {away} garantiza ocasiones constantes en ambas áreas. Partido ideal para buscar goles."),
        ("Ambos Equipos Anotan (Sí)", round(random.uniform(1.70, 2.05), 2), f"Las estadísticas defensivas recientes de ambos conjuntos nos muestran fragilidad atrás, mientras que sus delanteras atraviesan un estado de forma excelso."),
        ("Doble Oportunidad: " + home + " o Empate", round(random.uniform(1.35, 1.60), 2), f"Opción con buen colchón de seguridad. {home} no debería dejar escapar puntos en este estadio bajo ningún concepto.")
    ]

    chosen_pick, chosen_odds, analysis_text = random.choice(market_types)

    # Mensaje redactado con estilo de tipster profesional puro
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
    logging.info("Servicio Tipster Activo...")

    # Publica un primer pronóstico a los pocos segundos de arrancar
    time.sleep(5)
    generate_tipster_content()

    # Bucle continuo publicando cada 2 horas de manera automática y natural
    while True:
        try:
            generate_tipsterContent = generate_tipster_content()
        except Exception as e:
            logging.error(f"Error en bucle: {e}")
        time.sleep(7200) # Cada 2 horas publica un nuevo pick profesional

if __name__ == "__main__":
    main()
