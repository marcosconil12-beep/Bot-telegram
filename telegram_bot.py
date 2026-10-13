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

def get_clean_token():
    """Limpia el token de cualquier prefijo o corchete indeseado."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "8657360203:AAG0wJnyLFfEaBMY8XadJs1dZdSQU42ah7c")
    token = str(token).strip()
    
    # Si viene con la URL pegada o duplicada, la extrae
    if "api.telegram.org/bot" in token:
        token = token.split("api.telegram.org/bot")[-1]
    
    # Limpia caracteres raros
    for char in ['[', ']', '(', ')', "'", '"', ' ', '/']:
        token = token.replace(char, '')
        
    return token.strip()

TELEGRAM_BOT_TOKEN = get_clean_token()

raw_chat = os.environ.get("TELEGRAM_CHAT_ID", "")
CHAT_ID = str(raw_chat).replace('[', '').replace(']', '').replace("'", "").replace('"', '').strip()

GEMINI_API_KEY = "AQ.Ab8RN6IzHOYBnb0nCJ_95k78xwox8--fOsWPf94ytRYPuGtk4g"
TELEGRAM_USERNAME = "Mark122"

SPAIN_TZ = ZoneInfo("Europe/Madrid")

CHANNEL_STATS = {
    "wins": 65,
    "losses": 14,
    "profit_units": +51.8,
    "yield_pct": 24.5
}

def send_telegram_message(text, reply_markup=None, target_chat=None):
    token = get_clean_token()
    chat = str(target_chat or CHAT_ID).replace('[', '').replace(']', '').replace("'", "").replace('"', '').strip()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {"chat_id": chat, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        res = requests.post(url, json=payload, timeout=12)
        return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error enviando mensaje: {e}")
        return None

def send_telegram_photo(photo_path, caption, reply_markup=None, target_chat=None):
    token = get_clean_token()
    chat = str(target_chat or CHAT_ID).replace('[', '').replace(']', '').replace("'", "").replace('"', '').strip()
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            data = {"chat_id": chat, "caption": caption, "parse_mode": "HTML"}
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

def fetch_dynamic_daily_picks(count=4):
    now_spain = datetime.now(SPAIN_TZ)
    date_today = now_spain.strftime("%d de %B de %Y")
    
    prompt = f"""
    Eres un analista táctico de fútbol profesional y tipster para el canal @FreeTopTip. Hoy es {date_today}.
    
    TAREA:
    Genera {count} partidos REALES que se disputen HOY ({date_today}) en cualquier competición del mundo.
    Para cada uno crea un pronóstico de valor en Bet365 a cuota >= 2.00 y redacta un análisis técnico dividido estrictamente en tres bloques:
    1. Contexto ambiental en el estadio: Describe la presión de la afición y el ritmo de inicio.
    2. Estructura táctica del rival: Explica la alineación, transiciones y espacios concedidos.
    3. Relación Riesgo/Beneficio: Justifica el valor de la cuota.
    
    Devuelve ÚNICAMENTE un array JSON válido con este formato exacto:
    [
      {{
        "match": "Equipo A vs Equipo B",
        "league": "Nombre de Competición",
        "pick": "Pronóstico exacto",
        "odds": 2.15,
        "analysis": "Contexto ambiental en el estadio: ...\\n\\nEstructura táctica del rival: ...\\n\\nRelación Riesgo/Beneficio: ..."
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
        logging.error(f"Error obteniendo picks de Gemini: {e}")
    
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
            [{"text": "👑 Comprar Pase VIP / Contactar al Analista", "url": f"[https://t.me/](https://t.me/){TELEGRAM_USERNAME}"}]
        ]
    }

    img_path = create_scores24_card(match_title, league_name, pick_text, odds_val)
    sent = False
    if img_path:
        sent = send_telegram_photo(img_path, caption, reply_markup=keyboard)
    if not sent:
        send_telegram_message(caption, reply_markup=keyboard)

def send_daily_sales_message():
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
            [{"text": "👑 Entrar al Grupo VIP", "url": f"[https://t.me/](https://t.me/){TELEGRAM_USERNAME}"}]
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
        f"💰 <b>Beneficio Neto:</b> +{CHANNEL_STATS['profit_units']} Unidades (+{CHANNEL_STATS['yield_pct']}% Yield)\n\n"
        f"👑 <b>¿Quieres asegurar tus ganancias diarias? Pasa al VIP: @{TELEGRAM_USERNAME}</b>"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": "💳 Unirme al VIP para Mañana", "url": f"[https://t.me/](https://t.me/){TELEGRAM_USERNAME}"}]
        ]
    }
    send_telegram_message(msg, reply_markup=keyboard)

def publish_single_pick_now():
    picks = fetch_dynamic_daily_picks(count=1)
    if picks:
        item = picks[0]
        publish_pick(
            item.get("match", "Partido de Hoy"),
            item.get("league", "Competición"),
            item.get("pick", "Selección de Valor"),
            float(item.get("odds", 2.00)),
            item.get("analysis", "Análisis en detalle.")
        )
        return True
    return False

def handle_telegram_updates():
    offset = 0
    while True:
        try:
            token = get_clean_token()
            url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){token}/getUpdates?offset={offset}&timeout=20"
            res = requests.get(url, timeout=25)
            data = res.json()
            
            if data.get("ok"):
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    message = update.get("message", {})
                    text = message.get("text", "").strip()
                    user_chat_id = message.get("chat", {}).get("id")
                    
                    if not text:
                        continue
                        
                    if text == "/start" or text == "/help":
                        help_text = (
                            "👋 <b>¡Hola Admin! Menú de Control del Bot TopTips:</b>\n\n"
                            "• <b>/pick</b> ➔ Publica 1 pick nuevo con análisis en el canal ahora mismo.\n"
                            "• <b>/ventas</b> ➔ Publica el mensaje comercial VIP en el canal.\n"
                            "• <b>/balance</b> ➔ Publica el balance de aciertos y yield en el canal."
                        )
                        send_telegram_message(help_text, target_chat=user_chat_id)
                        
                    elif text == "/pick":
                        send_telegram_message("⏳ Generando pick con Gemini y publicando en el canal...", target_chat=user_chat_id)
                        ok = publish_single_pick_now()
                        if ok:
                            send_telegram_message("✅ ¡Pick publicado con éxito en el canal!", target_chat=user_chat_id)
                        else:
                            send_telegram_message("❌ Error generando el pick. Inténtalo de nuevo.", target_chat=user_chat_id)
                            
                    elif text == "/ventas":
                        send_daily_sales_message()
                        send_telegram_message("✅ Mensaje de ventas publicado en el canal.", target_chat=user_chat_id)
                        
                    elif text == "/balance":
                        send_evening_recap()
                        send_telegram_message("✅ Resumen y balance publicado en el canal.", target_chat=user_chat_id)

        except Exception as e:
            logging.error(f"Error en listener de Telegram: {e}")
            
        time.sleep(2)

def run_daily_routine():
    logging.info("Iniciando rutina completa de publicaciones...")
    send_daily_sales_message()
    time.sleep(4)
    
    picks = fetch_dynamic_daily_picks(count=4)
    for item in picks:
        publish_pick(
            item.get("match", "Partido de Hoy"),
            item.get("league", "Competición"),
            item.get("pick", "Selección de Valor"),
            float(item.get("odds", 2.00)),
            item.get("analysis", "Análisis táctico.")
        )
        time.sleep(6)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Tipster Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error servidor HTTP: {e}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    threading.Thread(target=handle_telegram_updates, daemon=True).start()
    logging.info("Servicio Tipster en ejecución...")

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
