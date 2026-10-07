import os
import time
import logging
import requests

# Configuración de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")  # O el ID de tu canal/grupo

API_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": API_FOOTBALL_KEY
}

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("TELEGRAM_BOT_TOKEN o CHAT_ID no configurados.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, json=payload)
        res.raise_for_status()
    except Exception as e:
        logging.error(f"Error enviando mensaje a Telegram: {e}")

def get_live_fixtures():
    url = f"{API_URL}/fixtures?live=all"
    try:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        return data.get("response", [])
    except Exception as e:
        logging.error(f"Error consultando API-Football: {e}")
        return []

def check_live_alerts():
    fixtures = get_live_fixtures()
    for fix in fixtures:
        fixture_id = fix["fixture"]["id"]
        elapsed = fix["fixture"]["status"]["elapsed"] or 0
        teams = fix["teams"]
        goals = fix["goals"]
        
        # Extraer estadísticas del partido si están disponibles
        stats = fix.get("statistics", [])
        if not stats or len(stats) < 2:
            continue

        # Formatear datos principales
        home_team = teams["home"]["name"]
        away_team = teams["away"]["name"]
        home_goals = goals["home"] or 0
        away_goals = goals["away"] or 0

        # Alerta personalizada predeterminada
        # Ajusta las condiciones según tus reglas personales
        if 30 <= elapsed <= 75 and (home_goals + away_goals) <= 1:
            msg = (
                f"🚨 <b>ALERTA EN DIRECTO</b> 🚨\n\n"
                f"⚽ <b>{home_team} vs {away_team}</b>\n"
                f"⏱ Minuto: {elapsed}' | Resultado: {home_goals} - {away_goals}\n\n"
                f"🔥 ¡Oportunidad detectada según la presión del partido!\n"
                f"👉 Revisa las líneas de córners/goles en tu casa de apuestas favorita."
            )
            send_telegram_message(msg)

def main():
    logging.info("Bot con redacción personal iniciado...")
    send_telegram_message("🤖 Bot iniciado correctamente y activo para monitorear partidos.")
    
    while True:
        try:
            check_live_alerts()
        except Exception as e:
            logging.error(f"Error en el bucle principal: {e}")
        
        # Espera 3 minutos entre revisiones
        time.sleep(180)

if __name__ == "__main__":
    main()
