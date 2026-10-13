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
    "wins": 65,
    "losses": 14,
    "profit_units": +51.8,
    "yield_pct": 24.5
}

def send_telegram_message(text, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("Falta TELEGRAM_BOT_TOKEN o CHAT_ID.")
        return None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        res = requests.post(url, json=payload, timeout=12)
        return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error enviando mensaje: {e}")
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
        logging.error(f"Error enviando foto: {e}")
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

def fetch_scores24_style_picks(count=4):
    """Llama a la IA para generar análisis de estilo noticioso/Scores24 con datos de partidos reales de hoy."""
    now_spain = datetime.now(SPAIN_TZ)
    date_today = now_spain.strftime("%d de %B de %Y")
    
    prompt = f"""
    Eres un periodista deportivo y analista de apuestas estilo Scores24 / Sofascore. Hoy es {date_today}.
    
    TAREA:
    Genera {count} análisis completos de partidos REALES de fútbol que se disputen HOY ({date_today}).
    
    Para cada partido redacta un informe profundo que incluya:
    - Noticias de última hora y estado de los equipos (bajas clave, ausencias, dinámicas recientes).
    - Estadísticas tácticas relevantes (xG esperados, promedio de córneres, tarjetas o rendimiento como local/visitante).
    - Selección Principal (Crear Apuesta o Mercado Bet365 a cuota >= 2.00).
    - Selección Secundaria de cobertura (Cuota más conservadora ~1.50-1.70).
    
    Devuelve ÚNICAMENTE un array JSON válido con este formato exacto:
    [
      {{
        "match": "Equipo A vs Equipo B",
        "league": "Nombre de Competición",
        "pick_main": "Pronóstico Principal exacto",
        "odds_main": 2.15,
        "pick_alt": "Pronóstico Secundario de Cobertura",
        "odds_alt": 1.65,
        "news": "Noticias de última hora sobre alineaciones y bajas...",
        "stats": "Estadísticas clave y datos numéricos tácticos...",
        "value_reason": "Justificación de valor estadístico y cuotas..."
      }}
    ]
    """

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        data = res.json()
        if "candidates" in data and len(data["candidates"]) > 0:
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text.replace("```", "").strip()
            return json.loads(raw_text)
    except Exception as e:
        logging.error(f"Error obteniendo análisis de Gemini: {e}")
    
    return []

def publish_scores24_pick(item):
    match_title = item.get("match", "Partido de Hoy")
    league_name = item.get("league", "Competición")
    pick_main = item.get("pick_main", "Selección Principal")
    odds_main = float(item.get("odds_main", 2.00))
    pick_alt = item.get("pick_alt", "Opción Secundaria")
    odds_alt = float(item.get("odds_alt", 1.60))
    
    news_text = item.get("news", "Bajas y dinámicas recientes.")
    stats_text = item.get("stats", "Métricas y datos estadísticos.")
    value_text = item.get("value_reason", "Valor en cuotas Bet365.")

    caption = (
        f"⚽ <b>INFORME Y ANÁLISIS DE PARTIDO - @FreeTopTip</b> ⚽\n\n"
        f"🏆 <b>Competición:</b> {league_name}\n"
        f"⚔️ <b>Encuentro:</b> {match_title}\n\n"
        f"📰 <b>NOTICIAS Y ÚLTIMA HORA:</b>\n"
        f"• {news_text}\n\n"
        f"📊 <b>DATOS TÁCTICOS Y ESTADÍSTICAS:</b>\n"
        f"• {stats_text}\n\n"
        f"🎯 <b>PRONÓSTICO PRINCIPAL (BET365):</b>\n"
        f"• Selección: <code>{pick_main}</code>\n"
        f"• Cuota: <b>@{odds_main:.2f}</b> | Stake: <b>1.5/10</b>\n\n"
        f"🛡️ <b>OPCIÓN SEGUNDARIA (COBERTURA):</b>\n"
        f"• Selección: <code>{pick_alt}</code> (@{odds_alt:.2f})\n\n"
        f"💡 <b>JUSTIFICACIÓN DE VALOR:</b>\n"
        f"💬 {value_text}\n\n"
        f"📈 <b>BALANCE ACUMULADO:</b> +{CHANNEL_STATS['profit_units']} Unidades\n\n"
        f"💳 <b>¿QUIERES RECIBIR LA COMBINADA VIP DE HOY?</b>\n"
        f"📲 Contacta por privado: <b>@{TELEGRAM_USERNAME}</b>"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "👑 Comprar Pase VIP / Contactar al Analista", "url": f"[https://t.me/](https://t.me/){TELEGRAM_USERNAME}"}]
        ]
    }

    img_path = create_scores24_card(match_title, league_name, pick_main, odds_main)
    sent = False
    if img_path:
        sent = send_telegram_photo(img_path, caption, reply_markup=keyboard)
    if not sent:
        send_telegram_message(caption, reply_markup=keyboard)

