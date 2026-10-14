import os
import time
import logging
import requests
from datetime import datetime
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

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "d6abc7c413mshf80c5e16b6760bcp14e3f9jsnf2c34103db6c")
FOOTBALL_DATA_API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "d406243cc58144269f85bfe80f4e79b3")

SPAIN_TZ = ZoneInfo("Europe/Madrid")

# ---------------------------------------------------------
# Cliente de Gemini AI
# ---------------------------------------------------------
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# ---------------------------------------------------------
# Manejador Global de Errores
# ---------------------------------------------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.warning(f"Excepción capturada: {context.error}")

# ---------------------------------------------------------
# Consulta Global de Partidos (RapidAPI)
# ---------------------------------------------------------
def fetch_global_matches_rapidapi() -> list:
    matches = []
    if not RAPIDAPI_KEY:
        return matches

    url = "https://flashlive-sports.p.rapidapi.com/v1/events/list"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
    }
    
    for day in [-1, 0, 1]:
        try:
            params = {
                "sport_id": "1", 
                "indent_days": str(day), 
                "locale": "es_ES",
                "timezone": "2"
            }
            res = requests.get(url, headers=headers, params=params, timeout=12)
            if res.status_code == 200:
                data = res.json()
                for tournament in data.get("DATA", []):
                    league_name = tournament.get("NAME", tournament.get("TOURNAMENT_NAME", "Liga Internacional"))
                    country = tournament.get("COUNTRY_NAME", "Global")
                    full_league = f"{country} - {league_name}".upper()
                    
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
    all_matches = fetch_global_matches_rapidapi()
    q = query.lower().strip()
    
    aliases = {
        "mls": ["usa", "major league", "mls"],
        "europa league": ["europa league", "uel", "europa"],
        "champions": ["champions", "ucl"],
        "premier": ["premier", "england", "inglaterra"],
        "laliga": ["spain", "españa", "la liga", "laliga"]
    }

    search_terms = aliases.get(q, [q])
    results = []
    seen = set()
    for m in all_matches:
        match_text = f"{m['home']} {m['away']} {m['league']}".lower()
        if any(term in match_text for term in search_terms):
            if m["match"] not in seen:
                seen.add(m["match"])
                results.append(m)
            
    return results

# ---------------------------------------------------------
# Análisis con Gemini API (Modelo Corregido: gemini-1.5-flash)
# ---------------------------------------------------------
def generate_single_match_analysis(match_info: dict) -> str:
    prompt = f"""
    Actúa como un analista profesional de fútbol estilo Scores24 para @FreeTopTip.
    Analiza este partido real en primera persona:
    Liga: {match_info['league']}
    Partido: {match_info['match']}
    Hora: {match_info['time']}

    Genera una respuesta detallada en formato HTML estricto para Telegram:
    🏆 <b>{match_info['league']}</b>
    ⏰ <b>Hora:</b> {match_info['time']} | ⚔️ <b>{match_info['match']}</b>

    📊 <b>Promedio de goles estimado:</b> [Dato analítico]
    📈 <b>Racha reciente:</b> [Local vs Visitante]
    ⚔️ <b>H2H histórico:</b> [Resumen de duelos]
    🎯 <b>Pronóstico Scores24:</b> [Pick de valor] | 🎲 <b>Confianza:</b> [%]
    💡 <b>Análisis detallado:</b> [2 párrafos profesionales redactados en primera persona explicando xG, dinámicas y planteamiento táctico].
    """

    if ai_client:
        try:
            res = ai_client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            if res and res.text:
                return res.text.strip()
        except Exception as e:
            logging.error(f"Error detallado de Gemini AI: {e}")
            return f"🏆 <b>{match_info['league']}</b>\n⏰ <b>Hora:</b> {match_info['time']} | ⚔️ <b>{match_info['match']}</b>\n\n💡 <b>Error API Gemini:</b> <code>{str(e)}</code>"

    return (
        f"🏆 <b>{match_info['league']}</b>\n"
        f"⏰ <b>Hora:</b> {match_info['time']} | ⚔️ <b>{match_info['match']}</b>\n\n"
        f"💡 <b>Análisis Scores24:</b> Error: Cliente de IA no inicializado."
    )

def generate_scores24_morning_report(matches: list) -> str:
    date_str = datetime.now(SPAIN_TZ).strftime("%d/%m/%Y")
    if not matches:
        return f"☀️ <b>Buenos días equipo de @FreeTopTip</b> ({date_str})\n\nNo se registran encuentros en este momento."

    context_text = f"Fecha: {date_str}\nPartidos:\n"
    for m in matches[:5]:
        context_text += f"- {m['league']} | {m['match']} | {m['time']}\n"

    prompt = f"Actúa como analista Scores24 para Telegram. Redacta un reporte matutino breve y profesional en HTML basado en:\n{context_text}"

    if ai_client:
        try:
            response = ai_client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            logging.error(f"Error reporte Gemini: {e}")

    return f"☀️ <b>BUENOS DÍAS EQUIPO ({date_str})</b> ☀️\n\n📲 VIP: @Mark122"

# ---------------------------------------------------------
# Comandos de Telegram
# ---------------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 <b>¡Bienvenido al Bot de @FreeTopTip (Estilo Scores24)!</b>\n\n"
        "Comandos:\n"
        "• /buenosdias - Informe matutino\n"
        "• /buscar [equipo o liga] - Ejemplo: <code>/buscar mls</code>"
    )
    await update.message.reply_text(msg, parse_mode="HTML")

async def morning_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Consultando eventos y generando informe con Gemini...")
    matches = fetch_global_matches_rapidapi()
    report = generate_scores24_morning_report(matches)
    await update.message.reply_text(report, parse_mode="HTML", disable_web_page_preview=True)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Indica el equipo o liga. Ejemplo: <code>/buscar mls</code>", parse_mode="HTML")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 Buscando y analizando con Gemini para <b>{query}</b>...", parse_mode="HTML")

    results = search_match_by_query(query)
    if not results:
        await update.message.reply_text(f"❌ No se encontraron partidos para '<b>{query}</b>'.", parse_mode="HTML")
        return

    for match in results[:3]:
        analysis = generate_single_match_analysis(match)
        await update.message.reply_text(analysis, parse_mode="HTML", disable_web_page_preview=True)

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("buenosdias", morning_report_command))
    application.add_handler(CommandHandler("buscar", search_command))
    logging.info("Bot en ejecución...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
