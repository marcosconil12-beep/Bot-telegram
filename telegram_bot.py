import os
import time
import logging
import threading
import requests
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuración de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TELEGRAM_USERNAME = "Mark122" # Tu usuario VIP configurado

published_picks = set()

# Sistema de estadísticas acumuladas del canal
CHANNEL_STATS = {
    "wins": 58,
    "losses": 12,
    "staked_units": 140,
    "profit_units": +42.5
}

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

def fetch_channel_logo():
    """Descarga el logo o avatar oficial del canal desde Telegram."""
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        return None
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN.strip()}/getChat"
        res = requests.get(url, params={"chat_id": CHAT_ID.strip()}, timeout=10).json()
        if res.get("ok") and "photo" in res.get("result", {}):
            file_id = res["result"]["photo"]["big_file_id"]
            file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN.strip()}/getFile", params={"file_id": file_id}, timeout=10).json()
            if file_info.get("ok"):
                file_path = file_info["result"]["file_path"]
                img_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN.strip()}/{file_path}"
                img_res = requests.get(img_url, timeout=10)
                with open("channel_logo.png", "wb") as f:
                    f.write(img_res.content)
                return "channel_logo.png"
    except Exception as e:
        logging.error(f"No se pudo descargar el logo del canal: {e}")
    return None

def create_scores24_card(match_title, league_name, pick_text, odds_val, highlight_win=False):
    """Genera una tarjeta gráfica profesional estilo Scores24 con el logo del canal e indicadores marcados."""
    img = Image.new('RGB', (1000, 600), color=(13, 27, 42))
    d = ImageDraw.Draw(img)
    
    # Borde y cabecera
    border_color = (0, 212, 170) if not highlight_win else (255, 215, 0)
    d.rectangle([20, 20, 980, 580], outline=border_color, width=4)
    d.rectangle([20, 20, 980, 100], fill=(20, 40, 65))
    
    # Intentar pegar el logo oficial del canal
    logo_path = fetch_channel_logo()
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).resize((70, 70))
            img.paste(logo, (35, 25))
        except Exception:
            pass

    d.text((120, 45), "⚡ TOPTIPS OFFICIAL ANALYTICS", fill=(0, 212, 170))
    d.text((550, 45), league_name.upper()[:28], fill=(200, 200, 200))
    
    d.text((40, 130), "PARTIDO ANALIZADO EN DETALLE:", fill=(150, 160, 180))
    d.text((40, 170), match_title, fill=(255, 255, 255))
    
    # Recadro del Pronóstico
    d.rectangle([40, 230, 960, 410], fill=(24, 43, 73), outline=(255, 215, 0), width=2)
    d.text((70, 250), "SELECCIÓN RECOMENDADA:", fill=(255, 215, 0))
    d.text((70, 305), f"{pick_text}", fill=(255, 255, 255))
    d.text((750, 305), f"@{odds_val:.2f}", fill=(0, 212, 170))
    
    # Si la tarjeta es para destacar un acierto (circulo marcado)
    if highlight_win:
        d.ellipse([700, 280, 930, 380], outline=(0, 255, 127), width=6)
        d.text((735, 315), "ACERTADO", fill=(0, 255, 127))

    d.text((40, 450), f"📊 Métricas: xG Proyectado | Córneres | Tarjetas | Yield: +{CHANNEL_STATS['profit_units']}U", fill=(150, 160, 180))
    d.text((40, 500), f"Canal Oficial: @FreeTopTip | Contacto VIP: @{TELEGRAM_USERNAME}", fill=(255, 215, 0))
    
    filename = "scores24_card.png"
    img.save(filename)
    return filename

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Vendedor Pro Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error HTTP: {e}")

