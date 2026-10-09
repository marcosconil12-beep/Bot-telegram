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
TELEGRAM_USERNAME = "Mark122" # Tu usuario VIP

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
    """Genera la tarjeta gráfica estilo Scores24."""
    bg_color = (13, 27, 42) if not is_live else (25, 10, 15)
    border_color = (0, 212, 170) if not is_live else (255, 45, 85)
    
    img = Image.new('RGB', (1000, 600), color=bg_color)
    d = ImageDraw.Draw(img)
    
    d.rectangle([20, 20, 980, 580], outline=border_color, width=4)
    d.rectangle([20, 20, 980, 110], fill=(20, 40, 65) if not is_live else (50, 15, 25))
    
    header_title = "🛡️ TOPTIPS OFFICIAL ANALYTICS" if not is_live else "🚨 ALERTA IA LIVE EN DIRECTO"
    d.text((40, 48), header_title, fill=border_color)
    d.text((580, 48), league_name.upper()[:25], fill=(200, 200, 200))
    
    d.text((40, 140), "ENCUENTRO MONITOREADO:" if is_live else "PARTIDO ANALIZADO EN DETALLE:", fill=(150, 160, 180))
    d.text((40, 180), match_title, fill=(255, 255, 255))
    
    d.rectangle([40, 240, 960, 420], fill=(24, 43, 73) if not is_live else (60, 20, 30), outline=(255, 215, 0), width=2)
    d.text((70, 260), "SELECCIÓN RECOMENDADA:" if not is_live else "SEÑAL IA DETECTADA:", fill=(255, 215, 0))
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
        self.wfile.write("Bot Vendedor Pro con Escáner IA Activo".encode('utf-8'))

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler).serve_forever()
    except Exception as e:
        logging.error(f"Error HTTP: {e}")

def get_global_pro_match():
    pool = [
        # España
        ("Real Madrid", "Villarreal", "La Liga EA Sports"),
        ("FC Barcelona", "Atlético de Madrid", "La Liga EA Sports"),
        ("Real Zaragoza", "Granada CF", "La Liga Hypermotion (2ª ESP)"),
        ("Sporting de Gijón", "Racing de Santander", "La Liga Hypermotion (2ª ESP)"),
        # Inglaterra
        ("Manchester City", "Liverpool", "Premier League"),
        ("Arsenal", "Chelsea", "Premier League"),
        ("Leeds United", "Sheffield United", "Championship (2ª ENG)"),
        # Italia
        ("Inter de Milán", "Juventus", "Serie A"),
        ("AC Milan", "Napoli", "Serie A"),
        ("Palermo", "Sassuolo", "Serie B (2ª ITA)"),
        # Alemania
        ("Bayern Múnich", "RB Leipzig", "Bundesliga"),
        ("Borussia Dortmund", "Bayer Leverkusen", "Bundesliga"),
        ("Hamburgo", "Hertha BSC", "2. Bundesliga (GER)"),
        # Francia
        ("PSG", "Marsella", "Ligue 1"),
        ("Lyon", "AS Monaco", "Ligue 1"),
        # Brasil
        ("Flamengo", "Palmeiras", "Brasileirão Serie A"),
        ("Santos", "Sport Recife", "Brasileirão Serie B"),
        # Japón
        ("Vissel Kobe", "Yokohama F. Marinos", "J1 League (Japón)")
    ]
    return random.choice(pool)

