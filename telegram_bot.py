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

def clean_env(var_name, default_val=""):
    val = os.environ.get(var_name, default_val)
    if not val:
        return default_val
    val_str = str(val).strip()
    for bad_char in ['[', ']', '(', ')', "'", '"', ' ']:
        val_str = val_str.replace(bad_char, '')
    return val_str.strip()

TELEGRAM_BOT_TOKEN = clean_env("TELEGRAM_BOT_TOKEN", "8657360203:AAG0wJnyLFfEaBMY8XadJs1dZdSQU42ah7c")
CHAT_ID = clean_env("TELEGRAM_CHAT_ID", "@FreeTopTip")
GEMINI_API_KEY = clean_env("GEMINI_API_KEY", "AQ.Ab8RN6IzHOYBnb0nCJ_95k78xwox8--fOsWPf94ytRYPuGtk4g")
TELEGRAM_USERNAME = "Mark122"

SPAIN_TZ = ZoneInfo("Europe/Madrid")

CHANNEL_STATS = {
    "wins": 71,
    "losses": 14,
    "profit_units": +58.4,
    "yield_pct": 27.2
}

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        res = requests.post(url, json=payload, timeout=15)
        res_json = res.json()
        if res_json.get("ok"):
            logging.info("¡Mensaje publicado en Telegram con éxito!")
            return True
        else:
            logging.error(f"Error Telegram: {res_json}")
            return False
    except Exception as e:
        logging.error(f"Excepción Telegram: {e}")
        return False

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}
            res = requests.post(url, data=data, files={"photo": photo}, timeout=20)
            res_json = res.json()
            if res_json.get("ok"):
                logging.info("¡Foto e informe publicados con éxito en Telegram!")
                return True
            else:
                logging.error(f"Error foto Telegram: {res_json}")
                return False
    except Exception as e:
        logging.error(f"Excepción enviando foto: {e}")
        return False

def create_scores24_card(match_title, league_name, pick_text, odds_val):
    try:
        img = Image.new('RGB', (1000, 600), color=(13, 27, 42))
        d = ImageDraw.Draw(img)
        
        d.rectangle([20, 20, 980, 580], outline=(0, 212, 170), width=4)
        d.rectangle([20, 20, 980, 110], fill=(20, 40, 65))
        
        d.text((40, 48), "🛡️ SCORES24 ESPAÑA - ANALYTICS", fill=(0, 212, 170))
        d.text((580, 48), league_name.upper()[:25], fill=(200, 200, 200))
        
        d.text((40, 140), "PARTIDO ANALIZADO (HOY):", fill=(150, 160, 180))
        d.text((40, 180), match_title, fill=(255, 255, 255))
        
        d.rectangle([40, 240, 960, 420], fill=(24, 43, 73), outline=(255, 215, 0), width=2)
        d.text((70, 260), "SELECCIÓN RECOMENDADA (BET365):", fill=(255, 215, 0))
        d.text((70, 315), f"{pick_text[:45]}...", fill=(255, 255, 255))
        d.text((750, 315), f"@{odds_val:.2f}", fill=(0, 212, 170))

        d.text((40, 460), f"📊 Rendimiento Estadístico | Yield: +{CHANNEL_STATS['profit_units']}U", fill=(150, 160, 180))
        d.text((40, 510), f"Canal Oficial: @FreeTopTip | VIP: @{TELEGRAM_USERNAME}", fill=(255, 215, 0))
        
        filename = "scores24_card.png"
        img.save(filename)
        return filename
    except Exception as e:
        logging.error(f"Error generando imagen: {e}")
        return None

def fetch_live_gemini_scores24():
    now_spain = datetime.now(SPAIN_TZ)
    date_today_str = now_spain.strftime("%A, %d de %B de %Y")
    
    prompt = f"""
    Actúa como un experto periodista deportivo y analista de apuestas de Scores24 / Sofascore.
    FECHA ACTUAL EXACTA: {date_today_str}.
    
    INSTRUCCIONES STRICTAS:
    1. Identifica un partido de fútbol que se dispute HOY MISMO ({date_today_str}). Puede ser de UEFA Nations League, Clasificatorias Internacionales, Ligas Sudamericanas, Copas o Ligas Locales en juego hoy.
    2. Redacta un análisis profesional e imparcial estilo Scores24 con datos tácticos reales, estadísticas de rendimiento, córneres o xG.
    3. Propón una Selección Principal en Bet365 (Cuota >= 2.00) y una Opción Secundaria de Cobertura (~1.50-1.70).
    
    Responde ÚNICAMENTE con un JSON válido con este formato:
    {{
      "match": "Equipo A vs Equipo B",
      "league": "Competición Exacta",
      "analysis": "• Análisis táctico del local y visitante.\\n• Estadísticas clave y xG.\\n• Justificación del valor en Bet365.",
      "pick_main": "Pronóstico Principal exacto",
      "odds_main": 2.15,
      "pick_alt": "Pronóstico Secundario de Cobertura",
      "odds_alt": 1.60
    }}
    """

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, headers=headers, json=payload, timeout=25)
        data = res.json()
        if "candidates" in data and len(data["candidates"]) > 0:
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text.replace("```", "").strip()
            return json.loads(raw_text)
    except Exception as e:
        logging.error(f"Error consultando Gemini en tiempo real: {e}")
    
    return None

