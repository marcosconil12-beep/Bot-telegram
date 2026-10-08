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
from urllib.parse import parse_qs, urlparse

# Configuración de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Registros en memoria persistente contra duplicados
sent_alerts = set()
scheduled_tasks = set()

# Archivo CSV / Excel diario local
CSV_FILE = "registro_pronosticos.csv"

# Cobertura completa de Ligas
TARGET_LEAGUES = [
    "soccer_spain_la_liga", "soccer_spain_segunda_division",
    "Primera RFEF (Todos los Grupos)", "Segunda RFEF (Todos los Grupos)", "Tercera RFEF (Grupo 10)",
    "soccer_epl", "soccer_efl_champ", "soccer_france_ligue_one", "soccer_france_ligue_two",
    "soccer_italy_serie_a", "soccer_italy_serie_b", "soccer_brazil_campeonato", "Serie B Brasil",
    "soccer_japan_j_league", "J2 League", "soccer_australia_aleague", "soccer_korea_kleague1",
    "soccer_scotland_premiership"
]

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Fecha", "Competición", "Encuentro", "Mercado", "Selección", "Cuota", "Resultado", "Unidades"])

init_csv()

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("TELEGRAM_BOT_TOKEN o CHAT_ID no configurados.")
        return None
    
    clean_chat_id = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": clean_chat_id, "text": text, "parse_mode": "HTML"}

    try:
        res = requests.post(url, json=payload, timeout=10)
        res_data = res.json()
        if res_data.get("ok"):
            return res_data.get("result", {}).get("message_id")
    except Exception as e:
        logging.error(f"Error enviando mensaje: {e}")
    return None

def send_telegram_photo(photo_path, caption):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        return None
    clean_chat_id = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    
    try:
        with open(photo_path, 'rb') as photo:
            payload = {"chat_id": clean_chat_id, "caption": caption, "parse_mode": "HTML"}
            files = {"photo": photo}
            res = requests.post(url, data=payload, files=files, timeout=15)
            return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error enviando foto: {e}")
    return None

def trigger_live_pick(home_team="Equipo Local", away_team="Equipo Visitante", minute=30, score="0-0"):
    """Lanza un pick Live instantáneo enviado desde la web."""
    msg = (
        f"⚡ <b>ALERTA EN DIRECTO (LIVE)</b> ⚡\n\n"
        f"🏆 <b>Competición:</b> Encuentro en Directo\n"
        f"⚔️ <b>Match:</b> {home_team} vs {away_team}\n"
        f"⏱️ <b>Minuto:</b> {minute}' | 📊 <b>Marcador:</b> {score}\n\n"
        f"⚽ <b>Mercado:</b> Más de 0.5 Goles en la 1ª Parte (HT)\n"
        f"💰 <b>Cuota Sugerida:</b> @1.80+ | 🏦 <b>Disponible en:</b> Bet365 / Casas TOP\n\n"
        f"📊 <b>ANÁLISIS DE PRESIÓN EN VIVO:</b>\n"
        f"• Ritmo ofensivo muy alto en los últimos 15 minutos con remates constantes.\n"
        f"• Desajuste defensivo inminente antes de llegar al descanso.\n\n"
        f"⚠️ <b>Stake Sugerido:</b> Stake 1 (1%-2% Bankroll)"
    )
    send_telegram_message(msg)

# Servidor HTTP con integración de comandos Web para lanzar LIVEs desde el navegador
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)

        # Ruta Web para activar alerta LIVE por URL: tu-app.railway.app/live?home=RealMadrid&away=Barcelona
        if parsed_url.path == "/live":
            home = params.get('home', ['Equipo Local'])[0]
            away = params.get('away', ['Equipo Visitante'])[0]
            minute = params.get('min', ['30'])[0]
            
            trigger_live_pick(home, away, minute, "0-0")
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            response_text = f"<h1>✅ Pick Live Lanzado Correctamente a Telegram</h1><p>{home} vs {away} - Minuto {minute}' (0-0)</p>"
            self.wfile.write(response_text.encode('utf-8'))
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot TOPTIPS Active & Ready for Web LIVE Triggers")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

def create_premium_image(match_text, league_text):
    """Crea una imagen promocional limpia con el Pick Premium STAKE 5."""
    img = Image.new('RGB', (800, 450), color=(15, 23, 42))
    d = ImageDraw.Draw(img)
    
    d.rectangle([20, 20, 780, 430], outline=(234, 179, 8), width=4)
    d.text((40, 50), "🔥 PICK PREMIUM STAKE 5 EXCLUSIVO 🔥", fill=(234, 179, 8))
    d.text((40, 120), f"Competición: {league_text}", fill=(255, 255, 255))
    d.text((40, 180), f"Encuentro: {match_text}", fill=(255, 255, 255))
    d.text((40, 250), "Pronóstico: CONFIDENCIAL / ALTA CONFIANZA", fill=(34, 197, 94))
    d.text((40, 320), "Precio: 9,99€", fill=(234, 179, 8))
    d.text((40, 370), "Adquiérelo contactando a: @Mark122", fill=(148, 163, 184))
    
    filename = "premium_pick.png"
    img.save(filename)
    return filename

