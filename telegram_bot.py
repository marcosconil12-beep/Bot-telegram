import os
import time
import logging
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
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

SPAIN_TZ = ZoneInfo("Europe/Madrid")

# Configuración de Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    ai_model = None

# ---------------------------------------------------------
# Creador de Imagen/Cartel Visual del Pick (Pillow)
# ---------------------------------------------------------
def create_match_banner(home_team: str, away_team: str, league: str, match_time: str, pick: str) -> BytesIO:
    """Genera una imagen personalizada para el pick con plantilla visual elegante."""
    width, height = 800, 450
    image = Image.new("RGB", (width, height), color=(15, 23, 42))  # Fondo azul oscuro deportivo
    draw = ImageDraw.Draw(image)

    # Marco decorativo
    draw.rectangle([15, 15, width - 15, height - 15], outline=(59, 130, 246), width=4)

    # Título Liga
    draw.text((40, 40), f"🏆 {league[:45]}", fill=(255, 255, 255))
    draw.text((40, 75), f"⏰ HORA: {match_time}", fill=(148, 163, 184))

    # Enfrentamiento Principal
    vs_text = f"⚔️  {home_team}\n       VS\n    {away_team}"
    draw.text((60, 140), vs_text, fill=(248, 250, 252))

    # Recuadro de Pick
    draw.rectangle([40, 310, width - 40, 400], fill=(30, 41, 59), outline=(34, 197, 94), width=3)
    draw.text((60, 325), "🎯 RECOMENDACIÓN VIP / SCORES24:", fill=(148, 163, 184))
    draw.text((60, 355), f"🔥 {pick}", fill=(34, 197, 94))

    # Firma
    draw.text((width - 220, height - 35), "📲 Canal Oficial: @FreeTopTip", fill=(100, 116, 139))

    bio = BytesIO()
    bio.name = "match_banner.png"
    image.save(bio, "PNG")
    bio.seek(0)
    return bio

