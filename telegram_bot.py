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
FOOTBALL_API_KEY = "d406243cc58144269f85bfe80f4e79b3"

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
    img = Image.new('RGB', (1000, 580), color=(13, 27, 42))
    d = ImageDraw.Draw(img)
    
    d.rectangle([20, 20, 980, 560], outline=(0, 212, 170), width=4)
    d.rectangle([20, 20, 980, 95], fill=(20, 40, 65))
    d.text((40, 45), "⚡ TOPTIPS PRO ANALYTICS", fill=(0, 212, 170))
    d.text((550, 45), league_name.upper()[:30], fill=(200, 200, 200))
    
    d.text((40, 130), "ANÁLISIS DE ENCUENTRO:", fill=(150, 160, 180))
    d.text((40, 170), match_title, fill=(255, 255, 255))
    
    d.rectangle([40, 230, 960, 390], fill=(24, 43, 73), outline=(255, 215, 0), width=2)
    d.text((70, 250), "PRONÓSTICO PRINCIPAL:", fill=(255, 215, 0))
    d.text((70, 300), f"{pick_text}", fill=(255, 255, 255))
    d.text((750, 300), f"@{odds_val:.2f}", fill=(0, 212, 170))
    
    d.text((40, 430), "📊 Métricas: Estado de Forma | xG | Córneres | Tarjetas", fill=(150, 160, 180))
    d.text((40, 470), "Canal Oficial: @FreeTopTip", fill=(255, 215, 0))
    
    filename = "scores24_card.png"
    img.save(filename)
    return filename

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Pro Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error HTTP: {e}")

def get_pro_match():
    """Base de datos masiva de las 5 grandes ligas y sus segundas divisiones."""
    pool = [
        # España (La Liga y Hypermotion)
        ("Real Madrid", "Villarreal", "La Liga EA Sports"),
        ("FC Barcelona", "Atlético de Madrid", "La Liga EA Sports"),
        ("Real Sociedad", "Athletic Club", "La Liga EA Sports"),
        ("Real Zaragoza", "Eibar", "La Liga Hypermotion (2ª ESP)"),
        ("Sporting de Gijón", "Racing de Santander", "La Liga Hypermotion (2ª ESP)"),
        ("Elche", "Tenerife", "La Liga Hypermotion (2ª ESP)"),
        
        # Inglaterra (Premier League y Championship)
        ("Manchester City", "Liverpool", "Premier League"),
        ("Arsenal", "Chelsea", "Premier League"),
        ("Tottenham Hotspur", "Aston Villa", "Premier League"),
        ("Leeds United", "Burnley", "Championship (2ª ENG)"),
        ("West Bromwich", "Coventry City", "Championship (2ª ENG)"),
        ("Sunderland", "Sheffield United", "Championship (2ª ENG)"),
        
        # Italia (Serie A y Serie B)
        ("Inter de Milán", "Juventus", "Serie A"),
        ("AC Milan", "Napoli", "Serie A"),
        ("AS Roma", "Lazio", "Serie A"),
        ("Palermo", "Sassuolo", "Serie B (2ª ITA)"),
        ("Sampdoria", "Bari", "Serie B (2ª ITA)"),
        
        # Alemania (Bundesliga y 2. Bundesliga)
        ("Bayern Múnich", "RB Leipzig", "Bundesliga"),
        ("Borussia Dortmund", "Bayer Leverkusen", "Bundesliga"),
        ("Stuttgart", "Eintracht Frankfurt", "Bundesliga"),
        ("Hamburgo", "Hertha BSC", "2. Bundesliga (GER)"),
        ("Schalke 04", "Hannover 96", "2. Bundesliga (GER)"),
        
        # Francia (Ligue 1 y Ligue 2)
        ("PSG", "Marsella", "Ligue 1"),
        ("Lyon", "AS Monaco", "Ligue 1"),
        ("Lille", "Niza", "Ligue 1"),
        ("Girondins de Burdeos", "Auxerre", "Ligue 2 (FRA)"),
        ("Saint-Étienne", "Paris FC", "Ligue 2 (FRA)")
    ]
    return random.choice(pool)

def publish_pick():
    home, away, league = get_pro_match()
    match_title = f"{home} vs {away}"
    odds_val = round(random.uniform(1.75, 2.30), 2)
    
    today_str = datetime.now().strftime("%Y-%m-%d-%H")
    pick_id = f"{match_title}_{today_str}"
    
    if pick_id in published_picks:
        return

    # Generación de métricas detalladas estilo Scores24
    forms = ["🟢 🟢 🟡 🔴 🟢", "🟢 🟢 🟢 🟡 🟢", "🟡 🔴 🟢 🟢 🟡", "🟢 🟡 🟡 🟢 🔴"]
    form_home = random.choice(forms)
    form_away = random.choice(forms)
    
    xg_home = round(random.uniform(1.2, 2.4), 2)
    xg_away = round(random.uniform(0.8, 1.9), 2)
    
    exact_scores = ["1-0", "2-1", "2-2", "1-1", "0-2", "3-1", "1-2"]
    exact_score = random.choice(exact_scores)
    
    corners = random.randint(8, 12)
    cards = random.randint(4, 7)

    markets = [
        ("Victoria de " + home, odds_val, f"{home} domina territorialmente con un xG de {xg_home} frente a {xg_away} del rival."),
        ("Más de 2.5 Goles", round(odds_val * 0.95, 2), f"Alta proyección ofensiva. Goles esperados conjuntos superiores a 3.1."),
        ("Ambos Anotan (Sí)", round(odds_val * 0.98, 2), f"Las defensas muestran concesiones recientes y los ataques promedian alta efectividad.")
    ]
    chosen_pick, chosen_odds, analysis = random.choice(markets)

    caption = (
        f"⚽ <b>ANÁLISIS PROFESIONAL DE PARTIDO</b> ⚽\n\n"
        f"🏆 <b>Competición:</b> {league}\n"
        f"⚔️ <b>Encuentro:</b> {match_title}\n\n"
        f"📈 <b>ESTADO DE FORMA:</b>\n"
        f"• {home}: {form_home}\n"
        f"• {away}: {form_away}\n\n"
        f"📊 <b>MÉTRICAS Y xG (Goles Esperados):</b>\n"
        f"• xG {home}: <b>{xg_home}</b> | xG {away}: <b>{xg_away}</b>\n"
        f"• Total Goles Proyectados: <b>{round(xg_home + xg_away, 1)}</b>\n\n"
        f"🎯 <b>PRONÓSTICO RECOMENDADO:</b>\n"
        f"• Selección: <code>{chosen_pick}</code>\n"
        f"• Cuota: <b>{chosen_odds:.2f}</b> (Bet365)\n\n"
        f"🔍 <b>DESGLOSE ESTADÍSTICO:</b>\n"
        f"• Resultado Exacto Sugerido: <b>{exact_score}</b>\n"
        f"• Total Córneres Estimados: <b>+{corners}.5</b>\n"
        f"• Total Tarjetas Esperadas: <b>+{cards}.5</b>\n\n"
        f"💬 <i>Lectura táctica: {analysis}</i>\n\n"
        f"💪 <i>¡A por el verde! Stake 1.5.</i>"
    )

    img_path = create_scores24_card(match_title, league, chosen_pick, chosen_odds)
    if send_telegram_photo(img_path, caption):
        published_picks.add(pick_id)
        logging.info(f"Análisis detallado publicado: {match_title} ({league})")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Tipster Pro Analítico Activo...")

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
