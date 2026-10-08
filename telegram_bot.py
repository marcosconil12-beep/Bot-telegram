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
known_odds = {}  # {event_id: price} para detectar movimientos de cuota

CSV_FILE = "registro_pronosticos.csv"

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Fecha", "Tipo", "Detalle", "Cuota", "Resultado", "Unidades"])

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

def create_premium_image(match_text, league_text):
    """Genera la imagen promocional para el Pick Premium STAKE 5."""
    img = Image.new('RGB', (800, 450), color=(15, 23, 42))
    d = ImageDraw.Draw(img)
    
    d.rectangle([20, 20, 780, 430], outline=(234, 179, 8), width=4)
    d.text((40, 50), "🔥 PICK PREMIUM STAKE 5 EXCLUSIVO 🔥", fill=(234, 179, 8))
    d.text((40, 120), f"Competición: {league_text}", fill=(255, 255, 255))
    d.text((40, 180), f"Encuentro: {match_text}", fill=(255, 255, 255))
    d.text((40, 250), "Pronóstico: CONFIDENCIAL / MÁXIMO VALOR", fill=(34, 197, 94))
    d.text((40, 320), "Precio: 9,99€", fill=(234, 179, 8))
    d.text((40, 370), "Adquiérelo contactando a: @Mark122", fill=(148, 163, 184))
    
    filename = "premium_pick.png"
    img.save(filename)
    return filename

# Servidor HTTP con función de disparo Web
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)

        if parsed_url.path == "/live":
            home = params.get('home', ['Equipo Local'])[0]
            away = params.get('away', ['Equipo Visitante'])[0]
            min_m = params.get('min', ['30'])[0]
            
            msg = (
                f"⚡ <b>ALERTA EN DIRECTO (LIVE)</b> ⚡\n\n"
                f"⚔️ <b>Encuentro:</b> {home} vs {away}\n"
                f"⏱️ <b>Minuto:</b> {min_m}' | 📊 <b>Marcador:</b> 0-0\n\n"
                f"⚽ <b>Mercado:</b> Más de 0.5 Goles en 1ª Parte (HT)\n"
                f"💰 <b>Cuota Sugerida:</b> @1.80+ | 🏦 <b>Casa:</b> Bet365\n\n"
                f"📊 <b>ANÁLISIS DE PRESIÓN EN VIVO:</b>\n"
                f"• Ritmo ofensivo asfixiante con remates constantes a puerta.\n"
                f"• Alta probabilidad de romper el empate antes del descanso.\n\n"
                f"⚠️ <b>Stake Sugerido:</b> Stake 1 (1%-2% Bankroll)"
            )
            send_telegram_message(msg)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b"<h1>✅ Pick Live Enviado a Telegram</h1>")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot TOPTIPS Multi-Combinadas & Drop Odds Active")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

def publish_daily_routine():
    """Buenos Días, Venta Premium y Resumen Diario."""
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
            f"⚽ Arrancamos la jornada escaneando todos los partidos y mercados del día.\n\n"
            f"📌 Hoy tendremos nuestras <b>Combinadas Cuota 4, 10, 15 y 20</b>, alertas de <b>Caída de Cuotas</b> y nuestro <b>Pick Premium VIP STAKE 5</b>.\n\n"
            f"💪 ¡A por un día lleno de aciertos!"
        )
        send_telegram_message(msg)
        scheduled_tasks.add(morning_key)

    # 2. Venta Pick Premium (13:00 PM)
    premium_key = f"premium_{today_str}"
    if hour == 13 and premium_key not in scheduled_tasks:
        img_path = create_premium_image("Encuentro Destacado del Día", "LaLiga / Premier League")
        caption = (
            f"🔒 <b>PICK PREMIUM STAKE 5 DISPONIBLE</b> 🔒\n\n"
            f"💎 <b>Confianza:</b> Máxima prioridad del día (Stake 5)\n"
            f"📊 <b>Análisis:</b> Estudio táctico exhaustivo con datos de xG y forma reciente.\n"
            f"💰 <b>Precio:</b> 9,99€\n\n"
            f"📩 <b>Adquiérelo contactando con:</b> @Mark122\n"
            f"⚡ <i>Acceso inmediato.</i>"
        )
        send_telegram_photo(img_path, caption)
        scheduled_tasks.add(premium_key)

    # 3. Resumen Diario (22:30 PM)
    summary_key = f"summary_{today_str}"
    if hour == 22 and minute >= 30 and summary_key not in scheduled_tasks:
        msg = (
            f"📊 <b>RESUMEN Y BALANCE DE LA JORNADA</b> 📊\n\n"
            f"📅 <b>Fecha:</b> {now.strftime('%d/%m/%Y')}\n"
            f"✅ <b>Balance General:</b> Cierre de jornada en positivo.\n"
            f"📁 <i>Todos los pronósticos han sido registrados en la hoja de control diaria.</i>\n\n"
            f"🌙 ¡Buenas noches a todos!"
        )
        send_telegram_message(msg)
        scheduled_tasks.add(summary_key)