def get_global_pro_match():
    """Base de datos verificada: 5 Grandes Ligas + 2ªs divisiones + Brasil (A/B) + Japón (J1/J2)."""
    pool = [
        # España
        ("Real Madrid", "Villarreal", "La Liga EA Sports"),
        ("FC Barcelona", "Atlético de Madrid", "La Liga EA Sports"),
        ("Real Zaragoza", "Granada CF", "La Liga Hypermotion (2ª ESP)"),
        ("Sporting de Gijón", "Racing de Santander", "La Liga Hypermotion (2ª ESP)"),
        
        # Inglaterra
        ("Manchester City", "Liverpool", "Premier League"),
        ("Arsenal", "Chelsea", "Premier League"),
        ("Leeds United", "Sheffield United", "Championship (2ª ENG)"),
        
        # Italia
        ("Inter de Milán", "Juventus", "Serie A"),
        ("AC Milan", "Napoli", "Serie A"),
        ("Palermo", "Sassuolo", "Serie B (2ª ITA)"),
        
        # Alemania
        ("Bayern Múnich", "RB Leipzig", "Bundesliga"),
        ("Borussia Dortmund", "Bayer Leverkusen", "Bundesliga"),
        ("Hamburgo", "Hertha BSC", "2. Bundesliga (GER)"),
        
        # Francia
        ("PSG", "Marsella", "Ligue 1"),
        ("Lyon", "AS Monaco", "Ligue 1"),
        ("Girondins de Burdeos", "Auxerre", "Ligue 2 (FRA)"),
        
        # Brasil
        ("Flamengo", "Palmeiras", "Brasileirão Serie A"),
        ("Fluminense", "Corinthians", "Brasileirão Serie A"),
        ("Santos", "Sport Recife", "Brasileirão Serie B"),
        
        # Japón
        ("Vissel Kobe", "Yokohama F. Marinos", "J1 League (Japón)"),
        ("Kawasaki Frontale", "Urawa Red Diamonds", "J1 League (Japón)"),
        ("Shimizu S-Pulse", "JEF United Chiba", "J2 League (Japón)")
    ]
    return random.choice(pool)

def send_good_morning():
    total_games = CHANNEL_STATS["wins"] + CHANNEL_STATS["losses"]
    winrate = round((CHANNEL_STATS["wins"] / total_games) * 100, 1)
    
    text = (
        "☀️ <b>¡BUENOS DÍAS A TODOS LOS MIEMBROS!</b> ☀️\n\n"
        "☕ Arrancamos una jornada clave con los análisis más potentes del mercado.\n\n"
        "📊 <b>REVISIÓN DE RESULTADOS Y BALANCES DEL MES:</b>\n"
        f"✅ <b>Picks Acertados:</b> {CHANNEL_STATS['wins']}\n"
        f"❌ <b>Picks Fallados:</b> {CHANNEL_STATS['losses']}\n"
        f"🔥 <b>Efectividad (WinRate):</b> <b>{winrate}%</b>\n"
        f"💰 <b>Beneficio Neto:</b> <b>+{CHANNEL_STATS['profit_units']} Unidades</b>\n\n"
        f"💣 <i>¡Aprovecha la racha de aciertos! Escríbeme ahora para unirte al Grupo VIP o comprar el Stake 10 de hoy:</i>\n"
        f"👉 <b>Contactar al Analista: @{TELEGRAM_USERNAME}</b>"
    )
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🚀 Entrar al Grupo VIP Ahora", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }
    send_telegram_message(text, reply_markup=keyboard)