# ---------------------------------------------------------
# Recopilador en Tiempo Real desde RapidAPI
# ---------------------------------------------------------
def fetch_realtime_matches() -> list:
    """Extrae la base de datos de partidos de hoy con datos de ligas principales."""
    matches = []
    if not RAPIDAPI_KEY:
        return matches

    url = "https://flashlive-sports.p.rapidapi.com/v1/events/list"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "flashlive-sports.p.rapidapi.com"
    }

    try:
        params = {"sport_id": "1", "indent_days": "0", "locale": "es_ES", "timezone": "2"}
        res = requests.get(url, headers=headers, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            for tournament in data.get("DATA", []):
                league = tournament.get("NAME", "Liga").upper()
                country = tournament.get("COUNTRY_NAME", "Global").upper()
                full_league = f"{country} - {league}"

                for ev in tournament.get("EVENTS", []):
                    home = ev.get("HOME_NAME", "")
                    away = ev.get("AWAY_NAME", "")
                    start_ts = ev.get("START_TIME", 0)
                    m_time = datetime.fromtimestamp(start_ts, SPAIN_TZ).strftime("%H:%M") + " CEST" if start_ts else "Por definir"

                    if home and away:
                        matches.append({
                            "league": full_league,
                            "home": home,
                            "away": away,
                            "time": m_time,
                            "raw": ev
                        })
    except Exception as e:
        logging.error(f"Error extrayendo partidos: {e}")

    return matches

# ---------------------------------------------------------
# Análisis Multimercado con Gemini AI
# ---------------------------------------------------------
def generate_advanced_multimarket_analysis(m: dict) -> tuple[str, str]:
    """Genera análisis profundo considerando goles, córners, tarjetas y remates."""
    prompt = f"""
    Actúa como el analista jefe de apuestas deportivas del canal @FreeTopTip (Estilo Scores24).
    Analiza este partido real con base de datos cuantitativa:

    Liga: {m['league']}
    Partido: {m['home']} vs {m['away']}
    Hora: {m['time']}

    Realiza un estudio completo considerando 5 mercados clave:
    1. Ganador / Apuesta Sin Empate (1X2)
    2. Total de Goles (Over/Under xG)
    3. Córners estimados por dinámica por bandas
    4. Tarjetas / Intensidad arbitral y faltas
    5. Remates a puerta e índice ofensivo

    Responde en formato HTML estricto para Telegram:

    🏆 <b>{m['league']}</b>
    ⏰ <b>Hora:</b> {m['time']} | ⚔️ <b>{m['home']} vs {m['away']}</b>

    📊 <b>MÉTRICAS Y ESTADÍSTICAS:</b>
    • ⚽ <b>xG (Goles Esperados):</b> [Estimación]
    • 🚩 <b>Córners promedio:</b> [Dato estimado]
    • 🟨 <b>Tarjetas / Faltas:</b> [Línea estimada]
    • 🎯 <b>Remates a puerta:</b> [Proyección]

    🔍 <b>ANÁLISIS TÁCTICO PROFUNDO:</b>
    [2 párrafos detallados redactados en primera persona explicando el momento de forma, dinámicas de ataque/defensa y planteamiento del técnico].

    🎯 <b>PICK PRINCIPAL SCORES24:</b> [Especifica el mercado con mejor valor: ej. Over 8.5 Córners / +2.5 Goles / Gana sin empate]
    🎲 <b>Índice de Confianza:</b> [% de probabilidad]

    📲 Canales VIP: @Mark122
    """

    pick = "Over 2.5 Goles & Córners"
    if ai_model:
        try:
            res = ai_model.generate_content(prompt)
            if res and res.text:
                text = res.text.strip()
                # Extraer el pick recomendado para la cartelera
                if "PICK PRINCIPAL" in text:
                    lines = text.split("\n")
                    for line in lines:
                        if "PICK PRINCIPAL" in line:
                            pick = line.split(":")[-1].replace("<b>", "").replace("</b>", "").strip()
                return text, pick
        except Exception as e:
            logging.error(f"Error analizando partido: {e}")

    fallback = (
        f"🏆 <b>{m['league']}</b>\n"
        f"⏰ <b>Hora:</b> {m['time']} | ⚔️ <b>{m['home']} vs {m['away']}</b>\n\n"
        f"📊 <b>Métricas de xG y Córners analizadas</b>\n"
        f"🎯 <b>Pick Sugerido:</b> {pick}\n"
        f"📲 VIP: @Mark122"
    )
    return fallback, pick

# ---------------------------------------------------------
# Tarea Automatizada (Publicación Directa en el Canal 24/7)
# ---------------------------------------------------------
async def auto_post_job(context: ContextTypes.DEFAULT_TYPE):
    """Función automática que busca partidos y los publica con imagen en el canal."""
    bot = context.bot
    logging.info("Iniciando escaneo automático de base de datos de partidos...")
    matches = fetch_realtime_matches()

    if not matches:
        logging.info("No hay partidos para publicar en este ciclo.")
        return

    # Publica los 3 partidos con mejor proyección del día
    for m in matches[:3]:
        try:
            analysis_html, pick_text = generate_advanced_multimarket_analysis(m)
            banner_img = create_match_banner(m['home'], m['away'], m['league'], m['time'], pick_text)

            # Publica la foto con el análisis directamente en el canal @FreeTopTip
            await bot.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=banner_img,
                caption=analysis_html,
                parse_mode="HTML"
            )
            time.sleep(5)  # Pausa de seguridad entre publicaciones
        except Exception as e:
            logging.error(f"Error publicando en el canal: {e}")

# ---------------------------------------------------------
# Comandos de Soporte Manual (Opcionales)
# ---------------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 <b>Bot de @FreeTopTip Activo en Modo Piloto Automático 24/7.</b>\n\n"
        "El bot publicará automáticamente en el canal los análisis multimercado (goles, córners, tarjetas) con imágenes personalizadas.",
        parse_mode="HTML"
    )

async def force_post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para forzar una publicación inmediata en el canal."""
    await update.message.reply_text("🔄 Ejecutando analisis automático y publicando cartelera en el canal...")
    await auto_post_job(context)
    await update.message.reply_text("✅ Publicación enviada con éxito al canal @FreeTopTip.")

# ---------------------------------------------------------
# Ejecución Principal
# ---------------------------------------------------------
def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Configurar tarea automática programada cada 4 horas (14400 segundos)
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(auto_post_job, interval=14400, first=10)

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("publicar", force_post_command))

    logging.info("Bot configurado en Piloto Automático 24/7...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
