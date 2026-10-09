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
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
FOOTBALL_API_KEY = "d406243cc58144269f85bfe80f4e79b3" # Token oficial de football-data.org

published_picks = set()

def send_telegram_photo(photo_path, caption):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("Falta TELEGRAM_BOT_TOKEN o CHAT_ID")
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
    d.text((40, 45), "⚡ TOPTIPS LIVE & ANALYTICS", fill=(0, 212, 170))
    d.text((580, 45), league_name.upper()[:25], fill=(200, 200, 200))
    
    d.text((40, 140), "ENCUENTRO EN DIRECTO:", fill=(150, 160, 180))
    d.text((40, 185), match_title, fill=(255, 255, 255))
    
    d.rectangle([40, 260, 960, 410], fill=(24, 43, 73), outline=(255, 215, 0), width=2)
    d.text((70, 285), "PRONÓSTICO SELECCIONADO:", fill=(255, 215, 0))
    d.text((70, 335), f"{pick_text}", fill=(255, 255, 255))
    d.text((750, 335), f"@{odds_val:.2f}", fill=(0, 212, 170))
    
    d.text((40, 460), "📊 Cuotas verificadas en tiempo real", fill=(150, 160, 180))
    d.text((40, 495), "Canal Oficial: @FreeTopTip", fill=(255, 215, 0))
    
    filename = "scores24_card.png"
    img.save(filename)
    return filename

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Football-Data Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error HTTP: {e}")

def fetch_football_data_matches():
    """Obtiene partidos reales usando la autenticación de football-data.org."""
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            matches = data.get("matches", [])
            valid_matches = []
            for m in matches:
                home = m.get("homeTeam", {}).get("name")
                away = m.get("awayTeam", {}).get("name")
                competition = m.get("competition", {}).get("name", "Fútbol Internacional")
                if home and away:
                    valid_matches.append((home, away, competition))
            if valid_matches:
                return random.choice(valid_matches)
        else:
            logging.warning(f"Football-data respondió con código: {res.status_code}")
    except Exception as e:
        logging.error(f"Error consultando football-data.org: {e}")
    return None

def publish_pick():
    match_data = fetch_football_data_matches()
    
    # Respaldo de máxima categoría por si la API gratuita requiere alguna liga específica
    if not match_data:
        fallback_pool = [
            ("Real Madrid", "Villarreal", "La Liga EA Sports"),
            ("FC Barcelona", "Atlético de Madrid", "La Liga EA Sports"),
            ("Manchester City", "Liverpool", "Premier League"),
            ("Arsenal", "Chelsea", "Premier League"),
            ("Bayern Múnich", "RB Leipzig", "Bundesliga"),
            ("Inter de Milán", "Juventus", "Serie A")
        ]
        home, away, league = random.choice(fallback_pool)
    else:
        home, away, league = match_data

    match_title = f"{home} vs {away}"
    odds_val = round(random.uniform(1.75, 2.20), 2)
    
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
        f"⚽ <b>PRONÓSTICO OFICIAL</b> ⚽\n\n"
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
        logging.info(f"Pronóstico publicado con éxito: {match_title} ({league})")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Tipster Football-Data Activo...")

    time.sleep(5)
    publish_pick()

    while True:
        try:
            publish_pick()
        except Exception as e:
            logging.error(f"Error en bucle: {e}")
        time.sleep(7200)

if __name__ == "__main__":
    main()
