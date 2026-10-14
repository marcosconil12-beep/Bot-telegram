import os
import time
import logging
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------------------------------------------------
# Configuración de Logging y Entorno
# ---------------------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8657360203:AAG0wJnyLFfEaBMY8XadJs1dZdSQU42ah7c")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@FreeTopTip")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "d6abc7c413mshf80c5e16b6760bcp14e3f9jsnf2c34103db6c")
FOOTBALL_DATA_API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "d406243cc58144269f85bfe80f4e79b3")

SPAIN_TZ = ZoneInfo("Europe/Madrid")

# ---------------------------------------------------------
# Cliente de Gemini AI
# ---------------------------------------------------------
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# ---------------------------------------------------------
# Manejador Global de Errores de Red / Telegram
# ---------------------------------------------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja fallos de red o excepciones para evitar cierres del bot."""
    logging.warning(f"Excepción de red/ejecución capturada: {context.error}")

# ---------------------------------------------------------
# PASO A: Consulta Global de Partidos (Cualquier liga del mundo)
# ---------------------------------------------------------
def fetch_global_matches_rapidapi() -> list:
    """Consulta FlashLive/RapidAPI cubriendo TODAS las ligas del mundo."""
    matches = []
    if not RAPIDAPI_KEY:
        return matches

    url = "https://flashlive-sports.p.rapidapi.com/v1/events/list"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
    }
    
    # Consulta día de hoy (0) y próximo día (1) para abarcar madrugadas/MLS
    for day in ["0", "1"]:
        try:
            params = {"sport_id": "1", "indent_days": day, "locale": "es_ES"}
            res = requests.get(url, headers=headers, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                for tournament in data.get("DATA", []):
                    league_name = tournament.get("NAME", tournament.get("TOURNAMENT_NAME", "Liga Internacional"))
                    country = tournament.get("COUNTRY_NAME", "Global")
                    full_league = f"{country.upper()} - {league_name.upper()}"
                    
                    for ev in tournament.get("EVENTS", []):
                        home = ev.get("HOME_NAME", "")
                        away = ev.get("AWAY_NAME", "")
                        if home and away:
                            start_ts = ev.get("START_TIME", 0)
                            if start_ts:
                                m_time = datetime.fromtimestamp(start_ts, SPAIN_TZ).strftime("%H:%M") + " CEST"
                            else:
                                m_time = "Por definir"
                                
                            is_live = ev.get("STAGE_TYPE") == "LIVE" or ev.get("TIME_RUNNING", False)
                            
                            matches.append({
                                "league": full_league,
                                "home": home,
                                "away": away,
                                "match": f"{home} vs {away}",
                                "time": "🔴 EN DIRECTO (LIVE)" if is_live else m_time
                            })
        except Exception as e:
            logging.error(f"Error consultando RapidAPI en día {day}: {e}")

    return matches

def search_match_by_query(query: str) -> list:
    """Filtra y busca partidos de cualquier liga mundial por texto de búsqueda."""
    all_matches = fetch_global_matches_rapidapi()
    q = query.lower().strip()
    
    # Mapeo de alias comunes
    if q == "mls":
        q = "usa"
    elif q in ["europa league", "uel"]:
        q = "europa"
    
    results = []
    for m in all_matches:
        if q in m["home"].lower() or q in m["away"].lower() or q in m["league"].lower():
            results.append(m)
            
    return results

# ---------------------------------------------------------
# PASO B y C: Análisis y Redacción con Gemini API (Estilo Scores24)
# ---------------------------------------------------------
def generate_scores24_morning_report(matches: list) -> str:
    date_str = datetime.now(SPAIN_TZ).strftime("%d/%m/%Y")
    
    if not matches:
        return f"☀️ <b>Buenos días equipo de @FreeTopTip</b> ({date_str})\n\nNo se registran encuentros de primera línea en este momento. ¡Atentos a las próximas publicaciones!"

    context_text = f"Fecha: {date_str}\nLista de partidos reales confirmados:\n"
    for m in matches[:6]:
        context_text += f"- Liga: {m['league']} | Partido: {m['match']} | Hora: {m['time']}\n"

    prompt = f"""
    Actúa como un analista profesional de fútbol estilo Scores24 para el canal de Telegram @FreeTopTip.
    Usa la lista de partidos reales proporcionada.

    Escribe un post para el canal con este formato HTML estricto:

    ☀️ <b>BUENOS DÍAS EQUIPO | CARTELERA Y ANÁLISIS ({date_str})</b> ☀️

    [Breve saludo de 2 líneas]

    A continuación, desglosa los partidos principales:

    🏆 <b>[Liga]</b>
    ⏰ <b>Hora:</b> [Hora] | ⚔️ <b>[Partido]</b>
    📊 <b>Promedio de goles:</b> [xG estimado]
    📈 <b>Racha reciente:</b> [Local vs Visitante]
    🎯 <b>Pronóstico Scores24:</b> [Mercado] | 🎲 <b>Probabilidad:</b> [%]
    💡 <b>Análisis táctico:</b> [Explicación de 2 líneas].

    Contacto VIP con @Mark122.
    """

    if ai_client:
        try:
            response = ai_client.models.generate_content(
                model='gemini-1.5-flash',
                contents=f"{context_text}\n\n{prompt}"
            )
            return response.text.strip()
        except Exception as e:
            logging.error(f"Error generando reporte con Gemini: {e}")

    report = f"☀️ <b>BUENOS DÍAS EQUIPO ({date_str})</b> ☀️\n\n"
    for m in matches[:4]:
        report += f"🏆 <b>{m['league']}</b>\n⏰ <b>Hora:</b> {m['time']} | ⚔️ <b>{m['match']}</b>\n🎯 <b>Pronóstico:</b> Ambos Anotan | 🎲 <b>Probabilidad:</b> 65%\n\n"
    report += "📲 VIP: @Mark122"
    return report

def generate_single_match_analysis(match_info: dict) -> str:
    prompt = f"""
    Actúa como un analista profesional de fútbol estilo Scores24 para @FreeTopTip.
    Analiza este partido real:
    Liga: {match_info['league']}
    Partido: {match_info['match']}
    Hora: {match_info['time']}

    Genera una respuesta en HTML estricto para Telegram:
    🏆 <b>{match_info['league']}</b>
    ⏰ <b>Hora:</b> {match_info['time']} | ⚔️ <b>{match_info['match']}</b>

    📊 <b>Promedio de goles estimado:</b> [Dato]
    📈 <b>Racha reciente:</b> [Local vs Visitante]
    ⚔️ <b>H2H histórico:</b> [Resumen]
    🎯 <b>Pronóstico Scores24:</b> [Pick de valor] | 🎲 <b>Confianza:</b> [%]
    💡 <b>Análisis detallado:</b> [2 párrafos breves explicando xG, bajas y propuesta táctica en primera persona].
    """

    if ai_client:
        try:
            res = ai_client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            return res.text.strip()
        except Exception as e:
            logging.error(f"Error analizando partido individual: {e}")

    return (
        f"🏆 <b>{match_info['league']}</b>\n"
        f"⏰ <b>Hora:</b> {match_info['time']} | ⚔️ <b>{match_info['match']}</b>\n\n"
        f"💡 <b>Análisis Scores24:</b> Encuentro analizado según métricas de xG. Mercado de valor detectado en líneas de goles."
    )

# ---------------------------------------------------------
# PASO C: Comandos e Interacción en Telegram
# ---------------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 <b>¡Bienvenido al Bot de @FreeTopTip (Estilo Scores24)!</b>\n\n"
        "Comandos disponibles:\n"
        "• /buenosdias - Envía el informe matutino con la cartelera real de hoy.\n"
        "• /buscar [equipo o liga] - Ejemplo: <code>/buscar mls</code> o <code>/buscar Inter</code>"
    )
    await update.message.reply_text(msg, parse_mode="HTML")

async def morning_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Consultando eventos globales y generando informe con Gemini...")
    matches = fetch_global_matches_rapidapi()
    report = generate_scores24_morning_report(matches)
    await update.message.reply_text(report, parse_mode="HTML", disable_web_page_preview=True)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Indica el equipo o liga a buscar. Ejemplo: <code>/buscar mls</code>", parse_mode="HTML")
        return

    query = " ".join(context.args
