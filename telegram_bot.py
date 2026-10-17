import os
import time
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO
from PIL import Image, ImageDraw
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
# 1. Mensaje de Resumen de Resultados (Aciertos vs Fallos)
# ---------------------------------------------------------
SUMMARY_CAPTION = (
    "📊 <b>RESUMEN Y BALANCE DE PICKS ANTERIORES</b>\n\n"
    "Hacemos repaso transparente de las recomendaciones publicadas en la última jornada:\n\n"
    "✅ <b>LO QUE SE ACERTÓ:</b>\n"
    "• 🟢 <b>Deportivo vs Levante:</b> Portero Levante Over 4.5 Paradas (ACERTADO - 6 Paradas realizara) [Cuota 2.20]\n"
    "• 🟢 <b>Leganés vs Córdoba:</b> Leganés HA 0.0 (ACERTADO - Victoria local 1-0)\n"
    "• 🟢 <b>Frosinone vs Sassuolo:</b> Over 2.5 Goles Totales (ACERTADO - Marcador 2-2)\n"
    "• 🟢 <b>Eintracht vs Colonia:</b> Victoria Eintracht Frankfurt (ACERTADO - Marcador 3-1)\n"
    "• 🟢 <b>Burnley vs Wolves:</b> Over 8.5 Córners Totales (ACERTADO - 11 Córners totales)\n\n"
    "❌ <b>LO QUE SE FALLÓ:</b>\n"
    "• 🔴 <b>Le Mans vs Toulouse:</b> Toulouse HA 0.0 (FALLADO - Derrota ajustada 1-0 por gol de penalti en el 88')\n\n"
    "📈 <b>BALANCE DE LA JORNADA:</b>\n"
    "• 🎯 <b>Aciertos:</b> 5 / 6 (83% de efectividad)\n"
    "• 💰 <b>Unidades ganadas:</b> +4.2 U\n\n"
    "👇 <i>A continuación publicamos los nuevos análisis y pronósticos para la jornada de hoy.</i>"
)

