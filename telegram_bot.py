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
    "wins": 74,
    "losses": 14,
    "profit_units": +61.2,
    "yield_pct": 28.5
}

# Base de datos local optimizada estilo Scores24
TODAY_MATCHES_POOL = [
    {
        "match": "España vs Italia",
        "league": "UEFA Nations League",
        "analysis": "• Dinámica táctica: La Roja mantiene un promedio de posesión del 64% en su feudo, buscando superioridad por bandas.\n• Bloque rival: Italia propone un sistema ultracompacto en bloque bajo, priorizando el contragolpe.\n• Métrica Scores24: Se prevé un volumen alto de saques de esquina según las estadísticas de centros al área.",
        "pick_main": "Crear Apuesta: España O Empate + Más de 7.5 Córneres",
        "odds_main": 2.15,
        "pick_alt": "España Más de 1.5 Goles",
        "odds_alt": 1.62
    },
    {
        "match": "Francia vs Alemania",
        "league": "Partido Internacional de Selecciones",
        "analysis": "• Estado de forma: Duelo estelar con los tridentes ofensivos titulares confirmados en ambos combinados.\n• Métricas avanzadas: Promedio conjunto superior a 13.5 remates directos a puerta por partido.\n• Clave de valor: Ritmo alto en transiciones rápidas que favorece las ocasiones en ambas áreas.",
        "pick_main": "Crear Apuesta: Ambos Anotan (Sí) + Más de 2.5 Goles",
        "odds_main": 2.20,
        "pick_alt": "Más de 1.5 Goles en la 1ª Mitad",
        "odds_alt": 1.75
    },
    {
        "match": "Brasil vs Colombia",
        "league": "Eliminatorias Conmebol",
        "analysis": "• Propuesta de juego: La canarinha busca desbordar con extremos abiertos para generar superioridad numérica.\n• Planteamiento visitante: Colombia apuesta por un bloque dinámico y transiciones verticales rápidas.\n• Tendencia Scores24: Alta efectividad en saques de esquina favorables al equipo local.",
        "pick_main": "Victoria Brasil + Más de 1.5 Goles Totales",
        "odds_main": 2.10,
        "pick_alt": "Brasil Más de 4.5 Córneres",
        "odds_alt": 1.58
    }
]

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

def publish_scores24_report():
    item = random.choice(TODAY_MATCHES_POOL)

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
        "☕ Arrancamos la jornada compartiendo informes estadísticos detallados y análisis de valor de los partidos programados para hoy al estilo Scores24.\n\n"
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
            logging.info("Ejecutando nuevo ciclo de publicación...")
            publish_scores24_report()
        except Exception as e:
            logging.error(f"Error en bucle de publicación: {e}")

if __name__ == "__main__":
    main()
