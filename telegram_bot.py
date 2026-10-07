import os
import time
import logging
import threading
import requests

# Desactivar advertencias de certificados SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Canal de Telegram extraído de tu Render
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# METEMOS TU SEGUNDA CLAVE DIRECTAMENTE PARA SALTAR EL BLOQUEO
FOOTBALL_DATA_KEY = "6d66424ab2d344bb468b05ec1b115991"

API_URL = "https://football-data.org"
HEADERS = {
    "X-Auth-Token": FOOTBALL_DATA_KEY
}

def send_telegram_message(text):
    if not CHAT_ID:
        return
    url_telegram = "https://telegram.org"
    payload = {
        "chat_id": str(CHAT_ID).strip(),
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url_telegram, json=payload)
        logging.info(f"Respuesta envío Telegram: {res.status_code}")
    except Exception as e:
        logging.error(f"Error Telegram: {e}")

def get_live_fixtures():
    url_futbol = f"{API_URL}?status=LIVE"
    try:
        response = requests.get(url_futbol, headers=HEADERS, verify=False)
        if response.status_code == 200:
            return response.json().get("matches", [])
        else:
            logging.error(f"La API de fútbol rechazó la contraseña. Código: {response.status_code}")
            return []
    except Exception as e:
        logging.error(f"Error de red con la API: {e}")
        return []

def check_live_alerts():
    matches = get_live_fixtures()
    if not matches:
        logging.info("No se encontraron partidos en vivo con esta clave.")
        return

    for match in matches:
        home_team = match.get("homeTeam", {}).get("name", "Local")
        away_team = match.get("awayTeam", {}).get("name", "Visitante")
        score = match.get("score", {}).get("fullTime", {})
        home_goals = score.get("home", 0)
        away_goals = score.get("away", 0)
        competition = match.get("competition", {}).get("name", "Liga")
        
        mensaje_partido = (
            f"⚽ <b>ALERTA EN DIRECTO</b> ⚽\n\n"
            f"🏆 Competencia: {competition}\n"
            f"⚔️ {home_team} vs {away_team}\n"
            f"📊 Marcador actual: {home_goals} - {away_goals}\n"
        )
        send_telegram_message(mensaje_partido)

def main_loop():
    time.sleep(2)
    send_telegram_message("🤖 Bot actualizado y activo monitoreando partidos sin límite.")
    
    while True:
        try:
            check_live_alerts()
        except Exception as e:
            logging.error(f"Error en el ciclo de monitoreo: {e}")
        time.sleep(90)

if __name__ == "__main__":
    # Arrancamos el bucle directamente sin servidor HTTP para evitar colapsos
    main_loop()
