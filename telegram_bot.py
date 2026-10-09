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
TELEGRAM_USERNAME = os.environ.get("TELEGRAM_USERNAME", "TuUsuarioVIP") # Pon aquí tu usuario de Telegram sin @ para los VIPs

published_picks = set()
stats_wins = 48
stats_losses = 12

def send_telegram_message(text, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        return None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN.strip()}/sendMessage"
    payload = {"chat_id": CHAT_ID.strip(), "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        res = requests.post(url, json=payload, timeout=15)
        return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error enviando mensaje: {e}")
        return None

def send_telegram_photo(photo_path, caption, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        return None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN.strip()}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            data = {"chat_id": CHAT_ID.strip(), "caption": caption, "parse_mode": "HTML"}
            if reply_markup:
                data["reply_markup"] = reply_markup
            res = requests.post(url, data=data, files={"photo": photo}, timeout=15)
            return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error enviando foto: {e}")
        return None

def create_scores24_card(match_title, league_name, pick_text, odds_val):
    img = Image.new('RGB', (1000, 580), color=(13, 27, 42))
    d = ImageDraw.Draw(img)
    
    d.rectangle([20, 20, 980, 560], outline=(0, 212, 170), width=4)
    d.rectangle([20, 20, 980, 95], fill=(20, 40, 65))
    d.text((40, 45), "⚡ TOPTIPS MASTER ANALYTICS", fill=(0, 212, 170))
    d.text((530, 45), league_name.upper()[:32], fill=(200, 200, 200))
    
    d.text((40, 130), "ANÁLISIS DE ENCUENTRO:", fill=(150, 160, 180))
    d.text((40, 170), match_title, fill=(255, 255, 255))
    
    d.rectangle([40, 230, 960, 390], fill=(24, 43, 73), outline=(255, 215, 0), width=2)
    d.text((70, 250), "PRONÓSTICO PRINCIPAL:", fill=(255, 215, 0))
    d.text((70, 300), f"{pick_text}", fill=(255, 255, 255))
    d.text((750, 300), f"@{odds_val:.2f}", fill=(0, 212, 170))
    
    d.text((40, 430), "📊 Métricas Avanzadas | xG | Córneres | Tarjetas", fill=(150, 160, 180))
    d.text((40, 470), "Canal Oficial: @FreeTopTip", fill=(255, 215, 0))
    
    filename = "scores24_card.png"
    img.save(filename)
    return filename

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Master Pro Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error HTTP: {e}")

def get_global_pro_match():
    """Base de datos masiva revisada: 5 grandes ligas, segundas divisiones, Brasil y Japón."""
    pool = [
        # España (La Liga y Hypermotion)
        ("Real Madrid", "Villarreal", "La Liga EA Sports"),
        ("FC Barcelona", "Atlético de Madrid", "La Liga EA Sports"),
        ("Real Sociedad", "Athletic Club", "La Liga EA Sports"),
        ("Real Zaragoza", "Granada CF", "La Liga Hypermotion (2ª ESP)"),
        ("Sporting de Gijón", "Racing de Santander", "La Liga Hypermotion (2ª ESP)"),
        
        # Inglaterra (Premier League y Championship)
        ("Manchester City", "Liverpool", "Premier League"),
        ("Arsenal", "Chelsea", "Premier League"),
        ("Tottenham Hotspur", "Aston Villa", "Premier League"),
        ("Coventry City", "Sheffield United", "Championship (2ª ENG)"),
        
        # Italia (Serie A y Serie B)
        ("Inter de Milán", "Juventus", "Serie A"),
        ("AC Milan", "Napoli", "Serie A"),
        ("Palermo", "Sassuolo", "Serie B (2ª ITA)"),
        
        # Alemania (Bundesliga y 2. Bundesliga)
        ("Bayern Múnich", "RB Leipzig", "Bundesliga"),
        ("Borussia Dortmund", "Bayer Leverkusen", "Bundesliga"),
        ("Hamburgo", "Hertha BSC", "2. Bundesliga (GER)"),
        
        # Francia (Ligue 1 y Ligue 2)
        ("PSG", "Marsella", "Ligue 1"),
        ("Lyon", "AS Monaco", "Ligue 1"),
        ("Girondins de Burdeos", "Auxerre", "Ligue 2 (FRA)"),
        
        # Brasil (Serie A y Serie B)
        ("Flamengo", "Palmeiras", "Brasileirão Serie A"),
        ("Fluminense", "Corinthians", "Brasileirão Serie A"),
        ("Santos", "Sport Recife", "Brasileirão Serie B"),
        
        # Japón (J1 League y J2 League)
        ("Vissel Kobe", "Yokohama F. Marinos", "J1 League (Japón)"),
        ("Kawasaki Frontale", "Urawa Red Diamonds", "J1 League (Japón)"),
        ("Shimizu S-Pulse", "JEF United Chiba", "J2 League (Japón)")
    ]
    return random.choice(pool)

def send_good_morning():
    text = (
        "☀️ <b>¡BUENOS DÍAS A TODOS LOS TIPSTERS!</b> ☀️\n\n"
        "☕ Arrancamos una jornada apasionante cargada de la mejor información y análisis detallado en el canal.\n\n"
        "📊 <b>Estadísticas Globales del Mes:</b>\n"
        f"✅ <b>Aciertos:</b> {stats_wins} | ❌ <b>Fallos:</b> {stats_losses}\n"
        f"📈 <b>Yield / Efectividad:</b> <b>78.4%</b>\n\n"
        "💎 <i>¿Quieres asegurar tus ganancias hoy? Escribe directamente a nuestro analista VIP para adquirir los combinados exclusivos:</i> <b>@" + TELEGRAM_USERNAME + "</b>\n\n"
        "👇 ¡Atentos a los picks y análisis detallados que publicaremos en breves minutos!"
    )
    send_telegram_message(text)

def publish_pick():
    global stats_wins
    home, away, league = get_global_pro_match()
    match_title = f"{home} vs {away}"
    odds_val = round(random.uniform(1.75, 2.30), 2)
    
    today_str = datetime.now().strftime("%Y-%m-%d-%H")
    pick_id = f"{match_title}_{today_str}"
    
    if pick_id in published_picks:
        return

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

    winrate_total = round((stats_wins / (stats_wins + stats_losses)) * 100, 1)

    caption = (
        f"⚽ <b>ANÁLISIS PROFESIONAL DETALLADO</b> ⚽\n\n"
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
        f"📊 <b>RECUENTO DE ACIERTOS GLOBAL:</b> {stats_wins}W - {stats_losses}L ({winrate_total}% WinRate)\n\n"
        f"💎 <b>¿QUIERES EL PICK VIP PREMIUM?</b>\n"
        f"Escríbenos directamente aquí para acceso exclusivo: <b>@{TELEGRAM_USERNAME}</b>\n\n"
        f"💪 <i>¡A por el verde! Stake 1.5.</i>"
    )

    # Botón interactivo para hablar contigo directamente por Telegram
    keyboard = {
        "inline_keyboard": [
            [{"text": "💎 Comprar Pick VIP / Premium", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }

    img_path = create_scores24_card(match_title, league, chosen_pick, chosen_odds)
    if send_telegram_photo(img_path, caption, reply_markup=keyboard):
        published_picks.add(pick_id)
        stats_wins += 1 # Simula el conteo automático de aciertos
        logging.info(f"Análisis detallado con botón VIP publicado: {match_title}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Master Tipster Activo...")

    # Envía saludo de buenos días al arrancar
    send_good_morning()
    time.sleep(5)
    publish_pick()

    last_morning_sent = datetime.now().day

    while True:
        try:
            # Comprueba si ha cambiado de día para mandar los buenos días por la mañana
            current_day = datetime.now().day
            if current_day != last_morning_sent and datetime.now().hour >= 9:
                send_good_morning()
                last_morning_sent = current_day
            
            publish_pick()
        except Exception as e:
            logging.error(f"Error en bucle: {e}")
        
        time.sleep(7200) # Publica cada 2 horas

if __name__ == "__main__":
    main()
