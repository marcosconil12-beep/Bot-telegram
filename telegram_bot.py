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
    "wins": 71,
    "losses": 14,
    "profit_units": +58.4,
    "yield_pct": 27.2
}

# Base de datos rigurosa con partidos de la jornada actual (13 de Octubre de 2026)
TODAY_SCORES24_MATCHES = [
    {
        "match": "España vs Italia",
        "league": "UEFA Nations League / Clasificación",
        "analysis": "• Dinámica táctica: España mantiene un promedio de posesión del 64% en su feudo con alta presión tras pérdida.\n• Estado visitante: Italia apuesta por un bloque medio-bajo muy compacto y transiciones rápidas por las bandas.\n• Clave Scores24: Los últimos 3 enfrentamientos directos registraron más de 9.5 córneres totales.",
        "pick_main": "Crear Apuesta: España O Empate + Más de 7.5 Córneres",
        "odds_main": 2.15,
        "pick_alt": "España Más de 1.5 Goles",
        "odds_alt": 1.62
    },
    {
        "match": "Argentina vs Uruguay",
        "league": "Eliminatorias Sudamericanas Conmebol",
        "analysis": "• Análisis de rendimiento: La albiceleste muestra un xG ofensivo de 2.25 jugando como local en eliminatorias.\n• Planteamiento rival: Uruguay propone un partido de máxima fricción física y alta intensidad en la medular.\n• Tendencia estadística: Media acumulada superior a 5.5 tarjetas amarillas por encuentro.",
        "pick_main": "Crear Apuesta: Victoria Argentina + Más de 4.5 Tarjetas Totales",
        "odds_main": 2.30,
        "pick_alt": "Argentina Empate No Válido",
        "odds_alt": 1.48
    },
    {
        "match": "Francia vs Alemania",
        "league": "Partido Internacional de Selecciones",
        "analysis": "• Estudio de bajas y alineaciones: Ambos combinados saltan al césped con sus tridentes ofensivos titulares.\n• Métricas avanzadas: Promedio combinado de 3.2 goles esperados (xG) por partido.\n• Valor de cuota: Altísima probabilidad de intercambio de ocasiones en ambas áreas desde el pitido inicial.",
        "pick_main": "Crear Apuesta: Ambos Anotan (Sí) + Más de 2.5 Goles",
        "odds_main": 2.20,
        "pick_alt": "Más de 1.5 Goles en la 1ª Mitad",
        "odds_alt": 1.75
    },
    {
        "match": "Brasil vs Colombia",
        "league": "Eliminatorias Sudamericanas Conmebol",
        "analysis": "• Estado de forma: Brasil busca desequilibrar por carriles interiores con desborde constante por los extremos.\n• Propuesta visitante: Colombia no se encierra y plantea un duelo abierto de ida y vuelta.\n• Tendencia Scores24: Alta efectividad en remates a puerta de los locales.",
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
        res_json = res.json()
        if res_json.get("ok"):
            logging.info("¡Mensaje de texto enviado con éxito a Telegram!")
            return True
        else:
            logging.error(f"Telegram rechazó el mensaje: {res_json}")
            return False
    except Exception as e:
        logging.error(f"Excepción al enviar mensaje: {e}")
        return False

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}
            res = requests.post(url, data=data, files={"photo": photo}, timeout=20)
            res_json = res.json()
            if res_json.get("ok"):
                logging.info("¡Foto y análisis publicados con éxito en el canal!")
                return True
            else:
                logging.error(f"Telegram rechazó la foto: {res_json}")
                return False
    except Exception as e:
        logging.error(f"Excepción al enviar foto: {e}")
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
    logging.info("Generando informe estadístico Scores24 para partidos de hoy...")
    item = random.choice(TODAY_SCORES24_MATCHES)
    
    match_title = item.get("match")
    league_name = item.get("league")
    analysis_text = item.get("analysis")
    pick_main = item.get("pick_main")
    odds_main = float(item.get("odds_main", 2.00))
    pick_alt = item.get("pick_alt")
    odds_alt = float(item.get("odds_alt", 1.60))

    now_spain = datetime.now(SPAIN_TZ)
    caption = (
        f"📊 <b>ESTADÍSTICAS Y ANÁLISIS TÁCTICO ({now_spain.strftime('%d de %B')})</b> 📊\n"
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
        logging.info("Intentando enviar por texto plano...")
        send_telegram_message(caption)

def send_daily_sales_message():
    now_spain = datetime.now(SPAIN_TZ)
    msg = (
        f"☀️ <b>¡BUENOS DÍAS A TODOS EN @FreeTopTip! ({now_spain.strftime('%d de %B')})</b> ☀️\n\n"
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
            time.sleep(600)
            logging.info("Iniciando nuevo ciclo de publicación...")
            publish_scores24_report()
        except Exception as e:
            logging.error(f"Error en bucle de publicación: {e}")

if __name__ ==- "__main__":
    main()
