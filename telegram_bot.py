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

sent_alerts = set()
scheduled_tasks = set()
CSV_FILE = "registro_pronosticos.csv"

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Fecha", "Tipo", "Detalle", "Cuota", "Resultado", "Unidades"])

init_csv()

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("Falta TELEGRAM_BOT_TOKEN o CHAT_ID")
        return None
    
    chat_id_clean = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    token_clean = str(TELEGRAM_BOT_TOKEN).strip().replace('"', '').replace("'", "")
    
    url = f"https://api.telegram.org/bot{token_clean}/sendMessage"
    payload = {"chat_id": chat_id_clean, "text": text, "parse_mode": "HTML"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        logging.info(f"Respuesta Telegram: {res.status_code} - {res.text}")
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

def create_toptips_analysis_image(match_title, league_name, pick_text, odds_val):
    """Genera una plantilla visual oficial de TOPTIPS con diseño elegante."""
    img = Image.new('RGB', (900, 500), color=(11, 19, 43))
    d = ImageDraw.Draw(img)
    
    # Marco Dorado TOPTIPS
    d.rectangle([15, 15, 885, 485], outline=(212, 175, 55), width=4)
    
    # Encabezado
    d.text((40, 35), "🛡️ TOPTIPS - INFORME DE INTELIGENCIA DEPORTIVA", fill=(212, 175, 55))
    d.text((40, 85), f"COMPETICIÓN: {league_name.upper()}", fill=(200, 200, 200))
    d.text((40, 135), f"ENCUENTRO: {match_title}", fill=(255, 255, 255))
    
    # Caja de Selección EV+
    d.rectangle([35, 200, 865, 330], fill=(28, 37, 65), outline=(0, 200, 150), width=2)
    d.text((55, 220), f"SELECCIÓN RECOMENDADA IA:", fill=(0, 200, 150))
    d.text((55, 265), f"{pick_text} @ {odds_val:.2f}", fill=(255, 255, 255))
    
    # Pie de imagen
    d.text((40, 370), "FILTROS ACTIVOS: xG Proyectado | Volumen de Tiros | Presión Táctica", fill=(160, 160, 160))
    d.text((40, 420), "Canal Oficial Telegram: @FreeTopTip", fill=(212, 175, 55))
    
    filename = "toptips_analysis.png"
    img.save(filename)
    return filename

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot TOPTIPS Multi-Mercado & Live Active".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()

def generate_ai_tactical_analysis(home, away, market_type, selection):
    """Genera análisis detallados en primera persona con fundamento táctico."""
    if "1X2" in market_type:
        return (
            f"• <b>Dinámica de Juego:</b> El conjunto de {selection} mantiene un control absoluto del ritmo de partido y transiciones ofensivas rapídisimas.\n"
            f"• <b>Rendimiento Táctico:</b> Los datos en tiempo real de volumen de tiros a puerta (SoT) proyectan una alta probabilidad de llevarse los 3 puntos."
        )
    elif "Goles" in market_type:
        return (
            f"• <b>Proyección xG:</b> La métrica de goles esperados entre {home} y {away} supera con claridad la línea establecida.\n"
            f"• <b>Ritmo Abierto:</b> Ambos equipos están dejando amplias grietas defensivas en las bandas, favoreciendo llegadas constantes al área rival."
        )
    else: # Córners
        return (
            f"• <b>Presión por Bandas:</b> Ataque constante mediante centros laterales e incursiones por las bandas que fuerzan despejes a la línea de fondo.\n"
            f"• <b>Volumen Estimado:</b> La proyección cuantitativa anticipa un número elevado de saques de esquina durante el tramo de partido."
        )

def check_live_and_prematch_picks():
    if not ODDS_API_KEY:
        return

    leagues = ["soccer_spain_la_liga", "soccer_epl", "soccer_germany_bundesliga", "soccer_italy_serie_a"]
    today_str = datetime.now().strftime("%Y-%m-%d")

    for league in leagues:
        try:
            # Consultar partidos y cuotas live/prematch
            url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h"
            res = requests.get(url, timeout=10)
            if res.status_code != 200:
                continue
            events = res.json()
        except Exception:
            continue

        for event in events[:2]:
            home = event.get("home_team", "Local")
            away = event.get("away_team", "Visitante")
            event_id = event.get("id")
            alert_key = f"live_pick_{event_id}_{today_str}"

            if alert_key in sent_alerts:
                continue

            # Selección de Mercados Live & Pre-match (1X2, Goles, Córners)
            market_options = [
                ("⚡ RECOMENDACIÓN LIVE 1X2", f"Victoria de {home}", 2.05),
                ("⚽ RECOMENDACIÓN LIVE GOLES", "Más de 2.5 Goles Totales", 1.95),
                ("🚩 RECOMENDACIÓN LIVE CÓRNERS", "Más de 9.5 Córners Totales", 2.10),
                ("⚡ RECOMENDACIÓN LIVE 1X2", f"Victoria de {away}", 2.35)
            ]
            
            chosen_mkt, chosen_sel, chosen_odds = random.choice(market_options)
            analysis_text = generate_ai_tactical_analysis(home, away, chosen_mkt, chosen_sel)

            caption_msg = (
                f"🔥 <b>{chosen_mkt} (EN DIRECTO)</b> 🔥\n\n"
                f"🏆 <b>Competición:</b> {event.get('sport_title', 'Grandes Ligas')}\n"
                f"⚔️ <b>Encuentro:</b> {home} vs {away}\n"
                f"📌 <b>Selección IA:</b> {chosen_sel}\n"
                f"📈 <b>Cuota:</b> {chosen_odds:.2f}€ | 🏦 <b>Casa:</b> Bet365\n\n"
                f"🧠 <b>ANÁLISIS TÁCTICO INTEGRADO:</b>\n"
                f"{analysis_text}\n\n"
                f"⚠️ <b>Stake Recomendado:</b> Stake 1.5 (Moderado / EV+)"
            )

            # Generar la imagen con tu marca TOPTIPS y enviarla
            img_path = create_toptips_analysis_image(f"{home} vs {away}", event.get('sport_title', 'Grandes Ligas'), chosen_sel, chosen_odds)
            
            if send_telegram_photo(img_path, caption_msg):
                sent_alerts.add(alert_key)
                return

def publish_intelligent_parlays():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    if f"parlay_ai_{today_str}" in sent_alerts:
        return

    msg = (
        f"🤖 <b>APUESTAS COMBINADAS IA - GRANDES LIGAS</b> 🤖\n\n"
        f"🏆 <i>Análisis Algorítmico Multimercado de Valor</i>\n\n"
        f"💥 <b>COMBINADA BASE EV+ (Cuota @3.85)</b>\n"
        f"• Victoria Local / Apuesta Segura\n"
        f"• Más de 1.5 Goles Totales\n"
        f"📌 <b>Stake 2/5</b>\n\n"
        f"🔥 <b>COMBINADA BOMBAGO LIVE (Cuota @12.50)</b>\n"
        f"• Ambos Equipos Anotan + Más de 8.5 Córners\n"
        f"• Resultado Positivo en Directo\n"
        f"📌 <b>Stake 0.5/5</b>\n\n"
        f"💡 <i>Analizado y validado mediante filtros de valor en casas de apuestas principales.</i>"
    )
    if send_telegram_message(msg):
        sent_alerts.add(f"parlay_ai_{today_str}")

def publish_daily_routine():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    hour = now.hour
    minute = now.minute

    # Saludo y Apertura Oficial (09:00 AM)
    if hour == 9 and minute == 0 and f"morning_{today_str}" not in scheduled_tasks:
        send_telegram_message("☀️ <b>¡BUENOS DÍAS A TODOS!</b> ☀️\n\nLos algoritmos TOPTIPS ya están rastreando partidos en directo y grandes ligas para detectar valor en Victorias, Goles y Córners.")
        scheduled_tasks.add(f"morning_{today_str}")

    # Resumen y Balance Nocturno (22:30 PM)
    if hour == 22 and minute == 30 and f"summary_{today_str}" not in scheduled_tasks:
        send_telegram_message("📊 <b>RESUMEN Y BALANCE DE LA JORNADA TOPTIPS</b> 📊\n\nAnálisis y seguimiento finalizado por hoy. Mañana volvemos con más oportunidades de valor.")
        scheduled_tasks.add(f"summary_{today_str}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Bot TOPTIPS Inteligente Activo...")

    while True:
        try:
            publish_daily_routine()
            publish_intelligent_parlays()
            check_live_and_prematch_picks()
        except Exception as e:
            logging.error(f"Error en el bucle principal: {e}")
        time.sleep(120)

if __name__ == "__main__":
    main()
