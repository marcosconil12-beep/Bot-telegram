import os
import time
import logging
import threading
import requests
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuración de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Función para limpiar variables de entorno de corchetes, comillas o espacios accidentales
def clean_env(var_name, default_val=""):
    val = os.environ.get(var_name, default_val)
    if not val:
        return default_val
    val_str = str(val).strip()
    for bad_char in ['[', ']', '(', ')', "'", '"', ' ']:
        val_str = val_str.replace(bad_char, '')
    return val_str.strip()

# Variables de entorno limpias
TELEGRAM_BOT_TOKEN = clean_env("TELEGRAM_BOT_TOKEN", "8657360203:AAG0wJnyLFfEaBMY8XadJs1dZdSQU42ah7c")
CHAT_ID = clean_env("TELEGRAM_CHAT_ID", "@FreeTopTip")
GEMINI_API_KEY = clean_env("GEMINI_API_KEY", "AQ.Ab8RN6IzHOYBnb0nCJ_95k78xwox8--fOsWPf94ytRYPuGtk4g")
TELEGRAM_USERNAME = "Mark122" # Tu usuario para ventas VIP

SPAIN_TZ = ZoneInfo("Europe/Madrid")

# Balance del Canal
CHANNEL_STATS = {
    "wins": 65,
    "losses": 14,
    "profit_units": +51.8,
    "yield_pct": 24.5
}

def send_telegram_message(text, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("Falta TELEGRAM_BOT_TOKEN o CHAT_ID en las variables.")
        return None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
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
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}
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

def generate_gemini_expert_analysis(match_name, league, pick, odds):
    """Genera un análisis técnico único, ultra-detallado y con datos específicos por partido."""
    prompt = f"""
    Actúa como un tipster analista de fútbol profesional para el canal de Telegram @FreeTopTip.
    Escribe un análisis táctico EN PRIMERA PERSONA ("He analizado", "Viendo el comportamiento...", "Me decido por...") extremadamente detallado y específico para este partido:
    
    - Encuentro: {match_name}
    - Competición: {league}
    - Selección / Apuesta: {pick}
    - Cuota Bet365: {odds}
    
    Estructura obligatoria del texto (desarrolla cada punto con datos tácticos reales, estilo de juego, volumen de remates, presión tras pérdida o xG esperados específicos de estos dos equipos):
    1. **Contexto ambiental y estadio:** Explica cómo afecta el factor cancha, el empuje de la afición local y la propuesta con la que saltan al campo.
    2. **Estructura táctica del rival:** Analiza los espacios que conceden en defensa, las transiciones ofensivas y por qué este pronóstico encaja con el planteamiento.
    3. **Relación Riesgo/Beneficio:** Justifica por qué entrar a esta cuota {odds} tiene un valor matemático y estadístico superior en Bet365.
    
    No repitas frases genéricas. Adapta cada argumento exclusivamente a {match_name}. No incluyas saludos ni despedidas.
    """
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, headers=headers, json=payload, timeout=25)
        data = res.json()
        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            return f"Contexto ambiental: El ambiente en el feudo local propone un inicio asfixiante con posesiones largas.\n\nEstructura táctica: Las debilidades en la línea defensiva del rival facilitarán múltiples llegadas por bandas.\n\nRelación Riesgo/Beneficio: La cuota {odds} ofrece un valor excelente."
    except Exception as e:
        logging.error(f"Error en API Gemini para {match_name}: {e}")
        return f"Contexto ambiental: Analizando el partido {match_name}, la necesidad de puntuar en {league} acelera el ritmo ofensivo.\n\nEstructura táctica: Las transiciones rápidas favorecen esta selección.\n\nRelación Riesgo/Beneficio: Magnífico valor en cuota {odds}."