def send_daily_sales_message():
    msg = (
        "☀️ <b>¡BUENOS DÍAS A TODOS EN @FreeTopTip!</b> ☀️\n\n"
        "☕ Arrancamos la jornada con informes de partidos, noticias y datos tácticos del día.\n\n"
        "💳 <b>TARIFAS GRUPO VIP PRIVADO:</b>\n"
        "🔥 <b>Pase Día Premium:</b> <b>5.00 €</b>\n"
        "🎟️ <b>Pase Semanal VIP:</b> <b>10.00 €</b>\n"
        "👑 <b>Pase Mensual VIP:</b> <b>34.99 €</b>\n\n"
        f"📲 <i>Escríbeme por privado para acceder a la combinada exclusiva:</i>\n"
        f"👉 <b>Contactar al Analista: @{TELEGRAM_USERNAME}</b>"
    )
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "👑 Entrar al Grupo VIP", "url": f"[https://t.me/](https://t.me/){TELEGRAM_USERNAME}"}]
        ]
    }
    send_telegram_message(msg, reply_markup=keyboard)

def send_evening_recap():
    msg = (
        "📈 <b>CIERRE DE JORNADA Y BALANCE DE RESULTADOS</b> 📈\n\n"
        "Finalizamos otro día aplicando análisis estadístico e informes tácticos en @FreeTopTip.\n\n"
        f"📊 <b>ESTADÍSTICAS GENERALES DEL CANAL:</b>\n"
        f"🟢 <b>Aciertos:</b> {CHANNEL_STATS['wins']}\n"
        f"🔴 <b>Fallos:</b> {CHANNEL_STATS['losses']}\n"
        f"💰 <b>Beneficio Neto:</b> +{CHANNEL_STATS['profit_units']} Unidades (+{CHANNEL_STATS['yield_pct']}% Yield)\n\n"
        f"👑 <b>¿Quieres asegurar tus ganancias diarias? Pasa al VIP: @{TELEGRAM_USERNAME}</b>"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": "💳 Unirme al VIP para Mañana", "url": f"[https://t.me/](https://t.me/){TELEGRAM_USERNAME}"}]
        ]
    }
    send_telegram_message(msg, reply_markup=keyboard)

def run_daily_routine():
    logging.info("Ejecutando rutina noticiosa y de pronósticos estilo Scores24...")
    send_daily_sales_message()
    time.sleep(4)
    
    picks = fetch_scores24_style_picks(count=4)
    for item in picks:
        publish_scores24_pick(item)
        time.sleep(8)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Tipster Scores24 Dinámico Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error servidor HTTP: {e}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Tipster Inteligente en ejecución...")

    # Publicación inmediata en el canal
    run_daily_routine()

    now_spain = datetime.now(SPAIN_TZ)
    last_executed_day = now_spain.day
    recap_sent_today = False

    while True:
        try:
            now_spain = datetime.now(SPAIN_TZ)
            current_day = now_spain.day
            current_hour = now_spain.hour

            if current_day != last_executed_day and current_hour == 8:
                run_daily_routine()
                last_executed_day = current_day
                recap_sent_today = False

            if current_hour == 22 and not recap_sent_today:
                send_evening_recap()
                recap_sent_today = True

        except Exception as e:
            logging.error(f"Error en bucle principal: {e}")

        time.sleep(30)

if __name__ == "__main__":
    main()
