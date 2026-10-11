import os
import time
import logging
import threading
import requests
import random
from datetime import datetime
from PIL import Image, ImageDraw
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuración de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TELEGRAM_USERNAME = "Mark122" # Tu usuario para ventas VIP

# Balance del Canal
CHANNEL_STATS = {
    "wins": 62,
    "losses": 13,
    "profit_units": +48.2
}

def send_telegram_message(text, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        return None
    token = str(TELEGRAM_BOT_TOKEN).strip().replace('"', '').replace("'", "")
    chat = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    import json
    payload = {"chat_id": chat, "text": text, "parse_mode": "HTML"}
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
    token = str(TELEGRAM_BOT_TOKEN).strip().replace('"', '').replace("'", "")
    chat = str(CHAT_ID).strip().replace('"', '').replace("'", "")
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        import json
        with open(photo_path, 'rb') as photo:
            data = {"chat_id": chat, "caption": caption, "parse_mode": "HTML"}
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
        d.text((70, 260), "SELECCIÓN RECOMENDADA:", fill=(255, 215, 0))
        d.text((70, 315), f"{pick_text[:45]}...", fill=(255, 255, 255))
        d.text((750, 315), f"@{odds_val:.2f}", fill=(0, 212, 170))

        d.text((40, 460), f"📊 Métricas: Rendimiento Táctico | Yield: +{CHANNEL_STATS['profit_units']}U", fill=(150, 160, 180))
        d.text((40, 510), f"Canal Oficial: TOPTIPS | Suscripción VIP: @{TELEGRAM_USERNAME}", fill=(255, 215, 0))
        
        filename = "scores24_card.png"
        img.save(filename)
        return filename
    except Exception as e:
        logging.error(f"Error tarjeta: {e}")
        return None

# --- PUBLICACIONES RFEF ESPAÑA ---
RFEF_MATCHES = [
    ("Ourense CF vs Zamora CF", "Primera RFEF - Gr. 1", "Victoria Zamora CF (Hándicap 0)", 2.05, "El Zamora se muestra impecable tácticamente como visitante en transiciones rápidas y Ourense deja muchas dudas en salida de balón."),
    ("UD Logroñés vsCD Numancia", "Segunda RFEF - Gr. 2", "Más de 2.0 Goles Totales", 1.85, "Duelo directo en la parte alta. Ambos promedian un volumen de tiro alto y defensas concediendo ocasiones a balón parado."),
    ("SE Penya Independent vs CE Andratx", "Segunda RFEF - Gr. 3", "Victoria Penya Independent", 2.10, "El factor campo balear y el ritmo físico de Penya Independent marcarán la diferencia en los segundos 45 minutos."),
    ("Tenerife B vs CD Paso", "Segunda RFEF - Gr. 5", "Más de 8.5 Córneres", 1.90, "Partido dinámico de juego por bandas. El filial chicharrero genera una media de 6.5 saques de esquina en su feudo."),
    ("Real Jaén vs UD Maracena", "Tercera RFEF - Gr. 9", "Victoria Real Jaén -1.0 HC", 1.95, "El Jaén impone una presión asfixiante en La Victoria frente a un rival que sufre encajando temprano fuera de casa."),
    ("CD Tropezón vs UM Escobedo", "Tercera RFEF - Gr. 3", "Ambos Anotan (Sí)", 2.00, "Choque cántabro con plantillas muy parejas y pólvora arriba. La efectividad en las áreas asegura presencia de goles."),
    ("Utebo FC vs SD Ejea", "Segunda RFEF - Gr. 2", "Doble Oportunidad Utebo/Empate + Más de 1.5 Goles", 1.80, "Utebo se mantiene invicto en casa con un bloque defensivo ordenado y salidas incisivas a la contra."),
    ("Salamanca UDS vs Bergantiños CF", "Segunda RFEF - Gr. 1", "Más de 4.5 Tarjetas", 1.85, "Partido tenso en el Helmántico con duelo directo en el centro del campo y un colegiado de promedio alto en amonestaciones."),
    ("Xerez CD vs Antoniano", "Segunda RFEF - Gr. 4", "Victoria Xerez CD", 2.05, "El empuje de Chapín y la necesidad de puntos del Xerez harán valer la superioridad técnica del conjunto local."),
    ("CD Toledo vs CD Marchamalo", "Tercera RFEF - Gr. 18", "Más de 2.5 Goles Totales", 2.15, "El Toledo genera múltiples ocasiones claras en el Salto del Caballo y el Marchamalo destaca por partidos abiertos.")
]

# --- PUBLICACIONES GENERALES Y INTERNACIONALES ---
GLOBAL_MATCHES = [
    ("Real Madrid vs Barcelona", "La Liga EA Sports", "Victoria Real Madrid + Más de 1.5 Goles", 2.35, "Análisis de máxima exigencia: la profundidad de banquillo y la pegada del Madrid en las áreas inclinarán la balanza en el tramo final."),
    ("Arsenal vs Chelsea", "Premier League", "Más de 9.5 Córneres Totales", 1.90, "Propuestas ofensivas de juego exterior constante por bandas que garantizan un goteo continuo de saques de esquina."),
    ("Bayern Múnich vs Borussia Dortmund", "Bundesliga", "Ambos Anotan + Más de 2.5 Goles", 1.85, "Derby alemán caracterizado por defensas adelantadas e intercambios de golpes constantes a alta velocidad."),
    ("Inter de Milán vs Juventus", "Serie A", "Más de 4.5 Tarjetas Totales", 1.95, "Duelo de máxima rivalidad táctica con alta densidad de faltas tácticas en la medular y exigencia arbitral.")
]

def publish_single_pick(match_info):
    home_away, league, pick, odds, analysis = match_info
    
    caption = (
        f"⚽ <b>ANÁLISIS PROFESIONAL DETALLADO - TOPTIPS</b> ⚽\n\n"
        f"🏆 <b>Competición:</b> {league}\n"
        f"⚔️ <b>Encuentro:</b> {home_away}\n\n"
        f"🎯 <b>SELECCIÓN RECOMENDADA:</b>\n"
        f"• Pronóstico: <code>{pick}</code>\n"
        f"• Cuota Real (Bet365): <b>{odds:.2f}</b>\n"
        f"• Stake Sugerido: <b>1.5 / 10</b>\n\n"
        f"🔎 <b>MI ANÁLISIS DEL PARTIDO:</b>\n"
        f"💬 {analysis}\n\n"
        f"📊 <b>BALANCES:</b> +{CHANNEL_STATS['profit_units']} U. Neto\n"
        f"📲 <b>Suscripciones VIP:</b> @{TELEGRAM_USERNAME}"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "👑 Contactar al Analista VIP", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }

    img_path = create_scores24_card(home_away, league, pick, odds)
    sent = False
    if img_path:
        sent = send_telegram_photo(img_path, caption, reply_markup=keyboard)
    if not sent:
        send_telegram_message(caption, reply_markup=keyboard)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Vendedor Pro TOPTIPS Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error HTTP: {e}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Tipster Pro en ejecución...")

    last_execution = ""

    while True:
        try:
            now = datetime.now()
            weekday = now.weekday() # 0: Lunes, 4: Viernes, 5: Sábado, 6: Domingo
            hour = now.hour
            minute = now.minute
            time_key = f"{now.strftime('%Y-%m-%d')}_{hour}_{minute}"

            # --- DOMINGO (6) ---
            if weekday == 6:
                # 08:00 - Buenos Días Domingo
                if hour == 8 and minute == 0 and last_execution != f"{time_key}_sun_0800":
                    msg = (
                        "☀️ <b>¡BUENOS DÍAS Y FELIZ DOMINGO DE FÚTBOL!</b> ☀️\n\n"
                        "☕ Arrancamos el día más importante de la semana con la mejor información del mercado.\n\n"
                        "💳 <b>TARIFAS PREMIUM PARA LA JORNADA DEL DOMINGO:</b>\n"
                        "🔥 <b>Pase Día Premium Domingo:</b> <b>5.00 €</b> (Acceso total a la jornada de hoy)\n"
                        "🎟️ <b>Pase Semanal VIP:</b> <b>10.00 €</b>\n"
                        "👑 <b>Pase Mensual VIP:</b> <b>34.99 €</b>\n\n"
                        f"📲 Escríbeme directamente para entrar al grupo VIP: <b>@{TELEGRAM_USERNAME}</b>"
                    )
                    send_telegram_message(msg)
                    last_execution = f"{time_key}_sun_0800"

                # 08:30 - Pack 10 RFEF
                elif hour == 8 and minute == 30 and last_execution != f"{time_key}_sun_0830":
                    for match in RFEF_MATCHES[:10]:
                        publish_single_pick(match)
                        time.sleep(2)
                    last_execution = f"{time_key}_sun_0830"

                # 12:00 - Pack 3 Matinales
                elif hour == 12 and minute == 0 and last_execution != f"{time_key}_sun_1200":
                    for match in GLOBAL_MATCHES[:3]:
                        publish_single_pick(match)
                        time.sleep(2)
                    last_execution = f"{time_key}_sun_1200"

                # 14:30 - Pack 10 Tarde
                elif hour == 14 and minute == 30 and last_execution != f"{time_key}_sun_1430":
                    for match in (GLOBAL_MATCHES + RFEF_MATCHES)[:10]:
                        publish_single_pick(match)
                        time.sleep(2)
                    last_execution = f"{time_key}_sun_1430"

            # --- VIERNES (4) ---
            elif weekday == 4:
                # 08:00 - Buenos Días Viernes
                if hour == 8 and minute == 0 and last_execution != f"{time_key}_fri_0800":
                    msg = (
                        "☀️ <b>¡BUENOS DÍAS! LLEGA EL FIN DE SEMANA</b> ☀️\n\n"
                        "💳 <b>TARIFAS ESPECIALES FIN DE SEMANA:</b>\n"
                        "⚡ <b>Día Premium Viernes:</b> <b>5.00 €</b>\n"
                        "🔥 <b>Jornada Completa (Viernes a Domingo):</b> <b>9.99 €</b>\n"
                        "👑 <b>Pase Mensual VIP:</b> <b>34.99 €</b>\n\n"
                        f"📲 Contáctame para unirte ahora: <b>@{TELEGRAM_USERNAME}</b>"
                    )
                    send_telegram_message(msg)
                    last_execution = f"{time_key}_fri_0800"

                # 12:00 - 2 Picks Viernes
                elif hour == 12 and minute == 0 and last_execution != f"{time_key}_fri_1200":
                    for match in GLOBAL_MATCHES[:2]:
                        publish_single_pick(match)
                        time.sleep(2)
                    last_execution = f"{time_key}_fri_1200"

            # --- SÁBADO (5) ---
            elif weekday == 5:
                # 08:00 - Buenos Días Sábado
                if hour == 8 and minute == 0 and last_execution != f"{time_key}_sat_0800":
                    msg = (
                        "☀️ <b>¡BUENOS DÍAS! JORNADA FUERTE DE SÁBADO</b> ☀️\n\n"
                        "💳 <b>TARIFAS GRUPO VIP SÁBADO:</b>\n"
                        "🔥 <b>Pase Día Premium Sábado:</b> <b>10.00 €</b>\n"
                        "🎟️ <b>Pase Semanal VIP:</b> <b>10.00 €</b>\n"
                        "👑 <b>Pase Mensual VIP:</b> <b>34.99 €</b>\n\n"
                        f"📲 Escríbeme para unirte al VIP: <b>@{TELEGRAM_USERNAME}</b>"
                    )
                    send_telegram_message(msg)
                    last_execution = f"{time_key}_sat_0800"

                # 11:00 - 3 Picks Sábado
                elif hour == 11 and minute == 0 and last_execution != f"{time_key}_sat_1100":
                    for match in GLOBAL_MATCHES[:3]:
                        publish_single_pick(match)
                        time.sleep(2)
                    last_execution = f"{time_key}_sat_1100"

            # --- LUNES A JUEVES (0, 1, 2, 3) ---
            else:
                # 08:00 - Buenos Días Diario
                if hour == 8 and minute == 0 and last_execution != f"{time_key}_weekday_0800":
                    msg = (
                        "☀️ <b>¡BUENOS DÍAS A TODOS!</b> ☀️\n\n"
                        "☕ Arrancamos la jornada analizando las mejores oportunidades del día.\n\n"
                        "💳 <b>TARIFAS GRUPO VIP:</b>\n"
                        "🎟️ <b>Pase Semanal VIP:</b> <b>10.00 €</b>\n"
                        "👑 <b>Pase Mensual VIP:</b> <b>34.99 €</b>\n\n"
                        f"📲 Escríbeme para unirte: <b>@{TELEGRAM_USERNAME}</b>"
                    )
                    send_telegram_message(msg)
                    last_execution = f"{time_key}_weekday_0800"

                # 12:00 - 3 Picks Diarios
                elif hour == 12 and minute == 0 and last_execution != f"{time_key}_weekday_1200":
                    for match in GLOBAL_MATCHES[:3]:
                        publish_single_pick(match)
                        time.sleep(2)
                    last_execution = f"{time_key}_weekday_1200"

        except Exception as e:
            logging.error(f"Error en bucle principal: {e}")

        time.sleep(30) # Comprobación de horario cada 30 segundos

if __name__ == "__main__":
    main()
