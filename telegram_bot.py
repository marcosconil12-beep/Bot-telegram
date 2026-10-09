import os
import time
import logging
import threading
import requests
import random
import csv
from datetime import datetime
from PIL import Image, ImageDraw
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuración de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

sent_alerts = set()
scheduled_tasks = set()
CSV_FILE = "registro_pronosticos.csv"

def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Fecha", "Tipo", "Detalle", "Cuota", "Resultado", "Unidades"])

init_csv()

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("Falta TELEGRAM_BOT_TOKEN o CHAT_ID")
        return None
    
    chat_id_clean = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    token_clean = str(TELEGRAM_BOT_TOKEN).strip().replace('"', '').replace("'", "")
    
    url = f"https://api.telegram.org/bot{token_clean}/sendMessage"
    payload = {"chat_id": chat_id_clean, "text": text, "parse_mode": "HTML"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        logging.info(f"Respuesta Telegram: {res.status_code} - {res.text}")
        return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error al enviar mensaje: {e}")
        return None

def send_telegram_photo(photo_path, caption):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        return None
    
    chat_id_clean = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    token_clean = str(TELEGRAM_BOT_TOKEN).strip().replace('"', '').replace("'", "")
    
    url = f"https://api.telegram.org/bot{token_clean}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            res = requests.post(url, data={"chat_id": chat_id_clean, "caption": caption, "parse_mode": "HTML"}, files={"photo": photo}, timeout=15)
            return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error al enviar foto: {e}")
        return None

def create_premium_image(match_text, league_text):
    img = Image.new('RGB', (800, 450), color=(15, 23, 42))
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, 780, 430], outline=(234, 179, 8), width=4)
    d.text((40, 50), "PICK PREMIUM STAKE 5 EXCLUSIVO", fill=(234, 179, 8))
    d.text((40, 120), f"Competicion: {league_text}", fill=(255, 255, 255))
    d.text((40, 180), f"Encuentro: {match_text}", fill=(255, 255, 255))
    d.text((40, 250), "Pronostico: CONFIDENCIAL / MAXIMO VALOR", fill=(34, 197, 94))
    d.text((40, 320), "Precio: 9.99 EUR", fill=(234, 179, 8))
    d.text((40, 370), "Adquierelo contactando a: @Mark122", fill=(148, 163, 184))
    filename = "premium_pick.png"
    img.save(filename)
    return filename

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot TOPTIPS Multi-Mercado & Combinadas Active".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()

def publish_daily_routine():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    
    # FORZADO DE PRUEBA INMEDIATA
    if f"test_force_{today_str}" not in scheduled_tasks:
        res = send_telegram_message("⚡ <b>¡SISTEMA TOPTIPS CONECTADO Y FUNCIONANDO!</b> ⚡\n\nSi ves este mensaje, la conexión entre Railway y tu canal de Telegram ha quedado 100% restablecida.")
        if res:
            scheduled_tasks.add(f"test_force_{today_str}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Bot TOPTIPS Definitivo Activo...")
    
    while True:
        try:
            publish_daily_routine()
        except Exception as e:
            logging.error(f"Error en main loop: {e}")
        time.sleep(10)

if __name__ == "__main__":
    main()
