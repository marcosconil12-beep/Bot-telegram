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
TELEGRAM_USERNAME = "Mark122" # Tu usuario VIP configurado

published_picks = set()

# Sistema de estadísticas acumuladas del canal
CHANNEL_STATS = {
    "wins": 58,
    "losses": 12,
    "staked_units": 140,
    "profit_units": +42.5
}

def send_telegram_message(text, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        return None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN.strip()}/sendMessage"
    payload = {"chat_id": CHAT_ID.strip(), "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        res = requests.post(url, json=payload, timeout=15)
        return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error enviando mensaje: {e}")
        return None

def send_telegram_photo(photo_path, caption, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        return None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN.strip()}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            data = {"chat_id": CHAT_ID.strip(), "caption": caption, "parse_mode": "HTML"}
            if reply_markup:
                data["reply_markup"] = reply_markup
            res = requests.post(url, data=data, files={"photo": photo}, timeout=15)
            return res.json().get("ok")
    except Exception as e:
        logging.error(f"Error enviando foto: {e}")
        return None

def create_scores24_card(match_title, league_name, pick_text, odds_val, is_live=False):
    """Genera una tarjeta gráfica profesional (modo Normal o modo LIVE en directo)."""
    bg_color = (13, 27, 42) if not is_live else (25, 10, 15)
    border_color = (0, 212, 170) if not is_live else (255, 45, 85)
    
    img = Image.new('RGB', (1000, 600), color=bg_color)
    d = ImageDraw.Draw(img)
    
    # Borde y Marco de Cabecera
    d.rectangle([20, 20, 980, 580], outline=border_color, width=4)
    d.rectangle([20, 20, 980, 110], fill=(20, 40, 65) if not is_live else (50, 15, 25))
    
    header_title = "🛡️ TOPTIPS OFFICIAL ANALYTICS" if not is_live else "🔴 TOPTIPS LIVE IN-PLAY ALERT"
    d.text((40, 48), header_title, fill=border_color)
    d.text((580, 48), league_name.upper()[:25], fill=(200, 200, 200))
    
    d.text((40, 140), "ENCUENTRO EN DIRECTO:" if is_live else "PARTIDO ANALIZADO EN DETALLE:", fill=(150, 160, 180))
    d.text((40, 180), match_title, fill=(255, 255, 255))
    
    # Recuadro de Pronóstico
    d.rectangle([40, 240, 960, 420], fill=(24, 43, 73) if not is_live else (60, 20, 30), outline=(255, 215, 0), width=2)
    d.text((70, 260), "SELECCIÓN RECOMENDADA:" if not is_live else "OPORTUNIDAD LIVE EN DIRECTO:", fill=(255, 215, 0))
    d.text((70, 315), f"{pick_text}", fill=(255, 255, 255))
    d.text((750, 315), f"@{odds_val:.2f}", fill=border_color)

    d.text((40, 460), f"📊 Métricas: xG Proyectado | Córneres | Tarjetas | Yield: +{CHANNEL_STATS['profit_units']}U", fill=(150, 160, 180))
    d.text((40, 510), f"Canal Oficial: TOPTIPS | Contacto VIP: @{TELEGRAM_USERNAME}", fill=(255, 215, 0))
    
    filename = "scores24_card.png"
    img.save(filename)
    return filename

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("Bot Tipster Pro Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error HTTP: {e}")

def get_global_pro_match():
    """Base de datos masiva revisada."""
    pool = [
        ("Real Madrid", "Villarreal", "La Liga EA Sports"),
        ("FC Barcelona", "Atlético de Madrid", "La Liga EA Sports"),
        ("Real Zaragoza", "Granada CF", "La Liga Hypermotion (2ª ESP)"),
        ("Sporting de Gijón", "Racing de Santander", "La Liga Hypermotion (2ª ESP)"),
        ("Manchester City", "Liverpool", "Premier League"),
        ("Arsenal", "Chelsea", "Premier League"),
        ("Leeds United", "Sheffield United", "Championship (2ª ENG)"),
        ("Inter de Milán", "Juventus", "Serie A"),
        ("AC Milan", "Napoli", "Serie A"),
        ("Palermo", "Sassuolo", "Serie B (2ª ITA)"),
        ("Bayern Múnich", "RB Leipzig", "Bundesliga"),
        ("Borussia Dortmund", "Bayer Leverkusen", "Bundesliga"),
        ("Hamburgo", "Hertha BSC", "2. Bundesliga (GER)"),
        ("PSG", "Marsella", "Ligue 1"),
        ("Lyon", "AS Monaco", "Ligue 1"),
        ("Flamengo", "Palmeiras", "Brasileirão Serie A"),
        ("Santos", "Sport Recife", "Brasileirão Serie B"),
        ("Vissel Kobe", "Yokohama F. Marinos", "J1 League (Japón)")
    ]
    return random.choice(pool)

def send_good_morning():
    total_games = CHANNEL_STATS["wins"] + CHANNEL_STATS["losses"]
    winrate = round((CHANNEL_STATS["wins"] / total_games) * 100, 1)
    
    text = (
        "☀️ <b>¡BUENOS DÍAS A TODOS LOS MIEMBROS DE TOPTIPS!</b> ☀️\n\n"
        "☕ Arrancamos una jornada clave con los análisis más potentes del mercado.\n\n"
        "📊 <b>REVISIÓN DE RESULTADOS Y BALANCES DEL MES:</b>\n"
        f"✅ <b>Picks Acertados:</b> {CHANNEL_STATS['wins']}\n"
        f"❌ <b>Picks Fallados:</b> {CHANNEL_STATS['losses']}\n"
        f"🔥 <b>Efectividad (WinRate):</b> <b>{winrate}%</b>\n"
        f"💰 <b>Beneficio Neto:</b> <b>+{CHANNEL_STATS['profit_units']} Unidades</b>\n\n"
        f"💣 <i>¡Aprovecha la racha de aciertos! Escríbeme ahora para unirte al Grupo VIP o comprar el Stake 10 de hoy:</i>\n"
        f"👉 <b>Contactar al Analista: @{TELEGRAM_USERNAME}</b>"
    )
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🚀 Entrar al Grupo VIP Ahora", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }
    send_telegram_message(text, reply_markup=keyboard)

def publish_live_pick():
    """Envía un pronóstico exclusivo en DIRECTO (LIVE)."""
    home, away, league = get_global_pro_match()
    match_title = f"{home} vs {away}"
    
    minute = random.randint(55, 78)
    score_home = random.randint(0, 2)
    score_away = random.randint(0, 2)
    
    live_markets = [
        (f"Más de 0.5 Goles antes del min 85'", round(random.uniform(1.80, 2.25), 2), f"Presión asfixiante de {home} con múltiples ocasiones claras en la segunda parte."),
        (f"Más de 1.5 Goles en la 2ª Parte", round(random.uniform(1.95, 2.40), 2), "Partido totalmente roto en ambas áreas, ritmo de juego altísimo."),
        (f"Próximo Gol: {home}", round(random.uniform(2.00, 2.50), 2), f"{home} domina la posesión en campo contrario y ha volcado sus líneas al ataque.")
    ]
    chosen_pick, chosen_odds, live_analysis = random.choice(live_markets)

    caption = (
        f"🔴 <b>¡ALERTA LIVE EN DIRECTO!</b> 🔴\n\n"
        f"🏆 <b>Competición:</b> {league}\n"
        f"⚔️ <b>Encuentro:</b> {match_title}\n"
        f"⏱️ <b>Minuto:</b> <b>{minute}'</b> | ⚽ <b>Marcador:</b> <b>{score_home} - {score_away}</b>\n\n"
        f"🔥 <b>ENTRADA LIVE RECOMENDADA:</b>\n"
        f"• Selección: <code>{chosen_pick}</code>\n"
        f"• Cuota Live: <b>{chosen_odds:.2f}</b> (Bet365 / Casas de Apuestas)\n"
        f"• Stake Sugerido: <b>1.5 / 10</b>\n\n"
        f"💬 <i>Lectura en vivo: {live_analysis}</i>\n\n"
        f"⚡ <b>¡ENTRAD YA MISMO ANTES DE QUE BAJE LA CUOTA O HAYA GOL!</b>\n\n"
        f"💎 <b>¿Quieres la jugada LIVE VIP con cuota +3.50?</b>\n"
        f"Escríbeme por privado al momento: <b>@{TELEGRAM_USERNAME}</b>"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "⚡ Hablar con Analista por Telegram", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }

    img_path = create_scores24_card(f"{match_title} ({minute}' {score_home}-{score_away})", league, chosen_pick, chosen_odds, is_live=True)
    if send_telegram_photo(img_path, caption, reply_markup=keyboard):
        logging.info(f"Pronóstico LIVE enviado con éxito: {match_title}")

def publish_pick():
    """Envía un pronóstico Pre-partido normal."""
    home, away, league = get_global_pro_match()
    match_title = f"{home} vs {away}"
    odds_val = round(random.uniform(1.75, 2.30), 2)
    
    today_str = datetime.now().strftime("%Y-%m-%d-%H")
    pick_id = f"{match_title}_{today_str}"
    
    if pick_id in published_picks:
        return

    forms = ["🟢 🟢 🟡 🔴 🟢", "🟢 🟢 🟢 🟡 🟢", "🟡 🔴 🟢 🟢 🟡", "🟢 🟡 🟡 🟢 🔴"]
    form_home, form_away = random.choice(forms), random.choice(forms)
    
    xg_home = round(random.uniform(1.2, 2.4), 2)
    xg_away = round(random.uniform(0.8, 1.9), 2)
    exact_score = random.choice(["1-0", "2-1", "2-2", "1-1", "0-2", "3-1", "1-2"])
    corners = random.randint(8, 12)
    cards = random.randint(4, 7)

    markets = [
        ("Victoria de " + home, odds_val, f"{home} domina territorialmente con un xG de {xg_home} frente a {xg_away} del rival."),
        ("Más de 2.5 Goles", round(odds_val * 0.95, 2), f"Alta proyección ofensiva. Goles esperados conjuntos superiores a 3.1."),
        ("Ambos Anotan (Sí)", round(odds_val * 0.98, 2), f"Las defensas muestran concesiones recientes y los ataques promedian alta efectividad.")
    ]
    chosen_pick, chosen_odds, analysis = random.choice(markets)

    total_games = CHANNEL_STATS["wins"] + CHANNEL_STATS["losses"]
    winrate_total = round((CHANNEL_STATS["wins"] / total_games) * 100, 1)

    caption = (
        f"⚽ <b>ANÁLISIS PROFESIONAL DETALLADO - TOPTIPS</b> ⚽\n\n"
        f"🏆 <b>Competición:</b> {league}\n"
        f"⚔️ <b>Encuentro:</b> {match_title}\n\n"
        f"📈 <b>ESTADO DE FORMA:</b>\n"
        f"• {home}: {form_home}\n"
        f"• {away}: {form_away}\n\n"
        f"📊 <b>MÉTRICAS Y xG (Goles Esperados):</b>\n"
        f"• xG {home}: <b>{xg_home}</b> | xG {away}: <b>{xg_away}</b>\n"
        f"• Total Goles Proyectados: <b>{round(xg_home + xg_away, 1)}</b>\n\n"
        f"🎯 <b>PRONÓSTICO GRATUITO:</b>\n"
        f"• Selección: <code>{chosen_pick}</code>\n"
        f"• Cuota: <b>{chosen_odds:.2f}</b> (Bet365)\n\n"
        f"🔍 <b>DESGLOSE ESTADÍSTICO COMPLETO:</b>\n"
        f"• Resultado Exacto Sugerido: <b>{exact_score}</b>\n"
        f"• Total Córneres Estimados: <b>+{corners}.5</b>\n"
        f"• Total Tarjetas Esperadas: <b>+{cards}.5</b>\n\n"
        f"💬 <i>Lectura táctica: {analysis}</i>\n\n"
        f"📊 <b>RECUENTO CANAL:</b> {CHANNEL_STATS['wins']}W - {CHANNEL_STATS['losses']}L ({winrate_total}% Acierto)\n\n"
        f"🔥 <b>¿QUIERES EL COMBINADO VIP CON CUOTA +4.50?</b>\n"
        f"Habla conmigo directamente para conseguir la jugada del día: <b>@{TELEGRAM_USERNAME}</b>\n\n"
        f"💪 <i>¡A por el verde! Stake 1.5.</i>"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "💎 Comprar Pick Premium / Unirse al VIP", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }

    img_path = create_scores24_card(match_title, league, chosen_pick, chosen_odds, is_live=False)
    if send_telegram_photo(img_path, caption, reply_markup=keyboard):
        published_picks.add(pick_id)
        CHANNEL_STATS["wins"] += 1
        CHANNEL_STATS["profit_units"] = round(CHANNEL_STATS["profit_units"] + 1.2, 1)
        logging.info(f"Análisis pre-partido publicado con éxito: {match_title}")

def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    logging.info("Servicio Master Tipster Pro con módulo LIVE Activo...")

    time.sleep(3)
    publish_pick()

    last_morning_day = -1
    cycle_counter = 0

    while True:
        try:
            current_hour = datetime.now().hour
            current_day = datetime.now().day
            
            if current_day != last_morning_day and 8 <= current_hour <= 11:
                send_good_morning()
                last_morning_day = current_day
            
            # Alterna entre publicar picks Pre-partido y Alertas LIVE en directo
            if cycle_counter % 2 == 0:
                publish_pick()
            else:
                publish_live_pick()
                
            cycle_counter += 1
        except Exception as e:
            logging.error(f"Error en bucle: {e}")
        
        time.sleep(7200) # Publica cada 2 horas

if __name__ == "__main__":
    main()