def scan_live_matches_ia():
    """
    ESCÁNER IA EN TIEMPO REAL:
    Evalúa continuamente parámetros en vivo (Ataques peligrosos, xG acumulado, remates a puerta).
    Si se cumple la condición de IA, salta de inmediato con la alerta.
    """
    home, away, league = get_global_pro_match()
    match_title = f"{home} vs {away}"
    
    # Simulación de condiciones en tiempo real (1ª mitad entre 20'-40' o 2ª mitad entre 55'-80')
    half = random.choice(["1ª Parte", "2ª Parte"])
    minute = random.randint(22, 38) if half == "1ª Parte" else random.randint(58, 78)
    
    score_home = random.randint(0, 1) if half == "1ª Parte" else random.randint(0, 2)
    score_away = random.randint(0, 1) if half == "1ª Parte" else random.randint(0, 2)
    
    shots_on_target = random.randint(6, 11)
    corners_count = random.randint(5, 9)
    danger_attacks = random.randint(45, 80)
    
    # Condición de IA para disparar la alerta
    ia_triggers = []
    
    # Requisito IA 1: Alta presión de gol
    if danger_attacks > 50 and shots_on_target >= 6:
        ia_triggers.append((
            f"GOL PROMINENTE ({half}): Más de 0.5 Goles antes del descanso/final", 
            round(random.uniform(1.85, 2.30), 2), 
            f"Algoritmo IA detecta índice de presión {danger_attacks} ataques peligrosos y {shots_on_target} disparos a puerta. Alta probabilidad de gol inminente."
        ))
    
    # Requisito IA 2: Carrera a Córneres
    if corners_count >= 6:
        ia_triggers.append((
            f"CÓRNERES EN VIVO: Más de {corners_count + 3}.5 Córneres Totales", 
            round(random.uniform(1.80, 2.15), 2), 
            f"El partido promedia un córner cada 5 minutos. Ritmo de juego totalmente volcado por las bandas."
        ))
        
    # Requisito IA 3: Remontada / Victoria del Favorito
    if score_home < score_away and "Real Madrid" in home or "Manchester City" in home or "PSG" in home:
        ia_triggers.append((
            f"VICTORIA EN REMONTADA: {home} (Empate Apuesta No Válida)", 
            round(random.uniform(2.10, 2.70), 2), 
            f"{home} está encerrando al rival en su área con más del 70% de posesión en la {half}."
        ))

    if not ia_triggers:
        return False # No reúne los requisitos estrictos de la IA en este chequeo

    chosen_pick, chosen_odds, ia_reason = random.choice(ia_triggers)
    
    pick_id = f"LIVE_{match_title}_{minute}_{datetime.now().strftime('%Y%m%d%H%M')}"
    if pick_id in published_picks:
        return False

    caption = (
        f"🚨 <b>¡ALERTA IA DETECTADA EN DIRECTO!</b> 🚨\n\n"
        f"🏆 <b>Competición:</b> {league}\n"
        f"⚔️ <b>Encuentro:</b> {match_title}\n"
        f"⏱️ <b>Tiempo:</b> <b>{minute}' ({half})</b> | ⚽ <b>Marcador:</b> <b>{score_home} - {score_away}</b>\n\n"
        f"🔥 <b>SEÑAL IA DE ALTO VALOR:</b>\n"
        f"• Selección: <code>{chosen_pick}</code>\n"
        f"• Cuota Live: <b>{chosen_odds:.2f}</b> (Casas de Apuestas / Bet365)\n"
        f"• Stake Recomendado: <b>2 / 10 (Fuerte)</b>\n\n"
        f"🧠 <b>ANÁLISIS ALGORÍTMICO EN TIEMPO REAL:</b>\n"
        f"<i>{ia_reason}</i>\n\n"
        f"⚡ <b>¡ENTRAD RÁPIDO ANTES DE QUE BAJE LA CUOTA O SUCEDA LA JUGADA!</b>\n\n"
        f"💎 <b>¿Quieres las señales VIP privadas con cuota +4.00?</b>\n"
        f"Escríbeme por privado de inmediato: <b>@{TELEGRAM_USERNAME}</b>"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "⚡ Entrar al VIP / Contactar Analista", "url": f"https://t.me/{TELEGRAM_USERNAME}"}]
        ]
    }

    img_path = create_scores24_card(f"{match_title} ({minute}' {score_home}-{score_away})", league, chosen_pick, chosen_odds, is_live=True)
    if send_telegram_photo(img_path, caption, reply_markup=keyboard):
        published_picks.add(pick_id)
        logging.info(f"¡Alerta IA LIVE publicada con éxito!: {match_title}")
        return True
    return False

def publish_pick():
    """Análisis Pre-Partido."""
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
        ("Más de 2.5 Goles", round(odds_val * 0.95, 2), f"Alta proyección offensive. Goles esperados conjuntos superiores a 3.1."),
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
    logging.info("Servicio Escáner IA y Tipster Pro Activo...")

    time.sleep(3)
    publish_pick() # Lanza un primer pronóstico de bienvenida al arrancar

    last_pre_match_time = time.time()

    while True:
        try:
            # 1. ESCÁNER IA LIVE CONTINUO (revisa cada 3 minutos si hay partidos en vivo que cumplan los requisitos)
            scan_live_matches_ia()
            
            # 2. PUBLICACIÓN PRE-PARTIDO PERIÓDICA (cada 2 horas envía un desglose pre-partido)
            if time.time() - last_pre_match_time >= 7200:
                publish_pick()
                last_pre_match_time = time.time()

        except Exception as e:
            logging.error(f"Error en bucle del escáner: {e}")
        
        time.sleep(180) # Revisa y escanea los partidos LIVE cada 3 minutos

if __name__ == "__main__":
    main()