def publish_pick(match_title, league_name, pick_text, odds_val):
    analysis_text = generate_gemini_expert_analysis(match_title, league_name, pick_text, odds_val)
    
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
        f"💳 <b>¿QUIERES ACCEDER A TODAS LAS COMBINADAS VIP DE HOY?</b>\n"
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
            "☕ Arrancamos una jornada cargada de análisis en los mejores partidos del día.\n\n"
            "💳 <b>TARIFAS GRUPO VIP PRIVADO:</b>\n"
            "🔥 <b>Pase Día Premium:</b> <b>5.00 €</b>\n"
            "🎟️ <b>Pase Semanal VIP:</b> <b>10.00 €</b>\n"
            "👑 <b>Pase Mensual VIP:</b> <b>34.99 €</b>\n\n"
            f"📲 <i>Escríbeme por privado para entrar al Grupo VIP:</i>\n"
            f"👉 <b>Contactar al Analista: @{TELEGRAM_USERNAME}</b>"
        )
    else: # Lunes a Jueves
        msg = (
            "☀️ <b>¡BUENOS DÍAS A TODOS! JORNADA DE VALOR DE HOY</b> ☀️\n\n"
            "☕ Ya tenemos filtrados los encuentros del día con mayor valor táctico.\n\n"
            "💳 <b>ACCESO ACCUMULATOR / VIP TOPTIPS:</b>\n"
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

def send_evening_recap():
    msg = (
        "📈 <b>CIERRE DE JORNADA Y BALANCE DE RESULTADOS</b> 📈\n\n"
        "Finalizamos otro día aplicando nuestro método de análisis estadístico en @FreeTopTip.\n\n"
        f"📊 <b>ESTADÍSTICAS GENERALES DEL CANAL:</b>\n"
        f"🟢 <b>Verdes / Aciertos:</b> {CHANNEL_STATS['wins']}\n"
        f"🔴 <b>Fallos:</b> {CHANNEL_STATS['losses']}\n"
        f"💰 <b>Beneficio Neto:</b> +{CHANNEL_STATS['profit_units']} Unidades (+{CHANNEL_STATS.get('yield_pct', 24.5)}% Yield)\n\n"
        f"👑 <b>¿Quieres asegurar tus ganancias diarias? Pasa al VIP: @{TELEGRAM_USERNAME}</b>"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": "💳 Unirme al VIP para Mañana", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }
    send_telegram_message(msg, reply_markup=keyboard)

TODAY_MATCHES = [
    ("Galatasaray vs FC Barcelona", "UEFA Champions League", "Crear Apuesta: Victoria FC Barcelona + Más de 8.5 Córneres + Ambos Anotan", 2.35),
    ("Arsenal vs Lille", "UEFA Champions League", "Crear Apuesta: Victoria Arsenal + Más de 1.5 Goles + Más de 4.5 Córneres Arsenal", 2.10),
    ("AZ Alkmaar vs FC Utrecht", "Eredivisie (Países Bajos)", "Más de 2.5 Goles Totales + Ambos Anotan (Sí)", 2.05),
    ("Sporting CP vs SC Braga", "Primeira Liga (Portugal)", "Crear Apuesta: Victoria Sporting CP + Más de 1.5 Goles + Más de 7.5 Córneres", 2.15),
    ("Boca Juniors vs River Plate", "Liga Profesional Argentina", "Más de 5.5 Tarjetas Totales + Doble Oportunidad Boca/Empate", 2.20)
]

def run_daily_routine():
    send_daily_sales_message()
    time.sleep(3)
    
    for match, league, pick, odds in TODAY_MATCHES:
        publish_pick(match, league, pick, odds)
        time.sleep(8)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Tipster Gemini Dinámico Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error servidor HTTP: {e}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Tipster Inteligente Gemini Dinámico en ejecución...")

    # Ejecución inmediata nada más arrancar
    run_daily_routine()

    now_spain = datetime.now(SPAIN_TZ)
    last_executed_day = now_spain.day
    recap_sent_today = False

    while True:
        try:
            now_spain = datetime.now(SPAIN_TZ)
            current_day = now_spain.day
            current_hour = now_spain.hour

            # Rutina diaria a las 08:00 AM
            if current_day != last_executed_day and current_hour == 8:
                run_daily_routine()
                last_executed_day = current_day
                recap_sent_today = False

            # Cierre diario a las 22:30 PM
            if current_hour == 22 and not recap_sent_today:
                send_evening_recap()
                recap_sent_today = True

        except Exception as e:
            logging.error(f"Error en bucle principal: {e}")

        time.sleep(30)

if __name__ == "__main__":
    main()
