import os
import time
import logging
import threading
import requests
import json
import random
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
TELEGRAM_USERNAME = "Mark122"

SPAIN_TZ = ZoneInfo("Europe/Madrid")

CHANNEL_STATS = {
    "wins": 68,
    "losses": 13,
    "profit_units": +54.2,
    "yield_pct": 26.1
}

# Base de datos de análisis detallados estilo Scores24
SCORES24_MATCHES = [
    {
        "match": "Real Madrid vs Manchester City",
        "league": "UEFA Champions League",
        "analysis": "Análisis profundo de la jornada:\n• El conjunto local muestra un índice ofensivo de 2.1 xG por partido en su feudo.\n• El visitante acumula una media de 64% de posesión y alta presión tras pérdida.\n• Tendencia clara a partidos abiertos con múltiples llegadas por bandas.",
        "pick_main": "Crear Apuesta: Ambos Anotan + Más de 8.5 Córneres",
        "odds_main": 2.20,
        "pick_alt": "Más de 2.5 Goles Totales",
        "odds_alt": 1.62
    },
    {
        "match": "Arsenal vs Bayern München",
        "league": "UEFA Champions League",
        "analysis": "Informe estadístico:\n• Los gunners promedian 2.4 goles a favor como local en competición europea.\n• La defensa visitante concede espacios considerables en transiciones rápidas.\n• Estadística clave: 4 de los últimos 5 enfrentamientos directos superaron la línea de 2.5 tantos.",
        "pick_main": "Victoria Arsenal + Más de 1.5 Goles",
        "odds_main": 2.15,
        "pick_alt": "Arsenal Más de 4.5 Córneres",
        "odds_alt": 1.55
    },
    {
        "match": "FC Barcelona vs Paris Saint-Germain",
        "league": "UEFA Champions League",
        "analysis": "Estudio táctico detallado:\n• Duelo de alto voltaje con ambos equipos jugándose el control de la medular.\n• Promedio combinado de más de 14 remates a puerta por encuentro.\n• Alta tendencia a faltas tácticas en zona de creación.",
        "pick_main": "Crear Apuesta: Ambos Anotan + Más de 3.5 Tarjetas",
        "odds_main": 2.30,
        "pick_alt": "FC Barcelona O Empate",
        "odds_alt": 1.58
    },
    {
        "match": "Atlético de Madrid vs Borussia Dortmund",
        "league": "UEFA Champions League",
        "analysis": "Reporte táctico de rendimiento:\n• El fortín local mantiene una solidez defensiva rigurosa con menos de 0.6 goles encajados en casa.\n• El rival sufre notablemente en desplazamientos largos bajo presión ambiental.\n• Valor matemático elevado en la victoria local.",
        "pick_main": "Victoria Atlético de Madrid + Menos de 4.5 Goles",
        "odds_main": 2.05,
        "pick_alt": "Atlético Empate No Válido",
        "odds_alt": 1.50
    },
    {
        "match": "Liverpool vs Atalanta",
        "league": "UEFA Europa League",
        "analysis": "Análisis de métricas avanzadas:\n• Propuesta hiperofensiva por parte de ambos conjuntos con índices de xG muy elevados.\n• Promedio de 11.8 saques de esquina totales por partido.\n• Margen de efectividad superior del 75% en duelos aéreos ofensivos.",
        "pick_main": "Crear Apuesta: Victoria Liverpool + Más de 2.5 Goles",
        "odds_main": 2.10,
        "pick_alt": "Liverpool Más de 1.5 Goles",
        "odds_alt": 1.48
    }
]

def send_telegram_message(text, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        return None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        res = requests.post(url, json=payload, timeout=10)
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
            res = requests.post(url, data=data, files={"photo": photo}, timeout=12)
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
        
        d.text((40, 48), "🛡️ SCORES24 ESPAÑA - ANALYTICS", fill=(0, 212, 170))
        d.text((580, 48), league_name.upper()[:25], fill=(200, 200, 200))
        
        d.text((40, 140), "PARTIDO ANALIZADO:", fill=(150, 160, 180))
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

def publish_scores24_report():
    item = random.choice(SCORES24_MATCHES)
    
    match_title = item.get("match")
    league_name = item.get("league")
    analysis_text = item.get("analysis")
    pick_main = item.get("pick_main")
    odds_main = item.get("odds_main")
    pick_alt = item.get("pick_alt")
    odds_alt = item.get("odds_alt")

    caption = (
        f"📊 <b>ESTADÍSTICAS Y ANÁLISIS TÁCTICO</b> 📊\n"
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
        f"📲 Escríbeme por privado: <b>@{TELEGRAM_USERNAME}</b>"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "👑 Acceder al Grupo VIP / Contactar", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
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
        "☕ Arrancamos la jornada compartiendo informes estadísticos detallados y análisis de valor al estilo de los mejores portales de datos.\n\n"
        "💳 <b>ACCESO AL GRUPO VIP PRIVADO:</b>\n"
        "🔥 <b>Pase Día Premium:</b> <b>5.00 €</b>\n"
        "🎟️ <b>Pase Semanal VIP:</b> <b>10.00 €</b>\n"
        "👑 <b>Pase Mensual VIP:</b> <b>34.99 €</b>\n\n"
        f"📲 <i>Para unirte al VIP y recibir las combinadas diarias, escríbeme:</i>\n"
        f"👉 <b>Contactar al Analista: @{TELEGRAM_USERNAME}</b>"
    )
    keyboard = {
        "inline_keyboard": [
            [{"text": "👑 Entrar al Grupo VIP", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }
    send_telegram_message(msg, reply_markup=keyboard)

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
    logging.info("Servicio Bot Scores24 Pro en ejecución...")

    # Mensaje inicial de bienvenida al arrancar
    send_daily_sales_message()
    time.sleep(3)

    # Publicación inmediata del primer informe estadístico
    publish_scores24_report()

    # Bucle continuo: Publica un nuevo informe estadístico detallado cada 10 minutos (600 segundos)
    while True:
        try:
            time.sleep(600)
            logging.info("Publicando nuevo informe estadístico en el canal...")
            publish_scores24_report()
        except Exception as e:
            logging.error(f"Error en bucle de publicación: {e}")

if __name__ == "__main__":
    main()
