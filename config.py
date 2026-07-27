# ============================================================================
#  CONFIGURACIÓN DEL BOT DE EMPLEOS  —  ajusta todo aquí
# ============================================================================
#  Perfil: Kevin Santiago Quimbaya — Ingeniero de Software / Full Stack
#  Stack: React, TypeScript, Python, FastAPI, PostgreSQL, REST, automatización
#  Ubicación: Neiva, Colombia  ·  Inglés B2  ·  abierto a remoto
# ============================================================================

# --- Fuentes de empleo (todas gratis y legales) ---------------------------
ENABLE_REMOTEOK = True     # remoto global (tech)
ENABLE_REMOTIVE = True     # remoto global (software-dev)
ENABLE_WWR = True          # We Work Remotely (full-stack / back / front)
ENABLE_ARBEITNOW = True    # remoto + Europa
ENABLE_JOOBLE = True       # Colombia — SOLO corre si defines el secret JOOBLE_API_KEY

# Búsquedas para Jooble (Colombia).  Formato: (palabras_clave, ubicación)
JOOBLE_QUERIES = [
    ("desarrollador full stack react python", "Colombia"),
    ("software developer react python", "Neiva"),
]

# --- Tu perfil: palabras clave para rankear y filtrar ---------------------
# FUERTES: definen si una oferta es relevante. Al menos una debe aparecer.
STRONG_KEYWORDS = [
    "react", "typescript", "javascript", "python", "fastapi", "node",
    "postgresql", "postgres", "rest api", "full stack", "fullstack",
    "full-stack", "frontend", "front-end", "front end", "backend", "back-end",
    "back end", "software engineer", "software developer", "web developer",
    "desarrollador", "programador", "ingeniero de software", "developer",
]

# BONUS: suman puntos extra (no son obligatorias). Empujan tus mejores matches arriba.
BONUS_KEYWORDS = [
    "junior", "entry", "trainee", "intern", "pasant", "graduate", "jr",
    "remote", "remoto", "colombia", "latam", "latin america", "americas", "worldwide",
    "spanish", "español", "git", "github", "automation", "automatizaci",
    "react native", "next.js", "nextjs", "tailwind", "html", "css", "api", "postman",
]

# --- Ajustes de comportamiento --------------------------------------------
MIN_SCORE = 3          # puntaje mínimo para avisarte (súbelo si quieres menos ofertas, más precisas)
MAX_PER_RUN = 20       # máximo de ofertas nuevas por corrida (evita spam)
FIRST_RUN_TOP = 10     # en la 1ª corrida, cuántas de las mejores enviarte (el resto se marca como visto)
MAX_SEEN = 4000        # cuántos IDs recordar para no repetir ofertas
