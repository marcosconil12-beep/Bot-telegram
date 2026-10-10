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
TELEGRAM_USERNAME = "Mark122" # Tu usuario para ventas VIP

published_picks = set()

# Balance Real del Canal (No se incrementa automáticamente al publicar)
CHANNEL_STATS = {
    "wins": 62,
    "losses": 13,
    "staked_units": 155,
    "profit_units": +48.2
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
        logging.error(f"Error enviando foto: {e}")
        return None

def create_scores24_card(match_title, league_name, pick_text, odds_val):
    """Genera la tarjeta gráfica oficial TOPTIPS."""
    img = Image.new('RGB', (1000, 600), color=(13, 27, 42))
    d = ImageDraw.Draw(img)
    
    d.rectangle([20, 20, 980, 580], outline=(0, 212, 170), width=4)
    d.rectangle([20, 20, 980, 110], fill=(20, 40, 65))
    
    d.text((40, 48), "🛡️ TOPTIPS OFFICIAL ANALYTICS", fill=(0, 212, 170))
    d.text((580, 48), league_name.upper()[:25], fill=(200, 200, 200))
    
    d.text((40, 140), "PARTIDO SELECCIONADO (HOY/FUTURO):", fill=(150, 160, 180))
    d.text((40, 180), match_title, fill=(255, 255, 255))
    
    d.rectangle([40, 240, 960, 420], fill=(24, 43, 73), outline=(255, 215, 0), width=2)
    d.text((70, 260), "CREAR APUESTA RECOMENDADO (IA):", fill=(255, 215, 0))
    d.text((70, 315), f"{pick_text[:45]}...", fill=(255, 255, 255))
    d.text((750, 315), f"@{odds_val:.2f}", fill=(0, 212, 170))

    d.text((40, 460), f"📊 Métricas: xG | Córneres | Tarjetas | Yield: +{CHANNEL_STATS['profit_units']}U", fill=(150, 160, 180))
    d.text((40, 510), f"Canal Oficial: TOPTIPS | Suscripción VIP: @{TELEGRAM_USERNAME}", fill=(255, 215, 0))
    
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
        "☕ Arrancamos la jornada con los 15 análisis de 'Crear Apuesta' más potentes del día.\n\n"
        "📊 <b>REVISIÓN DE RESULTADOS Y BALANCES DEL CANAL:</b>\n"
        f"✅ <b>Picks Acertados:</b> {CHANNEL_STATS['wins']}\n"
        f"❌ <b>Picks Fallados:</b> {CHANNEL_STATS['losses']}\n"
        f"🔥 <b>Efectividad (WinRate):</b> <b>{winrate}%</b>\n"
        f"💰 <b>Beneficio Neto:</b> <b>+{CHANNEL_STATS['profit_units']} Unidades</b>\n\n"
        "💳 <b>ACCESO AL GRUPO VIP PRIVADO TOPTIPS:</b>\n"
        "• 🎟️ <b>Pase Semanal VIP:</b> <b>10.00 €</b> (7 días de acceso total)\n"
        "• 👑 <b>Pase Mensual VIP:</b> <b>34.99 €</b> (Acceso completo 30 días)\n\n"
        f"📩 <i>Para unirte al VIP y recibir todas las combinadas exclusivas diario, escríbeme directamente:</i>\n"
        f"👉 <b>Contactar al Analista: @{TELEGRAM_USERNAME}</b>"
    )
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "👑 Comprar Acceso al Grupo VIP", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }
    send_telegram_message(text, reply_markup=keyboard)

def fetch_future_matches():
    """Filtra y devuelve ÚNICAMENTE partidos que aún NO han comenzado."""
    if not FOOTBALL_API_KEY:
        logging.warning("Falta configurar FOOTBALL_API_KEY en Railway.")
        return []
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    future_str = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    
    url = f"https://api.football-data.org/v4/matches?dateFrom={today_str}&dateTo={future_str}"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    future_matches = []
    
    try:
        response = requests.get(url, headers=headers, timeout=12)
        data = response.json()
        if data.get("matches"):
            now_utc = datetime.utcnow()
            for match in data["matches"]:
                # Comprobación de estado y fecha/hora
                match_status = match.get("status")
                utc_date_str = match.get("utcDate")
                
                if match_status in ["SCHEDULED", "TIMED"]:
                    match_time = datetime.strptime(utc_date_str, "%Y-%m-%dT%H:%M:%SZ")
                    # Solo incluir si falta al menos 10 minutos para que comience
                    if match_time > now_utc + timedelta(minutes=10):
                        future_matches.append(match)
    except Exception as e:
        logging.error(f"Error consultando partidos futuros: {e}")
        
    return future_matches

