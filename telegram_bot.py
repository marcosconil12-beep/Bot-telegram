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

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
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

def generate_gemini_expert_analysis(match_name, league, pick, odds):
    """Genera un análisis experto usando llamadas HTTP directas a la API de Gemini."""
    prompt = f"""
    Eres un analista táctico de fútbol profesional y tipster para el canal @FreeTopTip.
    Escribe un análisis MUY DETALLADO, EXTENSO Y ESPECÍFICO EN PRIMERA PERSONA ("He analizado", "Observando el planteamiento...", "Apuesto por...") para el partido: {match_name}.

    Datos del pronóstico:
    - Competición: {league}
    - Selección: {pick}
    - Cuota en Bet365: {odds}

    ESTRUCTURA OBLIGATORIA DEL ANÁLISIS:
    
    Contexto ambiental en el estadio: Describe el estadio concreto de este partido, la presión de la afición local y cómo saldrá a morder el equipo desde el minuto 1.

    Estructura táctica del rival: Explica la alineación o propuesta táctica de ambos clubes, los espacios que conceden en defensa, transiciones rápidas y volumen de faltas/córneres/disparos.

    Relación Riesgo/Beneficio: Justifica estadísticamente por qué buscar esta selección concreta a cuota {odds} en Bet365 es de las mejores entradas de la jornada.

    REGLAS ESTRICTAS:
    - Usa nombres reales de jugadores, entrenadores o aspectos específicos de {match_name}.
    - No uses plantillas genéricas ni repitas frases hechas.
    - No incluyas saludos ni despedidas.
    """

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        data = res.json()
        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        logging.error(f"Error en llamada API Gemini HTTP para {match_name}: {e}")

    # Respuestas únicas de alta calidad en caso de contingencia por partido
    if "Galatasaray" in match_name:
        return (
            "Contexto ambiental en Estambul: El Galatasaray en el RAMS Park sale siempre a morder desde el primer minuto impulsado por su enfervorecida afición. Es un estadio que empuja al equipo local a asumir riesgos masivos y probar disparos lejanos, obligando al rival a replegarse en bloque bajo.\n\n"
            "Estructura táctica del rival: Aunque el FC Barcelona parte como favorito y controlará gran parte de la posesión, su propuesta adelantada concede transiciones rápidas. El Galatasaray cuenta con extremos verticales que fuerzan continuos saques de esquina y duelos individuales en bandas.\n\n"
            "Relación Riesgo/Beneficio: Combinar la victoria azulgrana con más córneres y goles a cuota 2.35 en Bet365 ofrece una relación estadística excelente frente al riesgo asumido."
        )
    elif "Arsenal" in match_name:
        return (
            "Contexto ambiental en Londres: El Emirates Stadium se convierte en una auténtica caldera en las grandes noches de Champions League. La presión asfixiante tras pérdida ahoga la salida de balón del visitante desde la medular.\n\n"
            "Estructura táctica del rival: El Lille suele plantear un bloque defensivo compacto pero sufre de manera crónica en la defensa de los centros laterales y jugadas a balón parado perfiladas por los carrileros gunners.\n\n"
            "Relación Riesgo/Beneficio: Exigir la victoria del Arsenal con más de 1.5 goles y volumen de saques de esquina a cuota 2.10 representa un valor de mercado sumamente rentable."
        )
    elif "AZ Alkmaar" in match_name:
        return (
            "Contexto ambiental en Alkmaar: El AFAS Stadion acoge un choque de ida y vuelta donde el dinamismo de la Eredivisie premia los planteamientos valientes y el intercambio constante de golpes.\n\n"
            "Estructura táctica del rival: Tanto el AZ como el FC Utrecht promedian registros ofensivos muy elevados, dejando espacios evidentes a la espalda de sus laterales que facilitan transiciones claras hacia ambas porterías.\n\n"
            "Relación Riesgo/Beneficio: Buscar que ambos anotan y la línea de más de 2.5 goles a cuota 2.05 es estadísticamente una de las opciones más fiables de la jornada."
        )
    elif "Sporting" in match_name:
        return (
            "Contexto ambiental en Lisboa: El Estádio José Alvalade empuja al Sporting CP a volcarse en campo contrario con un caudal ofensivo incesante sostenido por su línea de mediapuntas.\n\n"
            "Estructura táctica del rival: El SC Braga concede ventajas considerables en los duelos individuales por los costados, lo que propiciará un alto volumen de llegadas a línea de fondo y saques de esquina.\n\n"
            "Relación Riesgo/Beneficio: La victoria del equipo local acompañada de córneres y goles a cuota 2.15 refleja un margen matemático de acierto muy superior al de las cuotas directas."
        )
    else:
        return (
            "Contexto ambiental en Buenos Aires: El ambiente en La Bombonera genera un voltaje competitivo absoluto, con entradas duras y un clima de máxima tensión en cada disputa dividida.\n\n"
            "Estructura táctica del rival: Los duelos de máxima rivalidad entre Boca Juniors y River Plate se deciden por detalles en la medular, propiciando un alto índice de faltas tácticas y amonestaciones tempranas.\n\n"
            "Relación Riesgo/Beneficio: Apostar por el mercado de tarjetas y doble oportunidad a cuota 2.20 es una alternativa de valor excelentemente calibrada para este perfil de encuentro."
        )

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
    
    if weekday in [4, 5, 6]:
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
    else:
        msg = (
            "☀️ <b>¡BUENOS DÍAS A TODOS! JORNADA DE VALOR DE HOY</b> ☀️\n\n"
            "☕ Ya tenemos filtrados los encuentros del día con mayor valor táctico.\n\n"
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
        time.sleep(6)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Tipster Gemini HTTP Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error servidor HTTP: {e}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Tipster Inteligente Gemini en ejecución...")

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
