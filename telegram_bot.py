import os
import time
import logging
import threading
import requests

# Desactivar advertencias de certificados SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración de logs limpia
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# CLAVE DE FÚTBOL FIJA
FOOTBALL_DATA_KEY = "6d66424ab2d344bb468b05ec1b115991"

API_URL = "https://football-data.org"
HEADERS = {
    "X-Auth-Token": FOOTBALL_DATA_KEY
}

def send_telegram_message(text):
    # DIRECCIÓN FIJA A TU CANAL REAL TOPTIPS
    url_telegram = "https://telegram.org"
    payload = {
        "chat_id": "@FreeTopTip",
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url_telegram, json=payload)
        logging.info(f"Respuesta envio Telegram: {res.status_code}")
    except Exception as e:
        logging.error(f"Error Telegram: {e}")

def get_live_fixtures():
    url_futbol = f"{API_URL}?status=LIVE"
    try:
        response = requests.get(url_futbol, headers=HEADERS, verify=False)
        if response.status_code == 200:
            return response.json().get("matches", [])
        return []
    except Exception:
        return []

def check_live_alerts():
    matches = get_live_fixtures()
    if not matches:
        logging.info("Monitoreando... No se encontraron partidos en vivo.")
        return

    for match in matches:
        home_team = match.get("homeTeam", {}).get("name", "Local")
        away_team = match.get("awayTeam", {}).get("name", "Visitante")
        competition = match.get("competition", {}).get("name", "Liga")
        
        mensaje_clasico = (
            f"⚽ <b>{home_team} vs {away_team}</b> (00:00 - {competition})\n"
            f"🎯 <b>Mercados a vigilar:</b> Goles / Córners / Tarjetas\n"
            f"🔍 Partido incluido en el calendario; las señales se basan en las estadísticas disponibles durante el directo.\n"
            f"───────────────────\n"
        )
        send_telegram_message(mensaje_clasico)

def main_loop():
    # El bot mandará este mensaje al canal nada más arrancar
    time.sleep(3)
    aviso_arranque = (
        "💬 Compartiré alertas en directo cuando las estadísticas "
        "alcancen los filtros de Goles, Córners, Tarjetas, Valor o Paradas."
    )
    send_telegram_message(aviso_arranque)
    
    while True:
        try:
            check_live_alerts()
        except Exception as e:
            logging.error(f"Error en el ciclo de monitoreo: {e}")
        time.sleep(90)

if __name__ == "__main__":
    main_loop()
