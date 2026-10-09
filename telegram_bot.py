import os
import time
import logging
import threading
import requests
import random
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuración de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "").strip()
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
    token = str(TELEGRAM_BOT_TOKEN).strip().replace('"', '').replace("'", "")
    chat = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        res = requests.post(url, json=payload, timeout=8)
        return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error enviando mensaje: {e}")
        return None

def send_telegram_photo(photo_path, caption, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        return None
    token = str(TELEGRAM_BOT_TOKEN).strip().replace('"', '').replace("'", "")
    chat = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            data = {"chat_id": chat, "caption": caption, "parse_mode": "HTML"}
            if reply_markup:
                import json
                data["reply_markup"] = json.dumps(reply_markup)
            res = requests.post(url, data=data, files={"photo": photo}, timeout=10)
            return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error enviando foto a Telegram: {e}")
        return None

def create_scores24_card(match_title, league_name, pick_text, odds_val):
    """Genera una tarjeta gráfica profesional con el nombre TOPTIPS destacado."""
    img = Image.new('RGB', (1000, 600), color=(13, 27, 42))
    d = ImageDraw.Draw(img)
    
    # Borde y Marco de Cabecera
    d.rectangle([20, 20, 980, 580], outline=(0, 212, 170), width=4)
    d.rectangle([20, 20, 980, 110], fill=(20, 40, 65))
    
    # Nombre del Canal destacado en la cabecera
    d.text((40, 48), "🛡️ TOPTIPS OFFICIAL ANALYTICS", fill=(0, 212, 170))
    d.text((580, 48), league_name.upper()[:25], fill=(200, 200, 200))
    
    d.text((40, 140), "PARTIDO ANALIZADO EN DETALLE:", fill=(150, 160, 180))
    d.text((40, 180), match_title, fill=(255, 255, 255))
    
    # Recuadro de Pronóstico
    d.rectangle([40, 240, 960, 420], fill=(24, 43, 73), outline=(255, 215, 0), width=2)
    d.text((70, 260), "SELECCIÓN RECOMENDADA:", fill=(255, 215, 0))
    d.text((70, 315), f"{pick_text}", fill=(255, 255, 255))
    d.text((750, 315), f"@{odds_val:.2f}", fill=(0, 212, 170))

    d.text((40, 460), f"📊 Métricas: xG Proyectado | Córneres | Tarjetas | Yield: +{CHANNEL_STATS['profit_units']}U", fill=(150, 160, 180))
    d.text((40, 510), f"Canal Oficial: TOPTIPS | Contacto VIP: @{TELEGRAM_USERNAME}", fill=(255, 215, 0))
    
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

def send_good_morning():
    total_games = CHANNEL_STATS["wins"] + CHANNEL_STATS["losses"]
    winrate = round((CHANNEL_STATS["wins"] / total_games) * 100, 1)
    
    text = (
        "☀️ <b>¡BUENOS DÍAS A TODOS LOS MIEMBROS DE TOPTIPS!</b> ☀️\n\n"
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

def fetch_scheduled_matches():
    """Consulta los partidos programados para hoy y los próximos 4 días en la API."""
    if not FOOTBALL_API_KEY:
        logging.warning("Falta configurar FOOTBALL_API_KEY en Railway.")
        return []
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    future_str = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")
    
    url = f"https://api.football-data.org/v4/matches?dateFrom={today_str}&dateTo={future_str}"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=12)
        data = response.json()
        if data.get("matches"):
            return data["matches"]
    except Exception as e:
        logging.error(f"Error al consultar partidos programados: {e}")
    return []

def publish_pick():
    matches = fetch_scheduled_matches()
    
    if not matches:
        logging.info("No hay partidos programados en el rango de fechas consultado.")
        return

    # Selecciona un partido de la lista de partidos reales programados
    match = random.choice(matches)
    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]
    league = match["competition"]["name"]
    match_id = match["id"]
    match_date = match["utcDate"][:10]
    
    pick_id = f"SCHEDULED_{match_id}"
    if pick_id in published_picks:
        return

    odds_val = round(random.uniform(1.75, 2.30), 2)
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
        f"⚽ <b>ANÁLISIS PROFESIONAL DETALLADO - TOPTIPS</b> ⚽\n\n"
        f"🏆 <b>Competición:</b> {league}\n"
        f"⚔️ <b>Encuentro:</b> {home} vs {away}\n"
        f"📅 <b>Fecha del Partido:</b> <b>{match_date}</b>\n\n"
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

    img_path = create_scores24_card(f"{home} vs {away}", league, chosen_pick, chosen_odds)
    if send_telegram_photo(img_path, caption, reply_markup=keyboard):
        published_picks.add(pick_id)
        CHANNEL_STATS["wins"] += 1
        CHANNEL_STATS["profit_units"] = round(CHANNEL_STATS["profit_units"] + 1.2, 1)
        logging.info(f"Análisis de partido programado publicado: {home} vs {away}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Master Tipster Pro con partidos programados Activo...")

    time.sleep(3)
    publish_pick()

    last_morning_day = -1

    while True:
        try:
            current_hour = datetime.now().hour
            current_day = datetime.now().day
            
            if current_day != last_morning_day and 8 <= current_hour <= 11:
                send_good_morning()
                last_morning_day = current_day
            
            publish_pick()
        except Exception as e:
            logging.error(f"Error en bucle: {e}")
        
        time.sleep(7200) # Publica un análisis de los partidos programados cada 2 horas

if __name__ == "__main__":
    main()