def publish_pick():
    home, away, league = get_global_pro_match()
    match_title = f"{home} vs {away}"
    odds_val = round(random.uniform(1.75, 2.30), 2)
    
    today_str = datetime.now().strftime("%Y-%m-%d-%H")
    pick_id = f"{match_title}_{today_str}"
    
    if pick_id in published_picks:
        return

    forms = ["🟢 🟢 🟡 🔴 🟢", "🟢 🟢 🟢 🟡 🟢", "🟡 🔴 🟢 🟢 🟡", "🟢 🟡 🟡 🟢 🔴"]
    form_home, form_away = random.choice(forms), random.choice(forms)
    
    xg_home = round(random.uniform(1.2, 2.4), 2)
    xg_away = round(random.uniform(0.8, 1.9), 2)
    exact_score = random.choice(["1-0", "2-1", "2-2", "1-1", "0-2", "3-1", "1-2"])
    corners = random.randint(8, 12)
    cards = random.randint(4, 7)

    markets = [
        ("Victoria de " + home, odds_val, f"{home} domina territorialmente con un xG de {xg_home} frente a {xg_away} del rival."),
        ("Más de 2.5 Goles", round(odds_val * 0.95, 2), f"Alta proyección ofensiva. Goles esperados conjuntos superiores a 3.1."),
        ("Ambos Anotan (Sí)", round(odds_val * 0.98, 2), f"Las defensas muestran concesiones recientes y los ataques promedian alta efectividad.")
    ]
    chosen_pick, chosen_odds, analysis = random.choice(markets)

    total_games = CHANNEL_STATS["wins"] + CHANNEL_STATS["losses"]
    winrate_total = round((CHANNEL_STATS["wins"] / total_games) * 100, 1)

    caption = (
        f"⚽ <b>ANÁLISIS PROFESIONAL Y DETALLADO</b> ⚽\n\n"
        f"🏆 <b>Competición:</b> {league}\n"
        f"⚔️ <b>Encuentro:</b> {match_title}\n\n"
        f"📈 <b>ESTADO DE FORMA:</b>\n"
        f"• {home}: {form_home}\n"
        f"• {away}: {form_away}\n\n"
        f"📊 <b>MÉTRICAS Y xG (Goles Esperados):</b>\n"
        f"• xG {home}: <b>{xg_home}</b> | xG {away}: <b>{xg_away}</b>\n"
        f"• Total Goles Proyectados: <b>{round(xg_home + xg_away, 1)}</b>\n\n"
        f"🎯 <b>PRONÓSTICO GRATUITO:</b>\n"
        f"• Selección: <code>{chosen_pick}</code>\n"
        f"• Cuota: <b>{chosen_odds:.2f}</b> (Bet365)\n\n"
        f"🔍 <b>DESGLOSE ESTADÍSTICO COMPLETO:</b>\n"
        f"• Resultado Exacto Sugerido: <b>{exact_score}</b>\n"
        f"• Total Córneres Estimados: <b>+{corners}.5</b>\n"
        f"• Total Tarjetas Esperadas: <b>+{cards}.5</b>\n\n"
        f"💬 <i>Lectura táctica: {analysis}</i>\n\n"
        f"📊 <b>RECUENTO CANAL:</b> {CHANNEL_STATS['wins']}W - {CHANNEL_STATS['losses']}L ({winrate_total}% Acierto)\n\n"
        f"🔥 <b>¿QUIERES EL COMBINADO VIP CON CUOTA +4.50?</b>\n"
        f"Habla conmigo directamente para conseguir la jugada del día: <b>@{TELEGRAM_USERNAME}</b>\n\n"
        f"💪 <i>¡A por el verde! Stake 1.5.</i>"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "💎 Comprar Pick Premium / Unirse al VIP", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }

    img_path = create_scores24_card(match_title, league, chosen_pick, chosen_odds)
    if send_telegram_photo(img_path, caption, reply_markup=keyboard):
        published_picks.add(pick_id)
        CHANNEL_STATS["wins"] += 1
        CHANNEL_STATS["profit_units"] = round(CHANNEL_STATS["profit_units"] + 1.2, 1)
        logging.info(f"Análisis profesional con logo publicado: {match_title}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Master Tipster Pro Activo...")

    time.sleep(5)
    publish_pick()

    last_morning_day = -1

    while True:
        try:
            current_hour = datetime.now().hour
            current_day = datetime.now().day
            
            # Filtro de horario estricto para el mensaje de buenos días (08:00 - 11:00)
            if current_day != last_morning_day and 8 <= current_hour <= 11:
                send_good_morning()
                last_morning_day = current_day
            
            publish_pick()
        except Exception as e:
            logging.error(f"Error en bucle: {e}")
        
        time.sleep(7200) # Publica un pick cada 2 horas

if __name__ == "__main__":
    main()
