def fetch_daily_picks_from_gemini():
    """Gemini selecciona los partidos reales de HOY y redacta el análisis detallado."""
    now_spain = datetime.now(SPAIN_TZ)
    date_today = now_spain.strftime("%Y-%m-%d")
    
    prompt = f"""
    Eres un tipster profesional con acceso a datos analíticos avanzados.
    La fecha actual de hoy es {date_today}.
    
    TAREA:
    Genera 4 pronósticos deportivos para partidos de fútbol QUE SE JUEGUEN HOY ({date_today}).
    Prioriza si hay Champions League, Europa League, Conference League o ligas de primera/segunda división de Europa, Sudamérica, Asia o Australia que jueguen HOY.
    
    REQUISITOS OBLIGATORIOS PARA CADA PICK:
    1. Para cada partido, crea una selección de valor con cuota 2.00 o superior en Bet365 (puedes usar BetBuilder / Crear Apuesta).
    2. Redacta un análisis EN PRIMERA PERSONA ("He analizado...", "Viendo la tendencia de córneres...", "Me inclino por...") MUY DETALLADO.
    3. Cita aspectos tácticos concretos: porcentaje de posesión, estilo de transiciones, promedio de faltas/tarjetas, saques de esquina o volumen de remates recibidos. Prohibido usar frases genéricas.
    
    FORMATO DE SALIDA (Responde ÚNICAMENTE con un array JSON válido):
    [
      {{
        "match": "Equipo A vs Equipo B",
        "league": "Nombre de la Competición",
        "pick": "Crear Apuesta: Victoria Equipo A + Más de 8.5 Córneres",
        "odds": 2.15,
        "analysis": "Explicación técnica detallada en primera persona con datos específicos del partido de hoy."
      }}
    ]
    """

    try:
        # Intentamos con el endpoint v1beta de gemini-1.5-flash
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        res = requests.post(url, headers=headers, json=payload, timeout=25)
        data = res.json()
        
        if "candidates" in data and len(data["candidates"]) > 0:
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text.replace("```", "").strip()
            return json.loads(raw_text)
        else:
            logging.error(f"Error o respuesta vacía de Gemini: {data}")
            return []
    except Exception as e:
        logging.error(f"Error obteniendo partidos de hoy desde Gemini: {e}")
        return []