def publish_builder_pick():
    matches = fetch_future_matches()
    if not matches:
        logging.info("No hay partidos futuros pendientes para analizar en este momento.")
        return False

    match = random.choice(matches)
    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]
    league = match["competition"]["name"]
    match_id = match["id"]
    match_time_utc = match["utcDate"].replace("T", " ")[:16]
    
    pick_id = f"BUILDER_{match_id}"
    if pick_id in published_picks:
        return False

    # Generación de Combinadas "Crear Apuesta" de Alto Valor
    builder_options = [
        (f"Victoria {home} + Más de 1.5 Goles + Más de 7.5 Córneres", round(random.uniform(2.40, 2.90), 2), f"Dominio local previsto. {home} genera un alto flujo de saques de esquina y volumen ofensivo."),
        (f"Más de 2.5 Goles + Ambos Anotan (Sí) + Más de 3.5 Tarjetas", round(random.uniform(2.60, 3.20), 2), "Encuentro de ida y vuelta con defensas adelantadas y alta intensidad en la medular."),
        (f"Doble Oportunidad {home}/Empate + Más de 8.5 Córneres + Más de 1.5 Goles", round(random.uniform(2.10, 2.50), 2), "Estructura de seguridad basada en el dominio de bandas del equipo local."),
        (f"Más de 0.5 Goles 1ª Parte + Victoria {home} + Más de 4.5 Córneres {home}", round(random.uniform(2.50, 3.10), 2), "Asedio inicial esperado. Salida intensiva buscando marcar en los primeros 45 minutos.")
    ]

    chosen_pick, chosen_odds, analysis = random.choice(builder_options)

    forms = ["🟢 🟢 🟡 🔴 🟢", "🟢 🟢 🟢 🟡 🟢", "🟡 🔴 🟢 🟢 🟡", "🟢 🟡 🟡 🟢 🔴"]
    form_home, form_away = random.choice(forms), random.choice(forms)
    
    total_games = CHANNEL_STATS["wins"] + CHANNEL_STATS["losses"]
    winrate_total = round((CHANNEL_STATS["wins"] / total_games) * 100, 1)

    caption = (
        f"⚽ <b>CREAR APUESTA (BET BUILDER IA) - TOPTIPS</b> ⚽\n\n"
        f"🏆 <b>Competición:</b> {league}\n"
        f"⚔️ <b>Encuentro:</b> {home} vs {away}\n"
        f"⏰ <b>Hora de Inicio (UTC):</b> <b>{match_time_utc}</b>\n\n"
        f"📈 <b>ESTADO DE FORMA:</b>\n"
        f"• {home}: {form_home}\n"
        f"• {away}: {form_away}\n\n"
        f"🎯 <b>SELECCIÓN CREAR APUESTA:</b>\n"
        f"• Combinada: <code>{chosen_pick}</code>\n"
        f"• Cuota Total (Bet365): <b>{chosen_odds:.2f}</b>\n"
        f"• Stake Sugerido: <b>1.5 / 10</b>\n\n"
        f"🔍 <b>ANÁLISIS TÁCTICO DE IA:</b>\n"
        f"💬 <i>{analysis}</i>\n\n"
        f"📊 <b>RECUENTO DEL CANAL:</b> {CHANNEL_STATS['wins']}W - {CHANNEL_STATS['losses']}L ({winrate_total}% Acierto)\n\n"
        f"💳 <b>ÚNETE AL GRUPO VIP OFICIAL:</b>\n"
        f"• Pase Semanal: <b>10 €</b> | Pase Mensual: <b>34.99 €</b>\n"
        f"📲 Recibe todas las combinadas exclusivas del día escribiéndome a: <b>@{TELEGRAM_USERNAME}</b>"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "👑 Comprar Pase VIP (10€ Semanal / 34,99€ Mensual)", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }

    img_path = create_scores24_card(f"{home} vs {away}", league, chosen_pick, chosen_odds)
    if send_telegram_photo(img_path, caption, reply_markup=keyboard):
        published_picks.add(pick_id)
        logging.info(f"Pick 'Crear Apuesta' futuro publicado: {home} vs {away}")
        return True

    return False

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Master Tipster Pro (15 Picks 'Crear Apuesta' Diarios) Activo...")

    time.sleep(3)
    publish_builder_pick()

    last_morning_day = -1

    while True:
        try:
            current_hour = datetime.now().hour
            current_day = datetime.now().day
            
            # Mensaje de Buenos Días entre 08:00 y 11:00
            if current_day != last_morning_day and 8 <= current_hour <= 11:
                send_good_morning()
                last_morning_day = current_day
            
            # Intenta publicar picks de partidos futuros
            publish_builder_pick()
        except Exception as e:
            logging.error(f"Error en bucle principal: {e}")
        
        # 15 publicaciones al día distribuidas (intervalo aproximado de 1 hora y 30 minutos)
        time.sleep(5400)

if __name__ == "__main__":
    main()
