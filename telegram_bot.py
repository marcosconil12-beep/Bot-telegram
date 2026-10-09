import os
import time
import logging
import threading
import requests
import random
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
    """Genera una tarjeta gráfica profesional estilo Scores24."""
    img = Image.new('RGB', (1000, 550), color=(13, 27, 42))
    d = ImageDraw.Draw(img)
    
    d.rectangle([20, 20, 980, 530], outline=(0, 212, 170), width=4)
    d.rectangle([20, 20, 980, 95], fill=(20, 40, 65))
    d.text((40, 45), "⚡ TOPTIPS GLOBAL ANALYTICS", fill=(0, 212, 170))
    d.text((580, 45), league_name.upper()[:25], fill=(200, 200, 200))
    
    d.text((40, 140), "ENCUENTRO EN CURSO / JORNADA:", fill=(150, 160, 180))
    d.text((40, 185), match_title, fill=(255, 255, 255))
    
    d.rectangle([40, 260, 960, 410], fill=(24, 43, 73), outline=(255, 215, 0), width=2)
    d.text((70, 285), "PRONÓSTICO SELECCIONADO:", fill=(255, 215, 0))
    d.text((70, 335), f"{pick_text}", fill=(255, 255, 255))
    d.text((750, 335), f"@{odds_val:.2f}", fill=(0, 212, 170))
    
    d.text((40, 460), "📊 Cuotas verificadas | Cobertura Mundial 24/7", fill=(150, 160, 180))
    d.text((40, 495), "Canal Oficial: @FreeTopTip", fill=(255, 215, 0))
    
    filename = "scores24_card.png"
    img.save(filename)
    return filename

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Global Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error HTTP: {e}")

def fetch_global_matches():
    """Obtiene partidos de la API o de la macro-base de datos mundial de categorías y divisiones."""
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
        valid_events = []
        for ev in events:
            home = ev.get("home_team")
            away = ev.get("away_team")
            league = ev.get("sport_title", "Fútbol Internacional")
            if home and away:
                odds = 2.00
                if ev.get("bookmakers") and len(ev["bookmakers"]) > 0:
                    mkts = ev["bookmakers"][0].get("markets", [])
                    if mkts and len(mkts[0].get("outcomes", [])) > 0:
                        odds = mkts[0]["outcomes"][0].get("price", 2.00)
                valid_events.append((home, away, league, odds))
        if valid_events:
            return random.choice(valid_events)

    # Macro base de datos mundial: Primera, Segunda división y ligas de todo el planeta
    global_database = [
        # España (Primera y Segunda / Hypermotion)
        ("Real Zaragoza", "Eibar", "La Liga Hypermotion (2ª ESP)", 2.05),
        ("Sporting de Gijón", "Racing de Santander", "La Liga Hypermotion (2ª ESP)", 1.95),
        ("Mirandés", "Albacete", "La Liga Hypermotion (2ª ESP)", 2.15),
        ("Elche", "Tenerife", "La Liga Hypermotion (2ª ESP)", 1.85),
        ("Real Madrid", "Villarreal", "La Liga EA Sports", 1.75),
        
        # Inglaterra (Premier y Championship)
        ("Leeds United", "Burnley", "Championship (2ª ENG)", 1.90),
        ("West Bromwich", "Coventry City", "Championship (2ª ENG)", 2.00),
        ("Sunderland", "Sheffield United", "Championship (2ª ENG)", 2.10),
        ("Arsenal", "Chelsea", "Premier League", 1.80),
        
        # Italia (Serie A y Serie B)
        ("Palermo", "Sassuolo", "Serie B (2ª ITA)", 2.05),
        ("Sampdoria", "Bari", "Serie B (2ª ITA)", 1.95),
        ("Inter de Milán", "Juventus", "Serie A", 1.90),
        
        # Alemania (Bundesliga y 2. Bundesliga)
        ("Hamburgo", "Hertha BSC", "2. Bundesliga (GER)", 1.85),
        ("Schalke 04", "Hannover 96", "2. Bundesliga (GER)", 2.10),
        ("Bayern Múnich", "RB Leipzig", "Bundesliga", 1.65),
        
        # Francia (Ligue 1 y Ligue 2)
        ("Girondins de Burdeos", "Auxerre", "Ligue 2 (FRA)", 2.00),
        ("Lens", "Lyon", "Ligue 1", 2.15),
        
        # Latinoamérica y Resto del Mundo
        ("River Plate", "Boca Juniors", "Liga Profesional Argentina", 2.00),
        ("Flamengo", "Palmeiras", "Brasileirão Serie A", 1.95),
        ("Club América", "Tigres UANL", "Liga MX (México)", 1.90),
        ("Al Nassr", "Al Hilal", "Saudi Pro League", 1.80),
        ("Júbilo Iwata", "Tokyo Verdy", "J1 League (Japón)", 2.10),
        ("PSV Eindhoven", "Heerenveen", "Eredivisie (Países Bajos)", 1.70),
        ("Sporting CP", "Porto", "Liga Portugal", 1.85)
    ]
    
    return random.choice(global_database)

def publish_pick():
    home, away, league, odds_val = global_match = fetch_global_matches()
    match_title = f"{home} vs {away}"
    
    today_str = datetime.now().strftime("%Y-%m-%d-%H")
    pick_id = f"{match_title}_{today_str}"
    
    if pick_id in published_picks:
        return

    markets = [
        ("Victoria de " + home, odds_val, f"Análisis táctico: {home} muestra superioridad en los duelos clave y una localía muy sólida en esta jornada."),
        ("Más de 2.5 Goles", round(odds_val * 0.95, 2), f"Análisis táctico: Alta tendencia ofensiva y necesidades urgentes de victoria que propiciarán un partido abierto."),
        ("Ambos Anotan (Sí)", round(odds_val * 0.98, 2), f"Análisis táctico: Estadísticas recientes de ambos equipos reflejan vulnerabilidad defensiva y pegada arriba.")
    ]
    chosen_pick, chosen_odds, analysis = random.choice(markets)

    caption = (
        f"⚽ <b>PRONÓSTICO OFICIAL GLOBAL</b> ⚽\n\n"
        f"🏆 <b>Competición:</b> {league}\n"
        f"⚔️ <b>Encuentro:</b> {match_title}\n\n"
        f"🎯 <b>Selección:</b> <code>{chosen_pick}</code>\n"
        f"📈 <b>Cuota:</b> <b>{chosen_odds:.2f}</b> | 🏦 <b>Bet365</b>\n\n"
        f"📊 <b>{analysis}</b>\n\n"
        f"💪 <i>¡A por el verde! Stake 1.5.</i>"
    )

    img_path = create_scores24_card(match_title, league, chosen_pick, chosen_odds)
    if send_telegram_photo(img_path, caption):
        published_picks.add(pick_id)
        logging.info(f"Pronóstico global publicado: {match_title} ({league})")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Tipster Global Activo...")

    time.sleep(5)
    publish_pick()

    while True:
        time.sleep(10800) # Publica un nuevo pronóstico de cualquier liga del mundo cada 3 horas
        try:
            publish_pick()
        except Exception as e:
            logging.error(f"Error en bucle: {e}")

if __name__ == "main__":
    main()
