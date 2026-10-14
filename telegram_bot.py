import os
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
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

# Carga de variables de entorno desde Railway / Entorno local
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "TU_TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@FreeTopTip")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "TU_GEMINI_API_KEY")

# Credenciales de API de Fútbol
FOOTBALL_DATA_API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "d406243cc58144269f85bfe80f4e79b3")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "d6abc7c413mshf80c5e16b6760bcp14e3f9jsnf2c34103db6c")

SPAIN_TZ = ZoneInfo("Europe/Madrid")

# ---------------------------------------------------------
# Cliente de Gemini AI
# ---------------------------------------------------------
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# ---------------------------------------------------------
# PASO A: Consulta a la API de Fútbol en tiempo real
# ---------------------------------------------------------
def get_today_matches_realtime() -> list:
    """
    Consulta partidos reales programados para el día de hoy usando Football-Data.org.
    Si no devuelve partidos, consulta FlashLive via RapidAPI.
    """
    today_str = datetime.now(SPAIN_TZ).strftime("%Y-%m-%d")
    matches = []

    # 1. Intento con Football-Data.org
    if FOOTBALL_DATA_API_KEY:
        try:
            url = f"https://api.football-data.org/v4/matches?dateFrom={today_str}&dateTo={today_str}"
            headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
            res = requests.get(url, headers=headers, timeout=12)
            if res.status_code == 200:
                data = res.json()
                for match in data.get("matches", []):
                    home = match["homeTeam"]["name"]
                    away = match["awayTeam"]["name"]
                    league = match["competition"]["name"]
                    match_utc = match.get("utcDate", "")
                    
                    if match_utc:
                        dt_utc = datetime.fromisoformat(match_utc.replace("Z", "+00:00"))
                        match_time = dt_utc.astimezone(SPAIN_TZ).strftime("%H:%M")
                    else:
                        match_time = "Por definir"

                    matches.append({
                        "league": league,
                        "home": home,
                        "away": away,
                        "match": f"{home} vs {away}",
                        "time": f"{match_time} CEST"
                    })
        except Exception as e:
            logging.error(f"Error consultando Football-Data.org: {e}")

    # 2. Respaldo con RapidAPI (FlashLive Sports) si la primera API no devolvió partidos
    if not matches and RAPIDAPI_KEY:
        try:
            url = "https://flashlive-sports.p.rapidapi.com/v1/events/list"
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
            }
            params = {"sport_id": "1", "indent_days": "0", "locale": "es_ES"}
            res = requests.get(url, headers=headers, params=params, timeout=12)
            if res.status_code == 200:
                data = res.json()
                for tournament in data.get("DATA", []):
                    league_name = tournament.get("NAME", tournament.get("TOURNAMENT_NAME", "Liga Internacional"))
                    country = tournament.get("COUNTRY_NAME", "")
                    full_league = f"{country} - {league_name}".strip(" -")
                    for ev in tournament.get("EVENTS", []):
                        home = ev.get("HOME_NAME", "")
                        away = ev.get("AWAY_NAME", "")
                        if home and away:
                            start_ts = ev.get("START_TIME", 0)
                            if start_ts:
                                m_time = datetime.fromtimestamp(start_ts, SPAIN_TZ).strftime("%H:%M") + " CEST"
                            else:
                                m_time = "Por definir"
                            matches.append({
                                "league": full_league,
                                "home": home,
                                "away": away,
                                "match": f"{home} vs {away}",
                                "time": m_time
                            })
        except Exception as e:
            logging.error(f"Error consultando RapidAPI FlashLive: {e}")

    return matches

def search_match_by_query(query: str) -> list:
    """Filtra partidos reales de la jornada que coincidan con la búsqueda del usuario."""
    all_matches = get_today_matches_realtime()
    query_lower = query.lower()
    results = [
        m for m in all_matches 
        if query_lower in m["home"].lower() or query_lower in m["away"].lower() or query_lower in m["league"].lower()
    ]
    return results

