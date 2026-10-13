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
    "wins": 82,
    "losses": 14,
    "profit_units": +72.8,
    "yield_pct": 31.8
}

# Base de datos completa y exhaustiva con TODOS los partidos de tus capturas de Bet365
MATCHES_DATABASE = [
    {
        "match": "Lens vs Sporting",
        "league": "UEFA Champions League",
        "time": "18:45 CEST",
        "analysis": "• Dinámica táctica: Duelo de alta intensidad con Lens buscando asfixiar en tres cuartos de campo y Sporting priorizando salidas limpias por bandas.\n• Rendimiento e xG: Promedio conjunto superior a 2.8 goles esperados en sus choques continentales.\n• Mercados Bet365: Cuotas 1X2 (2.55 - 3.70 - 2.60). Se aprecia un valor claro en el volumen de llegada.",
        "pick_main": "Crear Apuesta: Ambos Equipos Anotan (Sí) + Más de 7.5 Córneres",
        "odds_main": 2.10,
        "pick_alt": "Sporting o Empate (Doble Oportunidad)",
        "odds_alt": 1.50
    },
    {
        "match": "Sabah vs Slavia Praga",
        "league": "UEFA Champions League",
        "time": "18:45 CEST",
        "analysis": "• Dinámica táctica: Slavia Praga asume el control absoluto de la posesión; Sabah propondrá repliegue bajo defensivo.\n• Métricas de disciplina y córneres: Se proyecta un dominio de más del 65% de balón visitante con constantes saques de esquina.\n• Mercados Bet365: Favoritismo visitante respaldado en la cuota 1.90 a la victoria directa.",
        "pick_main": "Slavia Praga Gana el Partido + Slavia Más de 4.5 Córneres",
        "odds_main": 2.25,
        "pick_alt": "Slavia Praga Gana Directo (@1.90)",
        "odds_alt": 1.90
    },
    {
        "match": "Arsenal vs Lille",
        "league": "UEFA Champions League",
        "time": "21:00 CEST",
        "analysis": "• Estado de forma: Arsenal se muestra demoledor en el Emirates Stadium (cuota local 1.20). Bukayo Saka y Gabriel Martinelli generan ocasiones constantes.\n• Remates y faltas: Se prevé una alta cantidad de faltas tácticas visitantes en la frontal para frenar las transiciones Gunner.\n• Mercado de valor: Dominio desde la primera mitad.",
        "pick_main": "Arsenal Hándicap Asiático -1.5 Goles",
        "odds_main": 1.80,
        "pick_alt": "Arsenal Más de 6.5 Córneres Totales",
        "odds_alt": 1.62
    },
    {
        "match": "Atlético de Madrid vs Manchester United",
        "league": "UEFA Champions League",
        "time": "21:00 CEST",
        "analysis": "• Fricción táctica: Duelo estelar de máxima tensión física (cuotas equilibradas 1.90 - 3.75 - 3.75).\n• Análisis disciplinario: Promedio histórico en encuentros directos superior a 5.5 tarjetas amarillas combinadas.\n• Mercados Bet365: Batalla en la medular con tendencia a faltas estratégicas y duelos intensos.",
        "pick_main": "Crear Apuesta: Más de 4.5 Tarjetas Totales + Atlético de Madrid o Empate",
        "odds_main": 2.20,
        "pick_alt": "Atlético de Madrid Empate No Válido",
        "odds_alt": 1.42
    },
    {
        "match": "Galatasaray SK vs Barcelona",
        "league": "UEFA Champions League",
        "time": "21:00 CEST",
        "analysis": "• Análisis de plantilla: El FC Barcelona llega con su tridente estrella en plena forma (Raphinha, Lamine Yamal y Ferran Torres).\n• Rendimiento ofensivo: El conjunto turco sufre a la espalda de sus laterales cuando intenta presionar arriba.\n• Mercados Bet365: Barcelona favorito claro (cuota 1.25) con un xG esperado muy elevado.",
        "pick_main": "Crear Apuesta: Barcelona Gana + Lamine Yamal Más de 0.5 Remates a Puerta",
        "odds_main": 2.05,
        "pick_alt": "Barcelona Más de 1.5 Goles en el Partido",
        "odds_alt": 1.40
    },
    {
        "match": "Inter de Milán vs Club Brujas",
        "league": "UEFA Champions League",
        "time": "21:00 CEST",
        "analysis": "• Solidez defensiva: El Inter de Lautaro Martínez busca sentenciar por la vía rápida ante su afición (cuota local 1.25).\n• Balón parado y córneres: Superioridad física italiana clara en saques de esquina y balones colgados al área.\n• Mercado Bet365: Control territorial de principio a fin.",
        "pick_main": "Inter de Milán Gana 1ª Mitad y Final del Partido",
        "odds_main": 1.85,
        "pick_alt": "Inter de Milán Mantiene Portería a Cero",
        "odds_alt": 1.68
    },
    {
        "match": "RB Leipzig vs PSV",
        "league": "UEFA Champions League",
        "time": "21:00 CEST",
        "analysis": "• Propuesta ultraofensiva: Dos plantillas diseñadas para la presión en campo rival y el contragolpe vertiginoso.\n• Métricas de xG: Más de 3.2 goles de media en sus duelos recientes. Intercambio de golpes garantizado.\n• Mercados Bet365: Opción de Crear Apuesta combinando goles y disparos.",
        "pick_main": "Crear Apuesta: Ambos Equipos Anotan (Sí) + Más de 2.5 Goles",
        "odds_main": 2.15,
        "pick_alt": "RB Leipzig Más de 1.5 Goles",
        "odds_alt": 1.55
    },
    {
        "match": "Viking FK vs Bayern de Múnich",
        "league": "UEFA Champions League",
        "time": "21:00 CEST",
        "analysis": "• Superioridad aplastante: El Bayern parte como gran favorito (cuota 1.12) con una diferencia de plantilla abismal.\n• Volumen de disparos: Se proyectan más de 18 remates totales del Bayern y dominio absoluto del ritmo de juego.\n• Mercado Bet365: Búsqueda de cuota de valor mediante hándicap o goles en la primera mitad.",
        "pick_main": "Bayern de Múnich Hándicap Asiático -2.5 Goles",
        "odds_main": 1.95,
        "pick_alt": "Más de 1.5 Goles en la 1ª Mitad",
        "odds_alt": 1.50
    },
    {
        "match": "Villarreal vs Nápoles",
        "league": "UEFA Champions League",
        "time": "21:00 CEST",
        "analysis": "• Partido igualado: La Cerámica vivirá un enfrentamiento táctico brillante (cuotas 2.05 - 3.70 - 3.30).\n• Córneres y banda: Villarreal destaca por acumular un promedio de 6.2 córneres a favor por encuentro de local.\n• Mercado Bet365: Combinada con opciones en doble oportunidad y lanzamientos de esquina.",
        "pick_main": "Crear Apuesta: Villarreal o Empate + Más de 7.5 Córneres Totales",
        "odds_main": 2.00,
        "pick_alt": "Ambos Equipos Anotan (Sí)",
        "odds_alt": 1.65
    },
    {
        "match": "Boca Juniors vs Vasco da Gama",
        "league": "Copa Sudamericana",
        "time": "02:30 CEST",
        "analysis": "• Tensión en La Bombonera: Duelo de máxima intensidad en torneo Conmebol (Boca fav @1.85).\n• Faltas y disputa: Choque de alta agresividad defensiva con riesgo elevado de múltiples amonestaciones.\n• Mercado Bet365: Valor en la fortaleza local xG de Boca Juniors.",
        "pick_main": "Victoria Boca Juniors + Más de 4.5 Tarjetas Totales",
        "odds_main": 2.30,
        "pick_alt": "Victoria Boca Juniors Directa (@1.85)",
        "odds_alt": 1.85
    },
    {
        "match": "Bristol City vs Blackburn",
        "league": "Inglaterra - Championship",
        "time": "20:45 CEST",
        "analysis": "• Intensidad británica: Bristol busca imponer su ritmo local (cuotas 2.05 - 3.25 - 3.60).\n• Disputas aéreas: Elevado número de saques de esquina y balones al área por ambos costados.\n• Mercado Bet365: Doble oportunidad combinada con saques de esquina.",
        "pick_main": "Bristol City o Empate + Más de 8.5 Córneres Totales",
        "odds_main": 2.05,
        "pick_alt": "Más de 1.5 Goles Totales",
        "odds_alt": 1.38
    },
    {
        "match": "Birmingham City vs Preston",
        "league": "Inglaterra - Championship",
        "time": "21:00 CEST",
        "analysis": "• Dominio local esperado: Birmingham llega lanzado en casa (cuota 1.45) ante un Preston en horas bajas.\n• Planteamiento visitante: Bloque replegado buscando desesperadamente arañar un punto.\n• Mercado Bet365: Victoria local combinada con goles para subir cuota.",
        "pick_main": "Birmingham City Gana el Partido + Más de 1.5 Goles Totales",
        "odds_main": 1.85,
        "pick_alt": "Birmingham City Gana Directo (@1.45)",
        "odds_alt": 1.45
    }
]

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        res = requests.post(url, json=payload, timeout=15)
        return res.json().get("ok")
    except Exception as e:
        logging.error(f"Excepción Telegram: {e}")
        return False

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}
            res = requests.post(url, data=data, files={"photo": photo}, timeout=20)
            return res.json().get("ok")
    except Exception as e:
        logging.error(f"Excepción foto: {e}")
        return False

