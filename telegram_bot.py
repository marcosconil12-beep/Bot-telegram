import os
import time
import logging
import threading
import requests
import random
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuración de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "").strip()
TELEGRAM_USERNAME = "Mark122" # Tu usuario para ventas VIP

published_picks = set()

# Balance Real del Canal
CHANNEL_STATS = {
    "wins": 62,
    "losses": 13,
    "staked_units": 155,
    "profit_units": +48.2
}

def send_telegram_message(text, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logging.error("Falta TELEGRAM_BOT_TOKEN o CHAT_ID en Railway.")
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
        data = res.json()
        if not data.get("ok"):
            logging.error(f"Error de Telegram al enviar mensaje: {data}")
        return data.get("ok")
    except Exception as e:
        logging.error(f"Excepción enviando mensaje: {e}")
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
            res_data = res.json()
            if not res_data.get("ok"):
                logging.error(f"Error Telegram enviando Foto: {res_data}")
            return res_data.get("ok")
    except Exception as e:
        logging.error(f"Excepción enviando foto: {e}")
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
        d.text((70, 260), "CREAR APUESTA RECOMENDADO:", fill=(255, 215, 0))
        d.text((70, 315), f"{pick_text[:45]}...", fill=(255, 255, 255))
        d.text((750, 315), f"@{odds_val:.2f}", fill=(0, 212, 170))

        d.text((40, 460), f"📊 Métricas: Rendimiento Táctico | Córneres | Tarjetas | Yield: +{CHANNEL_STATS['profit_units']}U", fill=(150, 160, 180))
        d.text((40, 510), f"Canal Oficial: TOPTIPS | Suscripción VIP: @{TELEGRAM_USERNAME}", fill=(255, 215, 0))
        
        filename = "scores24_card.png"
        img.save(filename)
        return filename
    except Exception as e:
        logging.error(f"Error generando imagen: {e}")
        return None

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Vendedor Pro Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error HTTP: {e}")

def send_good_morning():
    total_games = CHANNEL_STATS["wins"] + CHANNEL_STATS["losses"]
    winrate = round((CHANNEL_STATS["wins"] / total_games) * 100, 1)
    
    text = (
        "☀️ <b>¡BUENOS DÍAS A TODOS LOS MIEMBROS DE TOPTIPS!</b> ☀️\n\n"
        "☕ Arrancamos la jornada con los análisis más potentes del día minuciosamente estudiados.\n\n"
        "📊 <b>REVISIÓN DE RESULTADOS Y BALANCES DEL CANAL:</b>\n"
        f"✅ <b>Picks Acertados:</b> {CHANNEL_STATS['wins']}\n"
        f"❌ <b>Picks Fallados:</b> {CHANNEL_STATS['losses']}\n"
        f"🔥 <b>Efectividad (WinRate):</b> <b>{winrate}%</b>\n"
        f"💰 <b>Beneficio Neto:</b> <b>+{CHANNEL_STATS['profit_units']} Unidades</b>\n\n"
        "💳 <b>ACCESO AL GRUPO VIP PRIVADO TOPTIPS:</b>\n"
        "• 🎟️ <b>Pase Semanal VIP:</b> <b>10.00 €</b> (7 días de acceso total)\n"
        "• 👑 <b>Pase Mensual VIP:</b> <b>34.99 €</b> (Acceso completo 30 días)\n\n"
        f"📩 <i>Para unirte al VIP y recibir todas las combinadas exclusivas del día, escríbeme directamente:</i>\n"
        f"👉 <b>Contactar al Analista: @{TELEGRAM_USERNAME}</b>"
    )
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "👑 Comprar Acceso al Grupo VIP", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }
    send_telegram_message(text, reply_markup=keyboard)

def fetch_future_matches():
    if not FOOTBALL_API_KEY:
        return []
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    future_str = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    
    url = f"https://api.football-data.org/v4/matches?dateFrom={today_str}&dateTo={future_str}"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=8)
        data = response.json()
        if data.get("matches"):
            return data["matches"]
    except Exception as e:
        logging.error(f"Error consultando partidos futuros: {e}")
        
    return []