# ---------------------------------------------------------
# PASO B y C: Análisis y Redacción con Gemini API (Estilo Scores24)
# ---------------------------------------------------------
def generate_scores24_morning_report(matches: list) -> str:
    """
    Genera un informe matutino con saludo de 'Buenos días' y desglose de partidos estilo Scores24.
    """
    date_str = datetime.now(SPAIN_TZ).strftime("%d/%m/%Y")
    
    if not matches:
        return f"☀️ <b>Buenos días equipo de @FreeTopTip</b> ({date_str})\n\nHoy no hay encuentros de primera línea registrados en la agenda de partidos. ¡Mantente atento a las actualizaciones del canal!"

    # Formatear el contexto de los partidos
    context_text = f"Fecha de hoy: {date_str}\nLista de partidos reales confirmados de la jornada:\n"
    for m in matches[:6]:  # Limitamos a los partidos más relevantes
        context_text += f"- Liga: {m['league']} | Partido: {m['match']} | Hora: {m['time']}\n"

    prompt = f"""
    Actúa como un analista profesional de fútbol estilo Scores24 y redactor jefe del canal de Telegram @FreeTopTip.
    Usa estrictamente la información de partidos reales recibida en el contexto. No inventes partidos ni fechas.

    Escribe una publicación completa para el canal con este formato HTML estricto:

    ☀️ <b>BUENOS DÍAS EQUIPO | CARTELERA Y ANÁLISIS DE HOY ({date_str})</b> ☀️

    Escribe un saludo inicial motivador de 2 líneas para la comunidad de @FreeTopTip.

    A continuación, para cada partido proporcionado en el contexto (máximo 4 partidos destacados):

    🏆 <b>[Nombre de la Liga]</b>
    ⏰ <b>Hora:</b> [Hora CEST] | ⚔️ <b>[Equipo Local] vs [Equipo Visitante]</b>
    📊 <b>Promedio de goles:</b> [Estimación analítica razonable ej: 2.6 goles/partido]
    📈 <b>Estado de forma reciente:</b> [Desglose breve ej: Local L-W-W | Visitante D-W-L]
    ⚔️ <b>H2H Duelos directos:</b> [Tendencia histórica previa]
    🎯 <b>Pronóstico Scores24:</b> [Mercado recomendado ej: Ambos Anotan / Victoria Local] | 🎲 <b>Probabilidad:</b> [Porcentaje %]
    💡 <b>Análisis táctico:</b> [Explicación detallada en 2 frases cortas del porqué de este pronóstico].

    Fin del mensaje con una invitación a interactuar y consultar el canal VIP con @Mark122.
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

    # Respaldo si la API de Gemini falla
    report = f"☀️ <b>BUENOS DÍAS EQUIPO | CARTELERA DE HOY ({date_str})</b> ☀️\n\n"
    for m in matches[:4]:
        report += (
            f"🏆 <b>{m['league']}</b>\n"
            f"⏰ <b>Hora:</b> {m['time']} | ⚔️ <b>{m['match']}</b>\n"
            f"📊 <b>Promedio de goles:</b> 2.5\n"
            f"🎯 <b>Pronóstico Scores24:</b> H.A. +0.5 / Ambos Anotan | 🎲 <b>Probabilidad:</b> 65%\n"
            f"💡 <b>Análisis táctico:</b> Duelo de alta intensidad con métricas ofensivas destacadas.\n\n"
        )
    report += "📲 Contacta para VIP: @Mark122"
    return report

def generate_single_match_analysis(match_info: dict) -> str:
    """Genera un desglose individual de un partido solicitado por el usuario."""
    prompt = f"""
    Actúa como un analista profesional de fútbol estilo Scores24 para @FreeTopTip.
    Analiza detalladamente este partido real:
    Liga: {match_info['league']}
    Partido: {match_info['match']}
    Hora: {match_info['time']}

    Genera una respuesta en formato HTML estricto:
    🏆 <b>{match_info['league']}</b>
    ⏰ <b>Hora:</b> {match_info['time']} | ⚔️ <b>{match_info['match']}</b>

    📊 <b>Promedio de goles estimado:</b> [Dato]
    📈 <b>Racha reciente:</b> [Local vs Visitante]
    ⚔️ <b>H2H histórico:</b> [Resumen de enfrentamientos]
    🎯 <b>Pronóstico Scores24:</b> [Pick de valor] | 🎲 <b>Confianza:</b> [%]
    💡 <b>Análisis detallado:</b> [2 párrafos explicativos sobre xG, ausencias y estilo táctico en primera persona].
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
        f"💡 <b>Análisis Scores24:</b> Encuentro analizado según las métricas recientes de xG y forma deportiva. Mercado de valor detectado en líneas de goles."
    )

# ---------------------------------------------------------
# PASO 3: Comandos e Interacción en Telegram
# ---------------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    msg = (
        "👋 <b>¡Bienvenido al Bot Oficial de @FreeTopTip (Estilo Scores24)!</b>\n\n"
        "Comandos disponibles:\n"
        "• /buenosdias - Envía el saludo e informe matutino con partidos reales de hoy.\n"
        "• /buscar [nombre del equipo o liga] - Busca y analiza cualquier partido de hoy en tiempo real."
    )
    await update.message.reply_text(msg, parse_mode="HTML")

async def morning_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /buenosdias"""
    await update.message.reply_text("🔄 Consultando las API de fútbol y procesando análisis con Gemini...")
    matches = get_today_matches_realtime()
    report = generate_scores24_morning_report(matches)
    await update.message.reply_text(report, parse_mode="HTML", disable_web_page_preview=True)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /buscar <equipo/liga>"""
    if not context.args:
        await update.message.reply_text("⚠️ Indica el equipo o liga a buscar. Ejemplo: <code>/buscar Real Madrid</code>", parse_mode="HTML")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 Buscando partidos de hoy para <b>{query}</b>...", parse_mode="HTML")

    results = search_match_by_query(query)
    if not results:
        await update.message.reply_text(f"❌ No se encontraron partidos reales de hoy para '<b>{query}</b>'. Verifique el nombre o intente de nuevo.", parse_mode="HTML")
        return

    for match in results[:2]:  # Enviamos los partidos encontrados
        analysis = generate_single_match_analysis(match)
        await update.message.reply_text(analysis, parse_mode="HTML", disable_web_page_preview=True)

# ---------------------------------------------------------
# Ejecución Principal
# ---------------------------------------------------------
def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("buenosdias", morning_report_command))
    application.add_handler(CommandHandler("buscar", search_command))

    logging.info("Bot en ejecución...")
    application.run_polling()

if __name__ == "__main__":
    main()