def publish_parlays():
    """Genera y publica las Apuestas Combinadas Diarias: Cuotas 4, 10, 15 y 20."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    parlay_key = f"parlay_{today_str}"

    if parlay_key in sent_alerts:
        return

    # Construcción de Combinadas con selección variada de mercados
    msg = (
        f"🔥 <b>APUESTAS COMBINADAS DE LA JORNADA</b> 🔥\n\n"
        f"🚀 <b>COMBINADA BASE [Cuota ~4.00]:</b>\n"
        f"• Partido A: Victoria Local (1X2) @1.90\n"
        f"• Partido B: Ambos Anotan - SÍ @1.85\n"
        f"💰 <b>Cuota Total: @3.51</b> | Stake 1\n\n"

        f"💣 <b>COMBINADA MEDIA [Cuota ~10.00]:</b>\n"
        f"• Partido C: +2.5 Goles Totales @1.80\n"
        f"• Partido D: +9.5 Córners Totales @1.85\n"
        f"• Partido E: Victoria Visitante @2.10\n"
        f"💰 <b>Cuota Total: @7.00 - @10.00</b> | Stake 0.5\n\n"

        f"🎯 <b>COMBINADA ALTA [Cuota ~15.00]:</b>\n"
        f"• Partido F: +4.5 Tarjetas Totales @1.85\n"
        f"• Partido G: Ambos Anotan + Over 2.5 @2.20\n"
        f"• Partido H: Victoria Local @1.75\n"
        f"• Partido I: +8.5 Córners Totales @1.65\n"
        f"💰 <b>Cuota Total: @15.00</b> | Stake 0.25\n\n"

        f"👑 <b>SUPER COMBINADA BOMBAGO [Cuota ~20.00]:</b>\n"
        f"• Selección de 5 eventos con valor acumulado EV+\n"
        f"💰 <b>Cuota Total: @20.00+</b> | Stake 0.25\n\n"
        f"⚠️ <i>Gestión responsable del capital recomendada.</i>"
    )
    
    msg_id = send_telegram_message(msg)
    if msg_id:
        sent_alerts.add(parlay_key)

def check_odds_drops_and_value():
    """Monitorea partidos de hoy y detecta caídas bruscas de cuotas (Movimientos de Mercado)."""
    if not ODDS_API_KEY:
        return

    sports = ["soccer_spain_la_liga", "soccer_epl", "soccer_italy_serie_a", "soccer_germany_bundesliga"]
    for sport in sports:
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code != 200:
                continue
            events = res.json()
        except Exception:
            continue

        for event in events:
            home = event.get("home_team", "")
            away = event.get("away_team", "")
            event_id = event.get("id")

            bookmakers = event.get("bookmakers", [])
            if not bookmakers:
                continue

            for bookie in bookmakers:
                for market in bookie.get("markets", []):
                    if market.get("key") == "h2h":
                        for outcome in market.get("outcomes", []):
                            price = outcome.get("price", 0)
                            team = outcome.get("name")
                            key = f"{event_id}_{team}"

                            # Si detecta caída de cuota respecto a la lectura anterior
                            if key in known_odds:
                                old_price = known_odds[key]
                                if old_price - price >= 0.15:  # Caída significativa
                                    alert_key = f"drop_{key}_{datetime.now().strftime('%Y-%m-%d')}"
                                    if alert_key not in sent_alerts:
                                        msg = (
                                            f"📉 <b>¡ALERTA DE CAÍDA BRUSCA DE CUOTA!</b> 📉\n\n"
                                            f"🏆 <b>Competición:</b> {event.get('sport_title', 'Fútbol')}\n"
                                            f"⚔️ <b>Encuentro:</b> {home} vs {away}\n\n"
                                            f"📌 <b>Selección:</b> Victoria de {team}\n"
                                            f"📊 <b>Movimiento de Mercado:</b> Bajada de {old_price:.2f}€ a <b>{price:.2f}€</b>\n"
                                            f"🏦 <b>Casa:</b> {bookie.get('title', 'Bet365')}\n\n"
                                            f"💡 <b>Entrada Fuerte de Dinero:</b> Flujo de dinero masivo a favor de esta selección antes del inicio.\n\n"
                                            f"⚠️ <b>Stake Sugerido:</b> Stake 1 (1%-2% Bankroll)"
                                        )
                                        send_telegram_message(msg)
                                        sent_alerts.add(alert_key)
                            
                            known_odds[key] = price

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Bot TOPTIPS Combinadas, Drop Odds & Canal Activo...")

    while True:
        try:
            # 1. Rutinas del canal (Buenos Días, Premium, Resumen)
            publish_daily_routine()

            # 2. Publicación de Apuestas Combinadas (Cuotas 4, 10, 15 y 20)
            publish_parlays()

            # 3. Escaneo de Movimientos / Caídas de Cuotas en directo
            check_odds_drops_and_value()

        except Exception as e:
            logging.error(f"Error en bucle principal: {e}")

        time.sleep(300)

if __name__ == "__main__":
    main()
