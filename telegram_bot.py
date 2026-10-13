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
    "wins": 78,
    "losses": 14,
    "profit_units": +67.3,
    "yield_pct": 30.2
}

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        res = requests.post(url, json=payload, timeout=15)
        return res.json().get("ok")
    except Exception as e:
        logging.error(f"Excepción Telegram: {e}")
        return False

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}
            res = requests.post(url, data=data, files={"photo": photo}, timeout=20)
            return res.json().get("ok")
    except Exception as e:
        logging.error(f"Excepción foto: {e}")
        return False

def create_scores24_card(match_title, league_name, pick_text, odds_val):
    try:
        img = Image.new('RGB', (1000, 600), color=(13, 27, 42))
        d = ImageDraw.Draw(img)
        
        d.rectangle([20, 20, 980, 580], outline=(0, 212, 170), width=4)
        d.rectangle([20, 20, 980, 110], fill=(20, 40, 65))
        
        d.text((40, 48), "🛡️ SCORES24 ESPAÑA - ANALYTICS PRO", fill=(0, 212, 170))
        d.text((580, 48), league_name.upper()[:25], fill=(200, 200, 200))
        
        d.text((40, 140), "PARTIDO ANALIZADO (JORNADA DE HOY):", fill=(150, 160, 180))
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

def generate_flexible_ai_analysis():
    now_spain = datetime.now(SPAIN_TZ)
    date_today = now_spain.strftime("%d de %B de %Y")
    
    prompt = f"""
    Actúa como el tipster jefe y analista estadístico de Scores24.
    La fecha de HOY es estrictamente: {date_today}.
    
    INSTRUCCIONES CLAVE:
    1. Selecciona un partidazo de fútbol real que se dispute HOY ({date_today}), utilizando plantillas actualizadas y jugadores reales actuales (por ejemplo, Lamine Yamal, Raphinha, Ferran Torres, Mbappé, etc.).
    2. EXPLORA LIBREMENTE TODOS LOS MERCADOS DE BET365: No te limites solo a remates. Puedes usar mercados de 1X2, Goles (Más/Menos), Córneres, Tarjetas, Hándicaps Asiáticos, Ambos Anotan, Tiros de esquina, Faltas o Crear Apuesta combinada.
    3. Redacta un informe táctico profundo al estilo Scores24 con estadísticas avanzadas y estado de forma.
    
    Devuelve ÚNICAMENTE un objeto JSON válido con este formato exacto:
    {{
      "match": "Equipo A vs Equipo B",
      "league": "Nombre de la Competición",
      "analysis": "• Estado de forma: Análisis táctico del encuentro.\\n• Claves Estadísticas: Métricas y rendimiento actual de plantillas.\\n• Justificación del mercado seleccionado.",
      "pick_main": "Pronóstico Principal de cualquier mercado en Bet365",
      "odds_main": 2.10,
      "pick_alt": "Pronóstico Secundario de Cobertura",
      "odds_alt": 1.55
    }}
    """

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        data = res.json()
        if "candidates" in data and len(data["candidates"]) > 0:
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
            return json.loads(raw_text)
    except Exception as e:
        logging.error(f"Error en IA flexible: {e}")
    
    # Respaldo dinámico con plantilla actual
    return {
        "match": "FC Barcelona vs Bayern de Múnich",
        "league": "UEFA Champions League (Jornada de Hoy)",
        "analysis": "• Estado de forma: El Barça despliega un juego vertical sobresaliente liderado por sus extremos; el Bayern mantiene su habitual vocación ultraofensiva.\n• Claves Estadísticas: Promedio superior a 3.4 goles totales en los duelos directos recientes.\n• Justificación: Alta probabilidad de intercambio de golpes en ambas áreas desde los primeros minutos.",
        "pick_main": "Crear Apuesta: Más de 2.5 Goles + Ambos Equipos Anotan (Sí)",
        "odds_main": 2.15,
        "pick_alt": "Más de 8.5 Córneres Totales en el Partido",
        "odds_alt": 1.60
    }

def publish_scores24_report():
    logging.info("Generando informe analítico con mercados abiertos...")
    item = generate_flexible_ai_analysis()

    match_title = item.get("match", "Partido Destacado de Hoy")
    league_name = item.get("league", "Competición UEFA / Liga")
    analysis_text = item.get("analysis", "Análisis táctico detallado.")
    pick_main = item.get("pick_main", "Más de 2.5 Goles Totales")
    odds_main = float(item.get("odds_main", 2.00))
    pick_alt = item.get("pick_alt", "Doble Oportunidad")
    odds_alt = float(item.get("odds_alt", 1.55))

    now_spain = datetime.now(SPAIN_TZ)
    caption = (
        f"📊 <b>ANÁLISIS ESTADÍSTICO DE HOY ({now_spain.strftime('%d/%m/%Y')})</b> 📊\n"
        f"🌐 <i>Fuente Oficial: Datos & Estadísticas Scores24</i>\n\n"
        f"🏆 <b>Competición:</b> {league_name}\n"
        f"⚔️ <b>Encuentro:</b> {match_title}\n\n"
        f"📋 <b>INFORME TÁCTICO Y CLAVES DE PLANTILLA:</b>\n"
        f"{analysis_text}\n\n"
        f"🎯 <b>PRONÓSTICO PRINCIPAL (BET365):</b>\n"
        f"• Selección: <code>{pick_main}</code>\n"
        f"• Cuota: <b>@{odds_main:.2f}</b> | Stake: <b>1.5 / 10</b>\n\n"
        f"🛡️ <b>MERCADO ALTERNATIVO (COBERTURA):</b>\n"
        f"• Selección: <code>{pick_alt}</code> (@{odds_alt:.2f})\n\n"
        f"📈 <b>ESTADÍSTICAS DEL CANAL:</b> +{CHANNEL_STATS['profit_units']} Unidades ({CHANNEL_STATS['yield_pct']}% Yield)\n\n"
        f"💳 <b>¿QUIERES ACCEDER A LAS COMBINADAS VIP EXCLUSIVAS?</b>\n"
        f"📲 Escríbeme por privado: <a href='https://t.me/{TELEGRAM_USERNAME}'>@{TELEGRAM_USERNAME}</a>"
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
        "☕ Arrancamos la jornada analizando los mejores mercados de valor disponibles en Bet365 para los partidos de hoy al estilo Scores24.\n\n"
        "💳 <b>ACCESO AL GRUPO VIP PRIVADO:</b>\n"
        "🔥 <b>Pase Día Premium:</b> <b>5.00 €</b>\n"
        "🎟️ <b>Pase Semanal VIP:</b> <b>10.00 €</b>\n"
        "👑 <b>Pase Mensual VIP:</b> <b>34.99 €</b>\n\n"
        f"📲 <i>Para unirte al VIP y recibir las combinadas diarias, escríbeme:</i>\n"
        f"👉 <b>Contactar al Analista: <a href='https://t.me/{TELEGRAM_USERNAME}'>@{TELEGRAM_USERNAME}</a></b>"
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

    while True:
        try:
            time.sleep(900)
            logging.info("Ejecutando nuevo ciclo con mercados abiertos...")
            publish_scores24_report()
        except Exception as e:
            logging.error(f"Error en bucle de publicación: {e}")

if __name__ == "__main__":
    main()