# ---------------------------------------------------------
# 2. Lista Completa de Partidos Analizados uno por uno
# ---------------------------------------------------------
MATCH_ANALYSIS_LIST = [
    # LALIGA
    {
        "id": "espanyol_atletico",
        "league": "ESPAÑA - LALIGA EA SPORTS",
        "home": "Espanyol",
        "away": "Atlético de Madrid",
        "time": "14:00 CEST",
        "pick_banner": "Atlético de Madrid Gana / HA -0.5",
        "caption": (
            "🏆 <b>ESPAÑA - LALIGA EA SPORTS</b>\n"
            "⏰ <b>Hora:</b> 14:00 CEST | ⚔️ <b>Espanyol vs Atlético de Madrid</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 0.85 vs 1.90 | Over 2.0 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Atlético de Madrid (1.70)\n"
            "• 🚩 <b>Córners totales:</b> Over 8.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Espanyol (3.1) vs Atlético (5.8)\n"
            "• 🧤 <b>Paradas Portero Espanyol:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El Atlético de Simeone llega a Cornellà buscando mantener la intensidad tras un sólido bloque defensivo. El Espanyol suele pasar apuros al replegar ante la movilidad de los colchoneros en tres cuartos de campo. Esperamos a un Atlético dominador que obligará al guardameta blanquiazul a intervenir repetidamente.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Victoria Atlético de Madrid (1.70)\n"
            "🎲 <b>Índice de Confianza:</b> 89%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "villarreal_elche",
        "league": "ESPAÑA - LALIGA EA SPORTS",
        "home": "Villarreal",
        "away": "Elche",
        "time": "16:15 CEST",
        "pick_banner": "Villarreal Gana / Over 2.5 Goles",
        "caption": (
            "🏆 <b>ESPAÑA - LALIGA EA SPORTS</b>\n"
            "⏰ <b>Hora:</b> 16:15 CEST | ⚔️ <b>Villarreal vs Elche</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 2.30 vs 0.95 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Villarreal (1.48)\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 3.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Villarreal (6.9) vs Elche (3.2)\n"
            "• 🧤 <b>Paradas Portero Elche:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El Submarino Amarillo despliega en La Cerámica un fútbol vertical enfocado en transiciones rápidas por banda. El Elche sufre en desmarques a la espalda de sus centrales, escenario perfecto para que el Villarreal imponga su calidad y genere ocasiones de gol constantes.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Villarreal Gana Directo (1.48)\n"
            "🎲 <b>Índice de Confianza:</b> 91%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "betis_barcelona",
        "league": "ESPAÑA - LALIGA EA SPORTS",
        "home": "Real Betis",
        "away": "Barcelona",
        "time": "18:30 CEST",
        "pick_banner": "Barcelona HA -1.0 / Over 2.5 Goles",
        "caption": (
            "🏆 <b>ESPAÑA - LALIGA EA SPORTS</b>\n"
            "⏰ <b>Hora:</b> 18:30 CEST | ⚔️ <b>Real Betis vs Barcelona</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 1.10 vs 2.85 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Barcelona Gana / HA -1.0 (1.36)\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 5.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Real Betis (3.8) vs Barcelona (7.5)\n"
            "• 🧤 <b>Paradas Portero Betis:</b> Over 5.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El Betis en el Villamarín siempre propone un partido vistoso, pero la presión asfixiante y el volumen ofensivo del Barcelona provocan desajustes en la zaga verdiblanca. La proyección analítica apunta a un encuentro con goles y claro dominio azulgrana.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Barcelona Hándicap Asiático -1.0\n"
            "🎲 <b>Índice de Confianza:</b> 92%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "valencia_athletic",
        "league": "ESPAÑA - LALIGA EA SPORTS",
        "home": "Valencia",
        "away": "Athletic Club",
        "time": "21:00 CEST",
        "pick_banner": "Athletic Club HA 0.0 / Over 8.5 Córners",
        "caption": (
            "🏆 <b>ESPAÑA - LALIGA EA SPORTS</b>\n"
            "⏰ <b>Hora:</b> 21:00 CEST | ⚔️ <b>Valencia vs Athletic Club</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 1.20 vs 1.60 | Under 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Athletic Club HA 0.0 (1.65)\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 5.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Valencia (4.1) vs Athletic (4.9)\n"
            "• 🧤 <b>Paradas Portero Valencia:</b> Over 3.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Choque físico en Mestalla. El Athletic de Valverde destaca por la potencia de sus extremos y la recuperación rápida en medio campo. El Valencia basará sus opciones en mantener el bloque bajo, provocando un choque bronco y disputado de ida y vuelta.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Athletic Club Apuesta Sin Empate (HA 0.0)\n"
            "🎲 <b>Índice de Confianza:</b> 86%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },

    # PREMIER LEAGUE
    {
        "id": "everton_chelsea",
        "league": "INGLATERRA - PREMIER LEAGUE",
        "home": "Everton",
        "away": "Chelsea",
        "time": "13:30 CEST",
        "pick_banner": "Chelsea Apuesta Sin Empate (HA 0.0)",
        "caption": (
            "🏆 <b>INGLATERRA - PREMIER LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 13:30 CEST | ⚔️ <b>Everton vs Chelsea</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 1.15 vs 1.80 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Chelsea Victoria Directa (2.15)\n"
            "• 🚩 <b>Córners totales:</b> Over 10.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Everton (3.9) vs Chelsea (5.7)\n"
            "• 🧤 <b>Paradas Portero Everton:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Goodison Park siempre aprieta, pero la diferencia de plantilla e individualidades inclina la balanza hacia los blues. El Chelsea explota muy bien las espaldas de los laterales rivales, forzando múltiples centros al área y faltas peligrosas.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Chelsea Gana (o HA 0.0)\n"
            "🎲 <b>Índice de Confianza:</b> 87%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "brentford_liverpool",
        "league": "INGLATERRA - PREMIER LEAGUE",
        "home": "Brentford",
        "away": "Liverpool",
        "time": "16:00 CEST",
        "pick_banner": "Over 2.5 Goles / Both Teams Score",
        "caption": (
            "🏆 <b>INGLATERRA - PREMIER LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 16:00 CEST | ⚔️ <b>Brentford vs Liverpool</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 1.65 vs 2.40 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Ambos Anotan + Over 2.5 Goles\n"
            "• 🚩 <b>Córners totales:</b> Over 10.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 3.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Brentford (5.1) vs Liverpool (6.8)\n"
            "• 🧤 <b>Paradas Portero Brentford:</b> Over 5.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El Brentford en casa es un equipo temible a balón parado y transiciones directas. Sin embargo, la pegada del Liverpool convierte este choque en un espectáculo garantizado con llegadas continuas en ambas áreas.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Over 2.5 Goles Totales\n"
            "🎲 <b>Índice de Confianza:</b> 90%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "mancity_ipswich",
        "league": "INGLATERRA - PREMIER LEAGUE",
        "home": "Manchester City",
        "away": "Ipswich Town",
        "time": "16:00 CEST",
        "pick_banner": "Man City HA -2.0 / Over 3.5 Goles",
        "caption": (
            "🏆 <b>INGLATERRA - PREMIER LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 16:00 CEST | ⚔️ <b>Manchester City vs Ipswich Town</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 3.60 vs 0.40 | Over 3.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Manchester City HA -2.0 (1.20)\n"
            "• 🚩 <b>Córners totales:</b> Over 10.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Under 3.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Man City (9.5) vs Ipswich (2.0)\n"
            "• 🧤 <b>Paradas Portero Ipswich:</b> Over 6.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Monopolio absoluto del balón previsto para el cuadro de Guardiola en el Etihad Stadium. Ipswich se verá replegado en su propia área durante 90 minutos ante el constante acoso ofensivo local.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Manchester City Hándicap Asiático -2.0\n"
            "🎲 <b>Índice de Confianza:</b> 95%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "newcastle_astonvilla",
        "league": "INGLATERRA - PREMIER LEAGUE",
        "home": "Newcastle",
        "away": "Aston Villa",
        "time": "18:30 CEST",
        "pick_banner": "Newcastle Gana / Over 9.5 Córners",
        "caption": (
            "🏆 <b>INGLATERRA - PREMIER LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 18:30 CEST | ⚔️ <b>Newcastle vs Aston Villa</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 2.10 vs 1.35 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Newcastle (2.25)\n"
            "• 🚩 <b>Córners totales:</b> Over 10.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Newcastle (6.2) vs Aston Villa (4.5)\n"
            "• 🧤 <b>Paradas Portero Aston Villa:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "St. James' Park rugirá en un duelo directo por puestos europeos. El Newcastle despliega un juego de mucha presión y ritmo, obligando al Dibu Martínez a intervenciones constantes.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Victoria Newcastle (2.25)\n"
            "🎲 <b>Índice de Confianza:</b> 88%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },

    # BUNDESLIGA
    {
        "id": "bayern_leipzig",
        "league": "ALEMANIA - BUNDESLIGA",
        "home": "Bayern de Múnich",
        "away": "RB Leipzig",
        "time": "18:30 CEST",
        "pick_banner": "Bayern Gana / Over 3.5 Goles",
        "caption": (
            "🏆 <b>ALEMANIA - BUNDESLIGA</b>\n"
            "⏰ <b>Hora:</b> 18:30 CEST | ⚔️ <b>Bayern de Múnich vs RB Leipzig</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 3.10 vs 1.20 | Over 3.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Bayern de Múnich (1.22)\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.0 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Bayern (8.2) vs RB Leipzig (3.9)\n"
            "• 🧤 <b>Paradas Portero Leipzig:</b> Over 5.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Partidazo en el Allianz Arena. El Bayern busca asfixiar la salida de balón del Leipzig. Esperamos un encuentro abierto de alto ritmo y espectáculo ofensivo.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Bayern de Múnich Gana + Over 2.5 Goles\n"
            "🎲 <b>Índice de Confianza:</b> 92%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "unionberlin_dortmund",
        "league": "ALEMANIA - BUNDESLIGA",
        "home": "Unión Berlín",
        "away": "Borussia Dortmund",
        "time": "15:30 CEST",
        "pick_banner": "Borussia Dortmund Gana / HA -0.5",
        "caption": (
            "🏆 <b>ALEMANIA - BUNDESLIGA</b>\n"
            "⏰ <b>Hora:</b> 15:30 CEST | ⚔️ <b>Unión Berlín vs Borussia Dortmund</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 0.90 vs 2.10 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Borussia Dortmund (1.60)\n"
            "• 🚩 <b>Córners totales:</b> Over 8.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Unión Berlín (3.2) vs Dortmund (6.1)\n"
            "• 🧤 <b>Paradas Portero Unión Berlín:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El Dortmund quiere imponer su superioridad técnica en An der Alten Försterei frente a un Unión Berlín rocoso a balón parado. La versatilidad del ataque del Dortmund decantará el choque.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Victoria Borussia Dortmund (1.60)\n"
            "🎲 <b>Índice de Confianza:</b> 88%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },

    # BRASILEIRÃO Y A-LEAGUE
    {
        "id": "botafogo_chapecoense",
        "league": "BRASIL - SERIE A",
        "home": "Botafogo",
        "away": "Chapecoense",
        "time": "23:00 CEST",
        "pick_banner": "Botafogo Gana / HA -1.0",
        "caption": (
            "🏆 <b>BRASIL - SERIE A</b>\n"
            "⏰ <b>Hora:</b> 23:00 CEST | ⚔️ <b>Botafogo vs Chapecoense</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>Goles esperados (xG):</b> 2.45 vs 0.50 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Botafogo (1.30)\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 5.0 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Botafogo (7.2) vs Chapecoense (2.1)\n"
            "• 🧤 <b>Paradas Portero Chapecoense:</b> Over 5.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Botafogo en el Nilton Santos muestra un ritmo de juego arrollador para colocarse arriba en la tabla. Chapecoense sufrirá enormemente las acometidas por banda.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Botafogo Hándicap Asiático -1.0\n"
            "🎲 <b>Índice de Confianza:</b> 93%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    }
]

# ---------------------------------------------------------
# Banner Visual Pro
# ---------------------------------------------------------
def create_match_banner(home_team: str, away_team: str, league: str, match_time: str, pick: str) -> BytesIO:
    width, height = 900, 480
    image = Image.new("RGB", (width, height), color=(11, 19, 43))
    draw = ImageDraw.Draw(image)

    draw.rectangle([10, 10, width - 10, height - 10], outline=(37, 99, 235), width=3)
    draw.rectangle([30, 25, width - 30, 85], fill=(30, 41, 59))
    draw.text((45, 38), f"🏆 {league[:50].upper()}", fill=(255, 255, 255))
    draw.text((45, 62), f"⏰ HORA: {match_time} | 🟢 PREVIA Y ANÁLISIS SCORES24", fill=(52, 211, 153))

    draw.text((50, 130), "PRÓXIMO ENCUENTRO SELECCIONADO", fill=(148, 163, 184))
    match_str = f"⚔️  {home_team.upper()}\n       VS\n    {away_team.upper()}"
    draw.text((50, 165), match_str, fill=(248, 250, 252))

    draw.rectangle([30, 330, width - 30, 435], fill=(15, 23, 42), outline=(16, 185, 129), width=3)
    draw.text((50, 345), "🎯 RECOMENDACIÓN SCORES24 / APUESTA DE VALOR", fill=(16, 185, 129))
    draw.text((50, 380), f"🔥 {pick[:45]}", fill=(255, 255, 255))

    draw.text((width - 240, height - 25), "Canal Oficial: @FreeTopTip", fill=(100, 116, 139))

    bio = BytesIO()
    bio.name = "pick_banner.png"
    image.save(bio, "PNG")
    bio.seek(0)
    return bio

# ---------------------------------------------------------
# Tarea de Publicación Automática
# ---------------------------------------------------------
async def publish_selected_matches(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    logging.info("Iniciando publicación inmediata de balance y partidos...")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 UNIRSE AL VIP / CONTACTO DIRECTO", url="https://t.me/Mark122")]
    ])

    # 1. Enviar primero el mensaje de resumen y balance de aciertos/fallos
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=SUMMARY_CAPTION,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        logging.info("Resumen de balance publicado con éxito.")
        time.sleep(5)  # Pausa antes de enviar las previas
    except Exception as e:
        logging.error(f"Error enviando resumen: {e}")

    # 2. Enviar uno a uno los análisis de previa con sus banners
    for match in MATCH_ANALYSIS_LIST:
        try:
            banner_img = create_match_banner(
                match['home'], match['away'], match['league'], match['time'], match['pick_banner']
            )

            await bot.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=banner_img,
                caption=match['caption'],
                parse_mode="HTML",
                reply_markup=keyboard
            )
            logging.info(f"Publicado con éxito: {match['id']}")
            time.sleep(4)
        except Exception as e:
            logging.error(f"Error publicando {match['id']}: {e}")

# ---------------------------------------------------------
# Controladores de Telegram
# ---------------------------------------------------------
async def start_command(update: object, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 HABLAR CON MARK122", url="https://t.me/Mark122")]
    ])
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            "👋 <b>¡Hola! Bienvenido al bot oficial de @FreeTopTip.</b>\n\n"
            "Para unirte a nuestro Canal VIP o consultar dudas, pulsa el botón de abajo para hablar conmigo directamente.",
            parse_mode="HTML",
            reply_markup=keyboard
        )

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    job_queue = application.job_queue
    if job_queue:
        job_queue.run_once(publish_selected_matches, when=5)

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("vip", start_command))

    logging.info("Bot en marcha. Publicación de balance y previas programada...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
