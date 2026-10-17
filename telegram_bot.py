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
# Selección de Partidos Analizados por Imagen
# ---------------------------------------------------------
MATCH_ANALYSIS_LIST = [
    # --- IMAGEN 1: LALIGA EA SPORTS ---
    {
        "id": "realmadrid_sevilla",
        "league": "ESPAÑA - LALIGA EA SPORTS",
        "home": "Real Madrid",
        "away": "Sevilla",
        "time": "Dom 21:00 CEST",
        "pick_banner": "Real Madrid Gana + Over 2.5 Goles",
        "caption": (
            "🏆 <b>ESPAÑA - LALIGA EA SPORTS</b>\n"
            "⏰ <b>Hora:</b> Dom 21:00 CEST | ⚔️ <b>Real Madrid vs Sevilla</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 2.75 vs 0.85 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Real Madrid (1.22) / HA -1.5\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Real Madrid (7.8) vs Sevilla (3.1)\n"
            "• 🧤 <b>Paradas Portero Sevilla:</b> Over 5.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El Real Madrid en el Santiago Bernabéu imprime una marcha muy superior en ataque posicional. El Sevilla sufre en el repliegue defensivo y conceding un alto volumen de remates cuando le atacan por bandas con Vinicius y Mbappé. Preveo dominio blanco de principio a fin obligando al meta hispalense a intervenir constantemente.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Real Madrid Gana + Over 2.5 Goles Totales\n"
            "🎲 <b>Índice de Confianza:</b> 92%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "celta_alaves",
        "league": "ESPAÑA - LALIGA EA SPORTS",
        "home": "Celta de Vigo",
        "away": "Alavés",
        "time": "Dom 16:15 CEST",
        "pick_banner": "Celta de Vigo HA 0.0 (Apuesta Sin Empate)",
        "caption": (
            "🏆 <b>ESPAÑA - LALIGA EA SPORTS</b>\n"
            "⏰ <b>Hora:</b> Dom 16:15 CEST | ⚔️ <b>Celta de Vigo vs Alavés</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 1.65 vs 1.10 | Over 2.0 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Celta de Vigo HA 0.0 (Cuota 1.55 / Directa 2.20)\n"
            "• 🚩 <b>Córners totales:</b> Over 8.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 5.0 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Celta (5.2) vs Alavés (3.8)\n"
            "• 🧤 <b>Paradas Portero Alavés:</b> Over 3.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El Celta en Balaídos genera un fútbol fluido por carril interior, mientras que el Alavés basa su juego en duelos físicos y transiciones directas. La propuesta celeste nos da ventaja en creación de ocasiones claras. Aseguramos la apuesta cubriendo el empate.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Celta de Vigo HA 0.0 (Apuesta Sin Empate)\n"
            "🎲 <b>Índice de Confianza:</b> 86%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },

    # --- IMAGEN 2: PREMIER LEAGUE ---
    {
        "id": "nottingham_arsenal",
        "league": "INGLATERRA - PREMIER LEAGUE",
        "home": "Nottingham Forest",
        "away": "Arsenal",
        "time": "17:30 CEST",
        "pick_banner": "Victoria Arsenal Directa / HA -0.75",
        "caption": (
            "🏆 <b>INGLATERRA - PREMIER LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 17:30 CEST | ⚔️ <b>Nottingham Forest vs Arsenal</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 0.75 vs 2.15 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Arsenal (1.61)\n"
            "• 🚩 <b>Córners totales:</b> Over 10.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 3.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Nottingham (2.9) vs Arsenal (6.5)\n"
            "• 🧤 <b>Paradas Portero Nottingham:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El Arsenal llega en una gran dinámica de control en campo contrario y balón parado. Nottingham se encerrará en bloque bajo en City Ground, pero el volumen de llegadas y saques de esquina de los Gunners acabará rompiendo el muro local.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Victoria Arsenal Directa (1.61)\n"
            "🎲 <b>Índice de Confianza:</b> 90%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "brighton_crystalpalace",
        "league": "INGLATERRA - PREMIER LEAGUE",
        "home": "Brighton",
        "away": "Crystal Palace",
        "time": "15:00 CEST",
        "pick_banner": "Victoria Brighton / Over 2.5 Goles",
        "caption": (
            "🏆 <b>INGLATERRA - PREMIER LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 15:00 CEST | ⚔️ <b>Brighton vs Crystal Palace</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 2.30 vs 0.90 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Brighton (1.50)\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Brighton (6.8) vs Crystal Palace (3.2)\n"
            "• 🧤 <b>Paradas Portero Crystal Palace:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El estilo de posesión y presión tras pérdida del Brighton ahoga a equipos que sufren para salir de la cueva. El Crystal Palace concederá muchos centros y disparos desde la frontal.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Victoria Brighton Directa (1.50)\n"
            "🎲 <b>Índice de Confianza:</b> 89%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },

    # --- IMAGEN 3 Y 4: SERIE A & BUNDESLIGA ---
    {
        "id": "acmilan_atalanta",
        "league": "ITALIA - SERIE A",
        "home": "AC Milan",
        "away": "Atalanta",
        "time": "18:00 CEST",
        "pick_banner": "Over 2.5 Goles / Ambos Anotan",
        "caption": (
            "🏆 <b>ITALIA - SERIE A</b>\n"
            "⏰ <b>Hora:</b> 18:00 CEST | ⚔️ <b>AC Milan vs Atalanta</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 1.85 vs 1.70 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> AC Milan HA 0.0 (1.38) / Victoria (1.80)\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> AC Milan (5.5) vs Atalanta (5.2)\n"
            "• 🧤 <b>Paradas Porteros:</b> Over 3.5 Paradas cada uno\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Partidazo de ida y vuelta garantizado en San Siro. La propuesta ofensiva de Gian Piero Gasperini fuerza duelos individuales en todo el campo, garantizando llegadas constantes en ambas áreas.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Ambos Equipos Anotan / Over 2.5 Goles\n"
            "🎲 <b>Índice de Confianza:</b> 88%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "bayerleverkusen_friburgo",
        "league": "ALEMANIA - BUNDESLIGA",
        "home": "Bayer Leverkusen",
        "away": "SC Friburgo",
        "time": "15:30 CEST",
        "pick_banner": "Bayer Leverkusen Gana / Over 2.5 Goles",
        "caption": (
            "🏆 <b>ALEMANIA - BUNDESLIGA</b>\n"
            "⏰ <b>Hora:</b> 15:30 CEST | ⚔️ <b>Bayer Leverkusen vs SC Friburgo</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 2.40 vs 0.80 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Bayer Leverkusen (1.66)\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 3.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Leverkusen (7.1) vs Friburgo (3.0)\n"
            "• 🧤 <b>Paradas Portero Friburgo:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El equipo de Xabi Alonso muestra una fluidez vertical tremenda en el BayArena. El Friburgo en sus salidas sufre ante la alta intensidad de circulación de balón local.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Victoria Bayer Leverkusen (1.66)\n"
            "🎲 <b>Índice de Confianza:</b> 91%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },

    # --- IMAGEN 5: LIGUE 1 (FRANCIA) ---
    {
        "id": "lyon_niza",
        "league": "FRANCIA - LIGUE 1",
        "home": "Lyon",
        "away": "Niza",
        "time": "20:45 CEST",
        "pick_banner": "Victoria Lyon / HA -0.5",
        "caption": (
            "🏆 <b>FRANCIA - LIGUE 1</b>\n"
            "⏰ <b>Hora:</b> 20:45 CEST | ⚔️ <b>Lyon vs Niza</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 2.10 vs 0.95 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Lyon (1.75)\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Lyon (6.0) vs Niza (3.2)\n"
            "• 🧤 <b>Paradas Portero Niza:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El Lyon en el Groupama Stadium ha consolidado un bloque sólido con mucha llegada de sus centrocampistas. El Niza fuera de casa sufre replegado ante equipos intensos.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Victoria Lyon Directa (1.75)\n"
            "🎲 <b>Índice de Confianza:</b> 87%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },

    # --- IMAGEN 6 Y 7: A-LEAGUE & EREDIVISIE ---
    {
        "id": "wellington_melbournevictory",
        "league": "AUSTRALIA - A-LEAGUE",
        "home": "Wellington Phoenix",
        "away": "Melbourne Victory",
        "time": "04:00 CEST",
        "pick_banner": "Melbourne Victory HA 0.0 / Over 2.5 Goles",
        "caption": (
            "🏆 <b>AUSTRALIA - A-LEAGUE</b>\n"
            "⏰ <b>Hora:</b> 04:00 CEST | ⚔️ <b>Wellington Phoenix vs Melbourne Victory</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 1.40 vs 2.10 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Melbourne Victory HA 0.0 (Cuota 1.55 / Directa 2.10)\n"
            "• 🚩 <b>Córners totales:</b> Over 10.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 3.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Wellington (4.1) vs Melbourne (6.2)\n"
            "• 🧤 <b>Paradas Portero Wellington:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "La liga australiana se caracteriza por transiciones rápidas y partidos de ida y vuelta. El Melbourne Victory presenta un nivel ofensivo superior para marcar la diferencia.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Melbourne Victory HA 0.0 (Apuesta Sin Empate)\n"
            "🎲 <b>Índice de Confianza:</b> 86%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "cambuur_az",
        "league": "PAÍSES BAJOS - EREDIVISIE",
        "home": "Cambuur Leeuwarden",
        "away": "AZ Alkmaar",
        "time": "14:30 CEST",
        "pick_banner": "AZ Alkmaar Gana / Over 2.5 Goles",
        "caption": (
            "🏆 <b>PAÍSES BAJOS - EREDIVISIE</b>\n"
            "⏰ <b>Hora:</b> 14:30 CEST | ⚔️ <b>Cambuur vs AZ Alkmaar</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 0.80 vs 2.60 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria AZ Alkmaar (1.50)\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 3.0 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Cambuur (3.0) vs AZ Alkmaar (7.0)\n"
            "• 🧤 <b>Paradas Portero Cambuur:</b> Over 5.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Diferencia abismal de plantillas en los Países Bajos. El AZ Alkmaar dominará el encuentro de principio a fin ante un Cambuur frágil defensivamente.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Victoria AZ Alkmaar (1.50)\n"
            "🎲 <b>Índice de Confianza:</b> 92%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },

    # --- IMAGEN 8 Y 9: ALLSVENSKAN & SÜPER LIG ---
    {
        "id": "halmstad_hammarby",
        "league": "SUECIA - ALLSVENSKAN",
        "home": "Halmstad",
        "away": "Hammarby",
        "time": "16:30 CEST",
        "pick_banner": "Victoria Hammarby Directa / HA -1.0",
        "caption": (
            "🏆 <b>SUECIA - ALLSVENSKAN</b>\n"
            "⏰ <b>Hora:</b> 16:30 CEST | ⚔️ <b>Halmstad vs Hammarby</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 0.50 vs 2.50 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Hammarby (1.22)\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 3.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Halmstad (2.1) vs Hammarby (6.9)\n"
            "• 🧤 <b>Paradas Portero Halmstad:</b> Over 5.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "El Hammarby llega en plena lucha por los puestos altos frente a un Halmstad muy mermado defensivamente. Dominio abrumador visitante previsto.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Victoria Hammarby (1.22)\n"
            "🎲 <b>Índice de Confianza:</b> 94%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },
    {
        "id": "istanbul_gaziantep",
        "league": "TURQUÍA - SÜPER LIG",
        "home": "Istanbul Basaksehir",
        "away": "Gaziantep FK",
        "time": "18:00 CEST",
        "pick_banner": "Victoria Istanbul Basaksehir",
        "caption": (
            "🏆 <b>TURQUÍA - SÜPER LIG</b>\n"
            "⏰ <b>Hora:</b> 18:00 CEST | ⚔️ <b>Istanbul Basaksehir vs Gaziantep FK</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 2.20 vs 0.85 | Over 2.5 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Istanbul Basaksehir (1.57)\n"
            "• 🚩 <b>Córners totales:</b> Over 9.5 Córners\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 4.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Basaksehir (6.1) vs Gaziantep (3.0)\n"
            "• 🧤 <b>Paradas Portero Gaziantep:</b> Over 4.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "Basaksehir en casa se muestra inexpugnable controlando la posesión en tres cuartos de campo. Gaziantep sufre fuera de casa concediendo muchas llegadas.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Victoria Istanbul Basaksehir (1.57)\n"
            "🎲 <b>Índice de Confianza:</b> 90%\n\n"
            "📩 <b>Habla conmigo para acceder al VIP:</b> @Mark122"
        )
    },

    # --- IMAGEN 10: BRASILEIRÃO SERIE A ---
    {
        "id": "atleticomineiro_coritiba",
        "league": "BRASIL - SERIE A",
        "home": "Atlético Mineiro",
        "away": "Coritiba",
        "time": "23:30 CEST",
        "pick_banner": "Victoria Atlético Mineiro / HA -0.75",
        "caption": (
            "🏆 <b>BRASIL - SERIE A</b>\n"
            "⏰ <b>Hora:</b> 23:30 CEST | ⚔️ <b>Atlético Mineiro vs Coritiba</b>\n\n"
            "📊 <b>MÉTRICAS SCORES24 Y PREVIA EN VIVO:</b>\n"
            "• ⚽ <b>xG Proyectado:</b> 2.30 vs 0.65 | Over 2.0 Goles\n"
            "• 🏆 <b>Pick Resultado:</b> Victoria Atlético Mineiro (1.66)\n"
            "• 🚩 <b>Córners totales:</b> Over 10.5 Córners Totales\n"
            "• 🟨 <b>Tarjetas totales:</b> Over 5.5 Tarjetas\n"
            "• 🎯 <b>Remates a puerta:</b> Mineiro (6.8) vs Coritiba (2.5)\n"
            "• 🧤 <b>Paradas Portero Coritiba:</b> Over 5.5 Paradas\n\n"
            "💡 <b>ANÁLISIS TÁCTICO DE PREVIA:</b>\n"
            "En el MRV Arena el Galo aprieta desde el primer minuto impulsado por su afición. Coritiba sufre enormemente en desplazamientos lejanos en el Brasileirão.\n\n"
            "🎯 <b>PICK RECOMENDADO:</b> Victoria Atlético Mineiro (1.66)\n"
            "🎲 <b>Índice de Confianza:</b> 91%\n\n"
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
    draw.text((45, 62), f"⏰ HORA: {match_time} | 🟢 PREVIA SCORES24", fill=(52, 211, 153))

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
    logging.info("Iniciando publicación de los nuevos partidos seleccionados...")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 UNIRSE AL VIP / CONTACTO DIRECTO", url="https://t.me/Mark122")]
    ])

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

    logging.info("Bot en marcha. Publicación de pronósticos programada...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
