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

# Variables de Entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6IzHOYBnb0nCJ_95k78xwox8--fOsWPf94ytRYPuGtk4g").strip()
TELEGRAM_USERNAME = "Mark122"  # Usuario para compras VIP

SPAIN_TZ = ZoneInfo("Europe/Madrid")

# Stats y Estado del Canal
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
        logging.error(f"Error enviando mensaje: {e}")
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
        logging.error(f"Error enviando foto: {e}")
        return None

def create_scores24_card(match_title, league_name, pick_text, odds_val):
    try:
        img = Image.new('RGB', (1000, 600), color=(13, 27, 42))
        d = ImageDraw.Draw(img)
        
        # Marco y fondo
        d.rectangle([20, 20, 980, 580], outline=(0, 212, 170), width=4)
        d.rectangle([20, 20, 980, 110], fill=(20, 40, 65))
        
        # Cabecera
        d.text((40, 48), "🛡️ TOPTIPS OFFICIAL ANALYTICS", fill=(0, 212, 170))
        d.text((580, 48), league_name.upper()[:25], fill=(200, 200, 200))
        
        # Partido
        d.text((40, 140), "PARTIDO ANALIZADO EN DETALLE:", fill=(150, 160, 180))
        d.text((40, 180), match_title, fill=(255, 255, 255))
        
        # Pronóstico
        d.rectangle([40, 240, 960, 420], fill=(24, 43, 73), outline=(255, 215, 0), width=2)
        d.text((70, 260), "SELECCIÓN RECOMENDADA (BET365):", fill=(255, 215, 0))
        d.text((70, 315), f"{pick_text[:45]}...", fill=(255, 255, 255))
        d.text((750, 315), f"@{odds_val:.2f}", fill=(0, 212, 170))

        # Pie
        d.text((40, 460), f"📊 Métricas: Rendimiento Táctico | Yield: +{CHANNEL_STATS['profit_units']}U", fill=(150, 160, 180))
        d.text((40, 510), f"Canal Oficial: @FreeTopTip | Suscripción VIP: @{TELEGRAM_USERNAME}", fill=(255, 215, 0))
        
        filename = "scores24_card.png"
        img.save(filename)
        return filename
    except Exception as e:
        logging.error(f"Error creando tarjeta gráfica: {e}")
        return None