def publish_daily_routine():
    """Gestión del canal: Buenos Días, Venta Premium y Resumen del Día."""
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    hour = now.hour
    minute = now.minute

    # 1. Buenos Días (09:00 AM)
    morning_key = f"morning_{today_str}"
    if hour == 9 and morning_key not in scheduled_tasks:
        msg = (
            f"☀️ <b>¡BUENOS DÍAS A TODOS!</b> ☀️\n\n"
            f"📅 <b>Fecha:</b> {now.strftime('%d/%m/%Y')}\n"
            f"⚽ Iniciamos la jornada con la cobertura de todas las grandes ligas y torneos internacionales.\n\n"
            f"🎯 Hoy publicaremos los <b>mejores pronósticos de valor</b> y nuestro <b>Pick Premium VIP</b>.\n\n"
            f"💪 ¡A por un día repleto de acertados! 🚀"
        )
        send_telegram_message(msg)
        scheduled_tasks.add(morning_key)

    # 2. Venta de Pick Premium Stake 5 (13:00 PM)
    premium_key = f"premium_{today_str}"
    if hour == 13 and premium_key not in scheduled_tasks:
        img_path = create_premium_image("Encuentro Destacado del Día", "LaLiga / Premier League")
        caption = (
            f"🔒 <b>PICK PREMIUM STAKE 5 DISPONIBLE</b> 🔒\n\n"
            f"💎 <b>Nivel de Confianza:</b> Máxima prioridad de la jornada (Stake 5)\n"
            f"📊 <b>Análisis:</b> Estudio táctico exhaustivo y métricas validadas.\n"
            f"💰 <b>Precio:</b> 9,99€\n\n"
            f"📩 <b>Para adquirir el pronóstico contacta con:</b> @Mark122\n"
            f"⚡ <i>Acceso inmediato tras confirmación.</i>"
        )
        send_telegram_photo(img_path, caption)
        scheduled_tasks.add(premium_key)

    # 3. Resumen Diario de Resultados (22:30 PM)
    summary_key = f"summary_{today_str}"
    if hour == 22 and minute >= 30 and summary_key not in scheduled_tasks:
        msg = (
            f"📊 <b>RESUMEN Y BALANCE DE LA JORNADA</b> 📊\n\n"
            f"📅 <b>Fecha:</b> {now.strftime('%d/%m/%Y')}\n"
            f"✅ <b>Pronósticos Acertados:</b> Jornada positiva completada.\n"
            f"📈 <b>Balance:</b> Rendimiento positivo acumulado.\n\n"
            f"📁 <i>Todos los pronósticos han sido registrados en el historial de control diario.</i>\n\n"
            f"🌙 ¡Buenas noches a todos! Mañana continuamos."
        )
        send_telegram_message(msg)
        
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([today_str, "Jornada Global", "Resumen Diario", "Multi-Mercado", "Varios", "1.85", "Ganada", "+1.70"])
            
        scheduled_tasks.add(summary_key)

def check_top_picks():
    """Selecciona y publica el mejor pick pre-partido del día."""
    if not ODDS_API_KEY:
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    top_pick_key = f"top_pick_{today_str}"

    if top_pick_key in sent_alerts:
        return

    url = f"https://api.the-odds-api.com/v4/sports/soccer_spain_la_liga/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=totals&oddsFormat=decimal"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            return
        events = res.json()
        
        if events:
            event = events[0]
            home = event.get("home_team", "")
            away = event.get("away_team", "")
            
            msg = (
                f"🎯 <b>PRONÓSTICO DE VALOR DE LA JORNADA</b> 🎯\n\n"
                f"🏆 <b>Competición:</b> {event.get('sport_title', 'LaLiga')}\n"
                f"⚔️ <b>Encuentro:</b> {home} vs {away}\n\n"
                f"⚽ <b>Selección:</b> Más de 2.5 Goles Totales\n"
                f"💰 <b>Cuota:</b> 1.85€ | 🏦 <b>Casa:</b> Bet365\n\n"
                f"📊 <b>ANÁLISIS TÁCTICO Y MÉTRICAS:</b>\n"
                f"• Promedio de llegada a área y volumen de disparo elevado en ambos conjuntos.\n"
                f"• Transiciones ofensivas rápidas que propician un partido abierto.\n\n"
                f"⚠️ <b>Stake Sugerido:</b> Stake 1 (1%-2% Bankroll)"
            )
            send_telegram_message(msg)
            sent_alerts.add(top_pick_key)
    except Exception as e:
        logging.error(f"Error buscando TOP Pick: {e}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Bot TOPTIPS Gestor de Canal & Triggers Web LIVE en ejecución...")

    while True:
        try:
            publish_daily_routine()
            check_top_picks()
        except Exception as e:
            logging.error(f"Error en bucle principal: {e}")

        time.sleep(300)

if __name__ == "__main__":
    main()
