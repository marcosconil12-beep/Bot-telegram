import os
import time
import logging
import threading
import requests
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuración de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
# Clave de API de Gemini integrada
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6IzHOYBnb0nCJ_95k78xwox8--fOsWPf94ytRYPuGtk4g").strip()
TELEGRAM_USERNAME = "Mark122" # Tu usuario para ventas VIP

SPAIN_TZ = ZoneInfo("Europe/Madrid")

# Balance del Canal
CHANNEL_STATS = {
    "wins": 65,
    "losses": 14,
    "profit_units": +51.8
}

def send_telegram_message(text, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("Falta TELEGRAM_BOT_TOKEN o CHAT_ID en las variables.")
        return None
    token = str(TELEGRAM_BOT_TOKEN).strip().replace('"', '').replace("'", "")
    chat = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    import json
    payload = {"chat_id": chat, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        res = requests.post(url, json=payload, timeout=12)
        return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error enviando mensaje a Telegram: {e}")
        return None

def send_telegram_photo(photo_path, caption, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        return None
    token = str(TELEGRAM_BOT_TOKEN).strip().replace('"', '').replace("'", "")
    chat = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        import json
        with open(photo_path, 'rb') as photo:
            data = {"chat_id": chat, "caption": caption, "parse_mode": "HTML"}
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)
            res = requests.post(url, data=data, files={"photo": photo}, timeout=15)
            return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error enviando foto a Telegram: {e}")
        return None

def create_scores24_card(match_title, league_name, pick_text, odds_val):
    try:
        img = Image.new('RGB', (1000, 600), color=(13, 27, 42))
        d = ImageDraw.Draw(img)
        
        d.rectangle([20, 20, 980, 580], outline=(0, 212, 170), width=4)
        d.rectangle([20, 20, 980, 110], fill=(20, 40, 65))
        
        d.text((40, 48), "🛡️ TOPTIPS OFFICIAL ANALYTICS", fill=(0, 212, 170))
        d.text((580, 48), league_name.upper()[:25], fill=(200, 200, 200))
        
        d.text((40, 140), "PARTIDO ANALIZADO EN DETALLE:", fill=(150, 160, 180))
        d.text((40, 180), match_title, fill=(255, 255, 255))
        
        d.rectangle([40, 240, 960, 420], fill=(24, 43, 73), outline=(255, 215, 0), width=2)
        d.text((70, 260), "SELECCIÓN RECOMENDADA (BET365):", fill=(255, 215, 0))
        d.text((70, 315), f"{pick_text[:45]}...", fill=(255, 255, 255))
        d.text((750, 315), f"@{odds_val:.2f}", fill=(0, 212, 170))

        d.text((40, 460), f"📊 Métricas: Rendimiento Táctico | Yield: +{CHANNEL_STATS['profit_units']}U", fill=(150, 160, 180))
        d.text((40, 510), f"Canal Oficial: @FreeTopTip | Suscripción VIP: @{TELEGRAM_USERNAME}", fill=(255, 215, 0))
        
        filename = "scores24_card.png"
        img.save(filename)
        return filename
    except Exception as e:
        logging.error(f"Error generando imagen: {e}")
        return None

def generate_gemini_analysis(match_name, league, pick, odds):
    """Genera un análisis experto utilizando la IA de Gemini."""
    if not GEMINI_API_KEY:
        return f"Analizando los patrones tácticos de {league}, la dinámica de ambos planteles refleja una clara superioridad en generación de ocasiones. {match_name} presenta las condiciones óptimas para buscar esta selección a cuota {odds:.2f} en Bet365."
    
    prompt = f"""
    Actúa como un tipster analista de fútbol profesional para el canal de Telegram @FreeTopTip.
    Redacta un análisis en primera persona (hablando yo como experto) muy detallado y técnico.
    
    Partido: {match_name}
    Competición: {league}
    Pronóstico / Selección: {pick}
    Cuota Bet365: {odds}
    
    Requisitos:
    - Habla en primera persona ("He analizado", "Viendo el volumen de disparos...", "Me inclino por...").
    - Explica razones tácticas reales: intensidad en campo contrario, saques de esquina, faltas, transición ofensiva o volumen de xG.
    - Longitud: 3 a 5 frases potentes y profesionales.
    - No agregues saludos ni despedidas, únicamente el texto del análisis.
    """
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        res = requests.post(url, headers=headers, json=payload, timeout=12)
        data = res.json()
        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            logging.error(f"Respuesta inesperada de Gemini API: {data}")
            return f"Tras revisar las estadísticas avanzadas y el volumen ofensivo en {league}, detectamos un valor claro en esta opción para {match_name} a cuota {odds:.2f}."
    except Exception as e:
        logging.error(f"Error llamando a la API de Gemini: {e}")
        return f"Tras revisar las estadísticas avanzadas y el volumen ofensivo en {league}, detectamos un valor claro en esta opción para {match_name} a cuota {odds:.2f}."

def publish_pick(match_title, league_name, pick_text, odds_val):
    analysis_text = generate_gemini_analysis(match_title, league_name, pick_text, odds_val)
    
    caption = (
        f"⚽ <b>ANÁLISIS DE VALOR Y PRONÓSTICO - @FreeTopTip</b> ⚽\n\n"
        f"🏆 <b>Competición:</b> {league_name}\n"
        f"⚔️ <b>Encuentro:</b> {match_title}\n\n"
        f"🎯 <b>SELECCIÓN RECOMENDADA (BET365):</b>\n"
        f"• Pronóstico: <code>{pick_text}</code>\n"
        f"• Cuota Real: <b>{odds_val:.2f}</b>\n"
        f"• Stake Sugerido: <b>1.5 / 10</b>\n\n"
        f"🔎 <b>MI ANÁLISIS DETALLADO DEL PARTIDO:</b>\n"
        f"💬 {analysis_text}\n\n"
        f"📊 <b>BALANCE DEL CANAL:</b> +{CHANNEL_STATS['profit_units']} Unidades de Beneficio\n\n"
        f"💳 <b>¿QUIERES ACCEDER A TODAS LAS COMBINADAS VIP?</b>\n"
        f"📲 Escríbeme directamente por privado: <b>@{TELEGRAM_USERNAME}</b>"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "👑 Comprar Pase VIP / Contactar al Analista", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }

    img_path = create_scores24_card(match_title, league_name, pick_text, odds_val)
    sent = False
    if img_path:
        sent = send_telegram_photo(img_path, caption, reply_markup=keyboard)
    if not sent:
        send_telegram_message(caption, reply_markup=keyboard)

def send_daily_sales_message():
    now_spain = datetime.now(SPAIN_TZ)
    weekday = now_spain.weekday()
    
    if weekday in [4, 5, 6]: # Viernes, Sábado, Domingo
        msg = (
            "☀️ <b>¡BUENOS DÍAS A TODOS EN @FreeTopTip!</b> ☀️\n\n"
            "☕ Arrancamos una jornada cargada de análisis en ligas europeas, sudamericanas e internacionales.\n\n"
            "💳 <b>TARIFAS GRUPO VIP PRIVADO:</b>\n"
            "🔥 <b>Pase Día Premium:</b> <b>5.00 €</b>\n"
            "🎟️ <b>Pase Semanal VIP:</b> <b>10.00 €</b>\n"
            "👑 <b>Pase Mensual VIP:</b> <b>34.99 €</b>\n\n"
            f"📲 <i>Escríbeme por privado para entrar al Grupo VIP:</i>\n"
            f"👉 <b>Contactar al Analista: @{TELEGRAM_USERNAME}</b>"
        )
    else: # Lunes a Jueves
        msg = (
            "☀️ <b>¡BUENOS DÍAS A TODOS! JORNADA DE VALOR GLOBAL</b> ☀️\n\n"
            "☕ Tenemos preparadas las mejores selecciones tras filtrar mercados de Champions, ligas sudamericanas y competiciones asiáticas.\n\n"
            "💳 <b>ACCESO AL GRUPO VIP TOPTIPS:</b>\n"
            "🎟️ <b>Pase Semanal VIP:</b> <b>10.00 €</b>\n"
            "👑 <b>Pase Mensual VIP:</b> <b>34.99 €</b>\n\n"
            f"📲 <i>Para unirte al VIP y recibir la combinada exclusiva de hoy, escríbeme:</i>\n"
            f"👉 <b>Escribir al Analista: @{TELEGRAM_USERNAME}</b>"
        )
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "👑 Entrar al Grupo VIP", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }
    send_telegram_message(msg, reply_markup=keyboard)

ALL_GLOBAL_PICKS = [
    # Champions / Europa League (BetBuilder)
    ("Galatasaray vs FC Barcelona", "UEFA Champions League", "Crear Apuesta: Victoria FC Barcelona + Más de 8.5 Córneres + Ambos Anotan", 2.35),
    ("Arsenal vs Lille", "UEFA Champions League", "Crear Apuesta: Victoria Arsenal + Más de 1.5 Goles + Más de 4.5 Córneres Arsenal", 2.10),
    ("Athletic Club vs AS Roma", "UEFA Europa League", "Crear Apuesta: Doble Oportunidad Athletic/Empate + Más de 8.5 Córneres + Más de 4.5 Tarjetas", 2.25),
    
    # Ligas Menores Europeas
    ("AZ Alkmaar vs FC Utrecht", "Eredivisie (Países Bajos)", "Más de 2.5 Goles Totales + Ambos Anotan (Sí)", 2.05),
    ("Sporting CP vs SC Braga", "Primeira Liga (Portugal)", "Crear Apuesta: Victoria Sporting CP + Más de 1.5 Goles + Más de 7.5 Córneres", 2.15),
    ("Bodø/Glimt vs Molde FK", "Eliteserien (Noruega)", "Ambos Anotan (Sí) + Más de 8.5 Córneres", 2.00),
    
    # Sudamérica
    ("Boca Juniors vs River Plate", "Liga Profesional Argentina", "Más de 5.5 Tarjetas Totales + Doble Oportunidad Boca/Empate", 2.20),
    ("Flamengo vs Palmeiras", "Brasileirão Serie A", "Ambos Anotan (Sí) + Más de 1.5 Goles Totales", 2.05),
    ("Millonarios vs Atlético Nacional", "Liga BetPlay (Colombia)", "Más de 4.5 Tarjetas + Más de 7.5 Córneres", 2.10),
    
    # Asia y Australia
    ("Al Hilal vs Al Nassr", "Saudi Pro League", "Crear Apuesta: Más de 2.5 Goles + Ambos Anotan + Más de 8.5 Córneres", 2.25),
    ("Kawasaki Frontale vs Yokohama Marinos", "J1 League (Japón)", "Más de 2.5 Goles Totales", 2.00),
    ("Sydney FC vs Melbourne Victory", "A-League (Australia)", "Crear Apuesta: Ambos Anotan + Más de 9.5 Córneres Totales", 2.15)
]

def run_daily_routine():
    send_daily_sales_message()
    time.sleep(3)
    
    selected_picks = random.sample(ALL_GLOBAL_PICKS, min(5, len(ALL_GLOBAL_PICKS)))
    
    for match, league, pick, odds in selected_picks:
        publish_pick(match, league, pick, odds)
        time.sleep(4)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Tipster Inteligente Gemini Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error servidor HTTP: {e}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Tipster Inteligente Gemini en ejecución...")

    # Ejecutar al arrancar para publicar de inmediato
    run_daily_routine()

    last_executed_day = -1

    while True:
        try:
            now_spain = datetime.now(SPAIN_TZ)
            current_day = now_spain.day
            current_hour = now_spain.hour

            if current_day != last_executed_day and current_hour == 8:
                run_daily_routine()
                last_executed_day = current_day

        except Exception as e:
            logging.error(f"Error en bucle principal: {e}")

        time.sleep(30)

if __name__ == "__main__":
    main()