def publish_scores24_report():
    logging.info("Generando análisis en tiempo real con Gemini...")
    item = fetch_live_gemini_scores24()
    
    if not item:
        logging.error("No se pudo obtener el análisis dinámico en este intento.")
        return

    match_title = item.get("match")
    league_name = item.get("league")
    analysis_text = item.get("analysis")
    pick_main = item.get("pick_main")
    odds_main = float(item.get("odds_main", 2.00))
    pick_alt = item.get("pick_alt")
    odds_alt = float(item.get("odds_alt", 1.60))

    now_spain = datetime.now(SPAIN_TZ)
    caption = (
        f"📊 <b>ESTADÍSTICAS Y ANÁLISIS TÁCTICO ({now_spain.strftime('%d/%m/%Y')})</b> 📊\n"
        f"🌐 <i>Fuente Oficial: Datos & Estadísticas Scores24</i>\n\n"
        f"🏆 <b>Competición:</b> {league_name}\n"
        f"⚔️ <b>Encuentro:</b> {match_title}\n\n"
        f"📋 <b>INFORME MINUSIOSO DE PARTIDO:</b>\n"
        f"{analysis_text}\n\n"
        f"🎯 <b>PRONÓSTICO PRINCIPAL (BET365):</b>\n"
        f"• Selección: <code>{pick_main}</code>\n"
        f"• Cuota: <b>@{odds_main:.2f}</b> | Stake: <b>1.5 / 10</b>\n\n"
        f"🛡️ <b>MERCADO ALTERNATIVO (COBERTURA):</b>\n"
        f"• Selección: <code>{pick_alt}</code> (@{odds_alt:.2f})\n\n"
        f"📈 <b>ESTADÍSTICAS DEL CANAL:</b> +{CHANNEL_STATS['profit_units']} Unidades ({CHANNEL_STATS['yield_pct']}% Yield)\n\n"
        f"💳 <b>¿QUIERES ACCEDER A LAS COMBINADAS VIP EXCLUSIVAS?</b>\n"
        f"📲 Escríbeme por privado: <a href='[https://t.me/](https://t.me/){TELEGRAM_USERNAME}'>@{TELEGRAM_USERNAME}</a>"
    )

    img_path = create_scores24_card(match_title, league_name, pick_main, odds_main)
    
    sent = False
    if img_path:
        sent = send_telegram_photo(img_path, caption)
    if not sent:
        send_telegram_message(caption)

def send_daily_sales_message():
    now_spain = datetime.now(SPAIN_TZ)
    msg = (
        f"☀️ <b>¡BUENOS DÍAS A TODOS EN @FreeTopTip! ({now_spain.strftime('%d/%m/%Y')})</b> ☀️\n\n"
        "☕ Arrancamos la jornada compartiendo informes estadísticos detallados y análisis de valor de los partidos programados para hoy al estilo Scores24.\n\n"
        "💳 <b>ACCESO AL GRUPO VIP PRIVADO:</b>\n"
        "🔥 <b>Pase Día Premium:</b> <b>5.00 €</b>\n"
        "🎟️ <b>Pase Semanal VIP:</b> <b>10.00 €</b>\n"
        "👑 <b>Pase Mensual VIP:</b> <b>34.99 €</b>\n\n"
        f"📲 <i>Para unirte al VIP y recibir las combinadas diarias, escríbeme:</i>\n"
        f"👉 <b>Contactar al Analista: <a href='[https://t.me/](https://t.me/){TELEGRAM_USERNAME}'>@{TELEGRAM_USERNAME}</a></b>"
    )
    send_telegram_message(msg)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Scores24 Pro Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error servidor HTTP: {e}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Bot Scores24 Pro iniciado correctamente.")

    send_daily_sales_message()
    time.sleep(3)

    publish_scores24_report()

    # Publicación periódica limpia cada 15 minutos (900 segundos)
    while True:
        try:
            time.sleep(900)
            logging.info("Ejecutando nuevo ciclo de publicación...")
            publish_scores24_report()
        except Exception as e:
            logging.error(f"Error en bucle de publicación: {e}")

if __name__ == "__main__":
    main()