def create_scores24_card(match_title, league_name, pick_text, odds_val, match_time):
    try:
        img = Image.new('RGB', (1000, 600), color=(13, 27, 42))
        d = ImageDraw.Draw(img)
        
        d.rectangle([20, 20, 980, 580], outline=(0, 212, 170), width=4)
        d.rectangle([20, 20, 980, 110], fill=(20, 40, 65))
        
        d.text((40, 48), f"🛡️ SCORES24 ESPAÑA | HORA: {match_time}", fill=(0, 212, 170))
        d.text((580, 48), league_name.upper()[:25], fill=(200, 200, 200))
        
        d.text((40, 140), "PARTIDO ANALIZADO (BET365):", fill=(150, 160, 180))
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
    item = random.choice(MATCHES_DATABASE)

    match_title = item.get("match")
    league_name = item.get("league")
    match_time = item.get("time")
    analysis_text = item.get("analysis")
    pick_main = item.get("pick_main")
    odds_main = float(item.get("odds_main", 2.00))
    pick_alt = item.get("pick_alt")
    odds_alt = float(item.get("odds_alt", 1.60))

    now_spain = datetime.now(SPAIN_TZ)
    caption = (
        f"📊 <b>ANÁLISIS Y PRONÓSTICO ({now_spain.strftime('%d/%m/%Y')})</b> 📊\n"
        f"🌐 <i>Fuente Oficial: Datos & Estadísticas Scores24</i>\n\n"
        f"🏆 <b>Competición:</b> {league_name}\n"
        f"⚔️ <b>Encuentro:</b> {match_title}\n"
        f"⏰ <b>Hora de Inicio:</b> {match_time}\n\n"
        f"📋 <b>INFORME TÁCTICO Y ANÁLISIS DE MERCADOS:</b>\n"
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

    img_path = create_scores24_card(match_title, league_name, pick_main, odds_main, match_time)
    
    sent = False
    if img_path:
        sent = send_telegram_photo(img_path, caption)
    if not sent:
        send_telegram_message(caption)

def send_daily_sales_message():
    now_spain = datetime.now(SPAIN_TZ)
    msg = (
        f"☀️ <b>¡BUENOS DÍAS A TODOS EN @FreeTopTip! ({now_spain.strftime('%d/%m/%Y')})</b> ☀️\n\n"
        "☕ Arrancamos la jornada publicando los mejores análisis tácticos y mercados de valor de la jornada de hoy en Bet365.\n\n"
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

    # Publica automáticamente cada 15 minutos (900 segundos)
    while True:
        try:
            time.sleep(900)
            logging.info("Ejecutando nuevo ciclo de publicación...")
            publish_scores24_report()
        except Exception as e:
            logging.error(f"Error en bucle de publicación: {e}")

if __name__ == "__main__":
    main()