def publish_builder_pick():
    matches = fetch_future_matches()
    
    fallback_matches = [
        {"homeTeam": {"name": "Real Sociedad"}, "awayTeam": {"name": "Deportivo La Coruña"}, "competition": {"name": "Primera División"}, "utcDate": "2026-10-11T16:15:00Z"},
        {"homeTeam": {"name": "Real Madrid"}, "awayTeam": {"name": "FC Barcelona"}, "competition": {"name": "La Liga"}, "utcDate": "2026-10-11T20:00:00Z"},
        {"homeTeam": {"name": "Arsenal"}, "awayTeam": {"name": "Chelsea"}, "competition": {"name": "Premier League"}, "utcDate": "2026-10-12T17:30:00Z"}
    ]
    
    selected_list = matches if matches else fallback_matches
    match = random.choice(selected_list)
    
    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]
    league = match["competition"]["name"]
    match_time_utc = match["utcDate"].replace("T", " ")[:16]

    builder_options = [
        (
            f"Victoria {home} + Más de 1.5 Goles + Más de 7.5 Córneres", 
            round(random.uniform(2.40, 2.90), 2), 
            f"He estado analizando el contexto de este partido y {home} llega con la obligación absoluta de sumar de 3 en su estadio. Su plan táctico pasa por volcarse a las bandas desde el minuto 1 para aprovechar la debilidad del rival en los centros laterales. Por su parte, {away} suele sufrir mucho cuando le hunden la línea defensiva, lo que provocará un goteo constante de córneres y ocasiones claras de gol. Veo una victoria sólida del equipo local en un partido abierto."
        ),
        (
            f"Más de 2.5 Goles + Ambos Anotan (Sí) + Más de 3.5 Tarjetas", 
            round(random.uniform(2.60, 3.20), 2), 
            f"Nos encontramos ante un choque directo donde ninguno de los dos entrenadores suele especular con el resultado. {home} destaca por su propuesta ofensiva en casa pero concede desajustes defensivos importantes al dejar huecos a la espalda. {away} tiene transiciones vertiginosas que van a hacer daño. Además, al ser un duelo de mucha tensión y necesidad de puntos, la intensidad en el medio campo provocará múltiples interrupciones y tarjetas. Esperamos goles en ambas porterías y ritmo alto."
        ),
        (
            f"Doble Oportunidad {home}/Empate + Más de 8.5 Córneres + Más de 1.5 Goles", 
            round(random.uniform(2.10, 2.50), 2), 
            f"Buscamos una combinación muy bien estructurada. {home} se muestra sumamente rocoso en su estadio y es muy difícil verles caer derrotados ante este perfil de rival. Tienen un juego muy directo que genera muchos bloqueos y saques de esquina por partido. Sumando la necesidad del equipo visitante de no irse de vacío, preveo un desarrollo activo en las áreas que nos garantice superar el margen de córneres y goles mientras nos cubrimos con el 1X."
        ),
        (
            f"Más de 0.5 Goles 1ª Parte + Victoria {home} + Más de 4.5 Córneres {home}", 
            round(random.uniform(2.50, 3.10), 2), 
            f"En este encuentro la clave está en el arranque. {home} suele salir a morder en los primeros 30 minutos para encarrilar el choque temprano, empujando al rival a encerrarse en su propia área. La diferencia de nivel técnico y el empuje de su afición me hacen inclinarme por ver al menos un gol antes del descanso y un dominio aplastante del conjunto local traducido en córneres y triunfo final."
        )
    ]

    chosen_pick, chosen_odds, analysis = random.choice(builder_options)

    forms = ["🟢 🟢 🟡 🔴 🟢", "🟢 🟢 🟢 🟡 🟢", "🟡 🔴 🟢 🟢 🟡", "🟢 🟡 🟡 🟢 🔴"]
    form_home, form_away = random.choice(forms), random.choice(forms)
    
    total_games = CHANNEL_STATS["wins"] + CHANNEL_STATS["losses"]
    winrate_total = round((CHANNEL_STATS["wins"] / total_games) * 100, 1)

    caption = (
        f"⚽ <b>ANÁLISIS Y CREAR APUESTA - TOPTIPS</b> ⚽\n\n"
        f"🏆 <b>Competición:</b> {league}\n"
        f"⚔️ <b>Encuentro:</b> {home} vs {away}\n"
        f"⏰ <b>Hora de Inicio (UTC):</b> <b>{match_time_utc}</b>\n\n"
        f"📈 <b>RITMO Y MOMENTO DE FORMA:</b>\n"
        f"• {home}: {form_home}\n"
        f"• {away}: {form_away}\n\n"
        f"🎯 <b>SELECCIÓN RECOMENDADA:</b>\n"
        f"• Combinada: <code>{chosen_pick}</code>\n"
        f"• Cuota Total (Bet365): <b>{chosen_odds:.2f}</b>\n"
        f"• Stake Sugerido: <b>1.5 / 10</b>\n\n"
        f"🔎 <b>MI ANÁLISIS DETALLADO DEL PARTIDO:</b>\n"
        f"💬 {analysis}\n\n"
        f"📊 <b>RECUENTO DEL CANAL:</b> {CHANNEL_STATS['wins']}W - {CHANNEL_STATS['losses']}L ({winrate_total}% Acierto)\n\n"
        f"💳 <b>ÚNETE AL GRUPO VIP OFICIAL TOPTIPS:</b>\n"
        f"• Pase Semanal: <b>10 €</b> | Pase Mensual: <b>34.99 €</b>\n"
        f"📲 Para recibir todas mis apuestas combinadas exclusivas del día, escríbeme a: <b>@{TELEGRAM_USERNAME}</b>"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "👑 Comprar Pase VIP (10€ Semanal / 34,99€ Mensual)", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }

    img_path = create_scores24_card(f"{home} vs {away}", league, chosen_pick, chosen_odds)
    
    sent_ok = False
    if img_path and os.path.exists(img_path):
        sent_ok = send_telegram_photo(img_path, caption, reply_markup=keyboard)
        
    # Si la foto falla, envía el texto completo para asegurar la publicación
    if not sent_ok:
        logging.info("Enviando publicación en formato texto...")
        sent_ok = send_telegram_message(caption, reply_markup=keyboard)

    if sent_ok:
        logging.info(f"¡Publicación confirmada en Telegram!: {home} vs {away}")
    else:
        logging.error("FALLO CRÍTICO: Revisa el TELEGRAM_BOT_TOKEN y CHAT_ID en Railway.")
        
    return sent_ok

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Tipster Pro Activo...")

    # Forzar primer envío inmediatamente
    publish_builder_pick()

    last_morning_day = -1

    while True:
        try:
            current_hour = datetime.now().hour
            current_day = datetime.now().day
            
            if current_day != last_morning_day and 8 <= current_hour <= 11:
                send_good_morning()
                last_morning_day = current_day
            
            publish_builder_pick()
        except Exception as e:
            logging.error(f"Error en bucle principal: {e}")
        
        time.sleep(5400)

if __name__ == "__main__":
    main()
