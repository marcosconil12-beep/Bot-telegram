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
    "wins": 65,
    "losses": 14,
    "profit_units": +51.8,
    "yield_pct": 24.5
}

# Base de datos dinámica local de partidos y análisis estilo Scores24
MATCHES_DATABASE = [
    {
        "match": "Real Madrid vs Manchester City",
        "league": "UEFA Champions League",
        "pick_main": "Crear Apuesta: Ambos Anotan + Más de 8.5 Córneres",
        "odds_main": 2.20,
        "pick_alt": "Más de 2.5 Goles Totales",
        "odds_alt": 1.62,
        "news": "Alineaciones confirmadas. Titulares habituales sobre el césped con presión alta desde el inicio.",
        "stats": "Promedio acumulado de 3.4 xG y 10.8 córneres por partido en los últimos encuentros europeos.",
        "value_reason": "El ritmo de transiciones ofensivas y la velocidad por bandas garantizan múltiples ocasiones claras."
    },
    {
        "match": "Arsenal vs Bayern München",
        "league": "UEFA Champions League",
        "pick_main": "Victoria Arsenal + Más de 1.5 Goles",
        "odds_main": 2.15,
        "pick_alt": "Arsenal Más de 4.5 Córneres",
        "odds_alt": 1.55,
        "news": "El conjunto local llega tras una racha imbatible en casa con solidez en el bloque central.",
        "stats": "68% de posesión de media en su feudo y solo 0.7 goles encajados por encuentro.",
        "value_reason": "Dominio territorial claro y debilidad defensiva del rival en repliegues rápidos."
    },
    {
        "match": "FC Barcelona vs Paris Saint-Germain",
        "league": "UEFA Champions League",
        "pick_main": "Crear Apuesta: Ambos Anotan + Más de 3.5 Tarjetas",
        "odds_main": 2.30,
        "pick_alt": "FC Barcelona O Empate (Doble Oportunidad)",
        "odds_alt": 1.58,
        "news": "Duelo de máxima tensión tactica con noticias de rotaciones de última hora en la medular.",
        "stats": "Promedio de 5.6 tarjetas y más de 14 remates a puerta acumulados por jornada.",
        "value_reason": "Cuota con valor matemático elevado dada la intensidad del choque en zonas de finalización."
    },
    {
        "match": "Atlético de Madrid vs Borussia Dortmund",
        "league": "UEFA Champions League",
        "pick_main": "Victoria Atlético de Madrid + Menos de 4.5 Goles",
        "odds_main": 2.05,
        "pick_alt": "Atlético de Madrid Empate No Válido",
        "odds_alt": 1.50,
        "news": "El feudo rojiblanco se presenta asfixiante con planteamiento táctico de repliegue y contra.",
        "stats": "El rival concede un 40% de sus ocasiones a balón parado. Fortín local comprobado.",
        "value_reason": "La solidez defensiva unida a la efectividad en área rival justifica la ventaja en la cuota."
    },
    {
        "match": "Liverpool vs Atalanta",
        "league": "UEFA Europa League",
        "pick_main": "Crear Apuesta: Victoria Liverpool + Más de 2.5 Goles + Más de 7.5 Córneres",
        "odds_main": 2.10,
        "pick_alt": "Liverpool Más de 1.5 Goles Individuales",
        "odds_alt": 1.48,
        "news": "Ritmo frenético esperado en el feudo local con tridente ofensivo confirmado.",
        "stats": "Promedio de 12.2 saques de esquina totales e índice de xG superior a 2.8 por partido.",
        "value_reason": "La propuesta ofensiva de ambos conjuntos asegura un partido de ida y vuelta constante."
    }
]

def send_telegram_message(text, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("Falta TELEGRAM_BOT_TOKEN o CHAT_ID.")
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

def publish_next_content():
    item = random.choice(MATCHES_DATABASE)
    
    match_title = item.get("match")
    league_name = item.get("league")
    pick_main = item.get("pick_main")
    odds_main = item.get("odds_main")
    pick_alt = item.get("pick_alt")
    odds_alt = item.get("odds_alt")
    
    news_text = item.get("news")
    stats_text = item.get("stats")
    value_text = item.get("value_reason")

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
        f"🛡️ <b>OPCIÓN SECUNDARIA (COBERTURA):</b>\n"
        f"• Selección: <code>{pick_alt}</code> (@{odds_alt:.2f})\n\n"
        f"💡 <b>JUSTIFICACIÓN DE VALOR:</b>\n"
        f"💬 {value_text}\n\n"
        f"📈 <b>BALANCE ACUMULADO:</b> +{CHANNEL_STATS['profit_units']} Unidades\n\n"
        f"💳 <b>¿QUIERES RECIBIR LA COMBINADA VIP DE HOY?</b>\n"
        f"📲 Contacta por privado: <b>@{TELEGRAM_USERNAME}</b>"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "👑 Comprar Pase VIP / Contactar al Analista", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
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
            [{"text": "👑 Entrar al Grupo VIP", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }
    send_telegram_message(msg, reply_markup=keyboard)

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
    logging.info("Servicio Tipster en ejecución...")

    # Mensaje inicial de ventas
    send_daily_sales_message()
    time.sleep(3)

    # Publicación inmediata del primer análisis con imagen
    publish_next_content()

    # Bucle continuo: Publica un nuevo análisis cada 2 minutos (120 segundos)
    while True:
        try:
            time.sleep(120)
            logging.info("Publicando nuevo contenido en el canal...")
            publish_next_content()
        except Exception as e:
            logging.error(f"Error en bucle de publicación: {e}")

if __name__ == "__main__":
    main()
