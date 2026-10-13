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

def fetch_today_picks_from_gemini():
    """Gemini busca los partidos REALES de la jornada de hoy y devuelve los pronósticos y análisis estructurados."""
    now_spain = datetime.now(SPAIN_TZ)
    today_str = now_spain.strftime("%d de %B de %Y")
    
    prompt = f"""
    Eres un analista táctico de fútbol profesional y tipster para el canal @FreeTopTip.
    Hoy es {today_str}.
    
    TAREA:
    Identifica 4 partidos de fútbol REALES que se jueguen HOY ({today_str}) en cualquier liga o competición oficial del mundo (Champions League, ligas europeas, sudamericanas, selecciones o ligas menores).
    
    Para cada partido, genera un pronóstico a cuota >= 2.00 en Bet365 y un análisis extremadamente detallado.
    
    ESTRUCTURA OBLIGATORIA DEL ANÁLISIS DE CADA PARTIDO:
    1. Contexto ambiental en el estadio: Describe la presión local, ambiente y cómo saldrá el equipo.
    2. Estructura táctica del rival: Explica la propuesta de ambos clubes, espacios en defensa y volumen ofensivo.
    3. Relación Riesgo/Beneficio: Justifica estadísticamente la cuota.
    
    Responde ÚNICAMENTE con una lista JSON válida en este formato exacto (sin etiquetas markdown ```json):
    [
      {{
        "match": "Equipo A vs Equipo B",
        "league": "Nombre de la Competición",
        "pick": "Selección o Crear Apuesta recomendada",
        "odds": 2.10,
        "analysis": "Contexto ambiental en el estadio: ...\\n\\nEstructura táctica del rival: ...\\n\\nRelación Riesgo/Beneficio: ..."
      }}
    ]
    """

    try:
        url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=){GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        data = res.json()
        if "candidates" in data and len(data["candidates"]) > 0:
            text_res = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if text_res.startswith("```json"):
                text_res = text_res.replace("```json", "").replace("```", "").strip()
            elif text_res.startswith("```"):
                text_res = text_res.replace("```", "").strip()
            return json.loads(text_res)
    except Exception as e:
        logging.error(f"Error generando picks de hoy con Gemini: {e}")
    
    return []

def publish_pick(match_title, league_name, pick_text, odds_val, analysis_text):
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

def run_daily_routine():
    send_daily_sales_message()
    time.sleep(3)
    
    today_picks = fetch_today_picks_from_gemini()
    
    for pick_item in today_picks:
        match = pick_item.get("match", "Partido de Hoy")
        league = pick_item.get("league", "Competición")
        pick = pick_item.get("pick", "Selección Recomendada")
        odds = float(pick_item.get("odds", 2.00))
        analysis = pick_item.get("analysis", "Análisis detallado en preparación.")
        
        publish_pick(match, league, pick, odds, analysis)
        time.sleep(6)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Tipster 100% Dinámico Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error servidor HTTP: {e}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Tipster Inteligente Gemini Diario en ejecución...")

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