def fetch_dynamic_daily_picks():
    """Gemini selecciona los partidos de HOY de cualquier liga y genera el análisis."""
    now_spain = datetime.now(SPAIN_TZ)
    date_today = now_spain.strftime("%d de %B de %Y")
    
    prompt = f"""
    Eres un analista táctico de fútbol profesional. Hoy es {date_today}.
    
    Genera 4 partidos REALES que se disputen HOY ({date_today}) en cualquier liga del mundo (grandes ligas, secundarias o sudamericanas).
    Para cada uno crea una selección Bet365 a cuota >= 2.00 y redacta un análisis técnico dividido estrictamente en:
    1. Contexto ambiental en el estadio
    2. Estructura táctica del rival
    3. Relación Riesgo/Beneficio
    
    Devuelve ÚNICAMENTE un array JSON válido con este formato:
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
            text_res = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if text_res.startswith("```json"):
                text_res = text_res.replace("```json", "").replace("```", "").strip()
            elif text_res.startswith("```"):
                text_res = text_res.replace("```", "").strip()
            return json.loads(text_res)
    except Exception as e:
        logging.error(f"Error llamando a Gemini: {e}")
    
    return []

def send_sales_banner_morning():
    """Mensaje de apertura de jornada enfocado en conversión VIP."""
    msg = (
        "☀️ <b>¡BUENOS DÍAS A TODOS EN @FreeTopTip!</b> ☀️\n\n"
        "☕ Arrancamos una nueva jornada con todo el equipo de análisis trabajando en los mejores mercados del día.\n\n"
        "🔥 <b>¿QUÉ INCLUYE EL GRUPO VIP DE HOY?</b>\n"
        "✅ <b>Combinada Premium del Día</b> (Cuota @3.80+)\n"
        "✅ <b>Stake 3 de Máxima Confianza</b> (Partido filtrado en exclusiva)\n"
        "✅ <b>Alertas Live en directo</b> según la evolución del marcador\n\n"
        "💳 <b>TARIFAS DE ACCESO DIRECTO:</b>\n"
        "🎟️ <b>Pase Semanal VIP:</b> <b>10.00 €</b>\n"
        "👑 <b>Pase Mensual VIP:</b> <b>34.99 €</b>\n\n"
        f"📲 <i>Escríbeme por privado para unirte antes de que empiecen los partidos:</i>\n"
        f"👉 <b>Contactar al Analista: @{TELEGRAM_USERNAME}</b>"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": "👑 Solicitar Acceso al VIP", "url": f"[https://t.me/](https://t.me/){TELEGRAM_USERNAME}"}]
        ]
    }
    send_telegram_message(msg, reply_markup=keyboard)

def send_midday_vip_reminder():
    """Mensaje de venta estratégica a mitad del día (FOMO)."""
    msg = (
        "🚨 <b>¡ÚLTIMAS PLAZAS PARA LA COMBINADA VIP DE HOY!</b> 🚨\n\n"
        "📊 Tras revisar la bajada de cuotas y las alineaciones confirmadas, ya tenemos lista la <b>Combinada de Valor</b> para nuestros miembros VIP.\n\n"
        "🎯 <b>Métricas de la apuesta VIP de hoy:</b>\n"
        "• Cuota Total: <b>@4.15</b>\n"
        "• Confianza / Stake: <b>2.5 / 10</b>\n"
        "• Competiciones: Ligas Europeas & Internacionales\n\n"
        f"📲 <i>Accede ahora antes de que comience el primer encuentro:</i>\n"
        f"👉 <b>Escribir al Analista: @{TELEGRAM_USERNAME}</b>"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔥 Entrar al Grupo VIP", "url": f"[https://t.me/](https://t.me/){TELEGRAM_USERNAME}"}]
        ]
    }
    send_telegram_message(msg, reply_markup=keyboard)

def send_evening_recap():
    """Resumen de cierre de jornada mostrando la rentabilidad del canal."""
    msg = (
        "📈 <b>CIERRE DE JORNADA Y BALANCE DE RESULTADOS</b> 📈\n\n"
        "Finalizamos otro día aplicando nuestro método de análisis estadístico en @FreeTopTip.\n\n"
        f"📊 <b>ESTADÍSTICAS GENERALES DEL CANAL:</b>\n"
        f"🟢 <b>Verdes / Aciertos:</b> {CHANNEL_STATS['wins']}\n"
        f"🔴 <b>Fallos:</b> {CHANNEL_STATS['losses']}\n"
        f"💰 <b>Beneficio Neto:</b> +{CHANNEL_STATS['profit_units']} Unidades (+{CHANNEL_STATS['yield_pct']}% Yield)\n\n"
        "La constancia y la gestión de banca son la clave del éxito a largo plazo.\n\n"
        f"👑 <b>¿Quieres asegurar tus ganancias diarias? Pasa al VIP: @{TELEGRAM_USERNAME}</b>"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": "💳 Unirme al VIP para Mañana", "url": f"[https://t.me/](https://t.me/){TELEGRAM_USERNAME}"}]
        ]
    }
    send_telegram_message(msg, reply_markup=keyboard)

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

def run_daily_routine():
    """Rutina diaria automatizada."""
    # 1. Buenos días y venta inicial (08:00 AM)
    send_sales_banner_morning()
    time.sleep(5)
    
    # 2. Publicación de pronósticos gratuitos del día
    picks = fetch_dynamic_daily_picks()
    for item in picks:
        match = item.get("match", "Partido de Hoy")
        league = item.get("league", "Competición")
        pick = item.get("pick", "Selección de Valor")
        odds = float(item.get("odds", 2.00))
        analysis = item.get("analysis", "Análisis detallado en proceso.")
        
        publish_pick(match, league, pick, odds, analysis)
        time.sleep(8)
        
    # 3. Recordatorio VIP de mediodía
    time.sleep(10)
    send_midday_vip_reminder()

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Tipster Inteligente y Estratégico Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error servidor HTTP: {e}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Tipster Inteligente en ejecución...")

    # Ejecución inmediata al arrancar el servidor
    run_daily_routine()

    last_executed_day = -1
    recap_sent_today = False

    while True:
        try:
            now_spain = datetime.now(SPAIN_TZ)
            current_day = now_spain.day
            current_hour = now_spain.hour

            # Publicación de jornada diaria a las 08:00 AM
            if current_day != last_executed_day and current_hour == 8:
                run_daily_routine()
                last_executed_day = current_day
                recap_sent_today = False

            # Cierre de jornada y balance a las 22:30 PM
            if current_hour == 22 and not recap_sent_today:
                send_evening_recap()
                recap_sent_today = True

        except Exception as e:
            logging.error(f"Error en bucle principal: {e}")

        time.sleep(30)

if __name__ == "__main__":
    main()
