import os
import time
import logging
from zoneinfo import ZoneInfo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------------------------------------------------------
# Configuración y Entorno
# ---------------------------------------------------------
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8657360203:AAHdtvCjS5o4_-p2Bk7w6mSDBBA2gbHi470")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@FreeTopTip")

SPAIN_TZ = ZoneInfo("Europe/Madrid")

# ---------------------------------------------------------
# Pronósticos de Argentina y Brasil
# ---------------------------------------------------------
MATCH_PICKS = [
    {
        "code": "ARG-ESTRC-ALD",
        "text": (
            "🇦🇷 <b>ARGENTINA - LIGA PROFESIONAL</b>\n"
            "⏰ <b>23:00 CEST</b> | ⚔️ <b>Estudiantes Río Cuarto vs Aldosivi</b>\n\n"
            "📊 <b>CÓDIGO DE SEGUIMIENTO:</b> <code>ARG-ESTRC-ALD</code>\n\n"
            "• ⚽ <b>xG Proyectado:</b> 1.10 vs 1.05 | Menos de 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Empate o Estudiantes Río Cuarto (HA 0.0) [Cuota 1.90]\n"
            "• 🚩 <b>Córners:</b> Under 9.5 Córners\n"
            "• 🟨 <b>Tarjetas:</b> Over 4.5 Tarjetas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO:</b>\n"
            "Partido muy cerrado de ritmo lento. Ambos equipos priorizan el bloque defensivo bajo y minimizan riesgos en la construcción. La opción del Hándicap Asiático a favor de los locales nos da una excelente cobertura."
        )
    },
    {
        "code": "ARG-EST-SLO",
        "text": (
            "🇦🇷 <b>ARGENTINA - LIGA PROFESIONAL</b>\n"
            "⏰ <b>23:00 CEST</b> | ⚔️ <b>Estudiantes de La Plata vs San Lorenzo</b>\n\n"
            "📊 <b>CÓDIGO DE SEGUIMIENTO:</b> <code>ARG-EST-SLO</code>\n\n"
            "• ⚽ <b>xG Proyectado:</b> 1.65 vs 0.80 | Over 1.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Estudiantes de La Plata (Cuota 2.01)\n"
            "• 🚩 <b>Córners:</b> Over 8.5 Córners\n"
            "• 🟨 <b>Tarjetas:</b> Over 5.5 Tarjetas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO:</b>\n"
            "Estudiantes en su estadio (UNO) impone una presión asfixiante sobre los centrales rivales. San Lorenzo sufre en salidas lejanas y concederá ocasiones claras de gol."
        )
    },
    {
        "code": "BRA-BAH-FLA",
        "text": (
            "🇧🇷 <b>BRASIL - SERIE A</b>\n"
            "⏰ <b>23:30 CEST</b> | ⚔️ <b>Bahia vs Flamengo</b>\n\n"
            "📊 <b>CÓDIGO DE SEGUIMIENTO:</b> <code>BRA-BAH-FLA</code>\n\n"
            "• ⚽ <b>xG Proyectado:</b> 1.15 vs 1.95 | Over 2.0 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Flamengo Directa (Cuota 1
