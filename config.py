# ============================================================================
#  CONFIGURACIÓN DEL BOT DE EMPLEOS  —  ajusta todo aquí
# ============================================================================
#  Perfil: Kevin Santiago Quimbaya — Ingeniero de Software / Full Stack
#  Stack: React, TypeScript, Python, FastAPI, PostgreSQL, REST, automatización
#  Ubicación: Neiva, Colombia  ·  Inglés B2  ·  early-career  ·  abierto a remoto
# ============================================================================

# --- Fuentes (gratis y legales) -------------------------------------------
ENABLE_REMOTEOK = True      # remoto global (tech)
ENABLE_REMOTIVE = True      # remoto global (software-dev)
ENABLE_WWR = True           # We Work Remotely (full-stack / back / front)
ENABLE_ARBEITNOW = True     # remoto + Europa
ENABLE_HIMALAYAS = True     # remoto global (trae nivel/seniority)
ENABLE_JOBICY = True        # remoto global (marca geo LATAM)
ENABLE_JOOBLE = True        # Colombia — necesita el secret JOOBLE_API_KEY
ENABLE_CAREERJET = True     # agregador (Colombia) — necesita el secret CAREERJET_AFFID
ENABLE_SERPAPI = True       # Google Jobs (LinkedIn/Computrabajo/Indeed) — necesita SERPAPI_KEY

# Etiquetas a consultar en Jobicy (tu stack)
JOBICY_TAGS = ["python", "react", "javascript", "typescript"]

# Búsquedas de Jooble (Colombia).  (keywords, ubicación)
JOOBLE_QUERIES = [
    ("desarrollador full stack react python", "Colombia"),
    ("software developer react python", "Neiva"),
    ("full stack developer remote", "Colombia"),          # en inglés (remoto internacional)
]

# Búsquedas de Careerjet.  (keywords, ubicación, locale_code)
CAREERJET_QUERIES = [
    ("desarrollador full stack react python", "Colombia", "es_CO"),
    ("react python developer", "Neiva", "es_CO"),
    ("junior full stack developer remote", "Colombia", "es_CO"),   # en inglés
]

# Búsquedas de Google Jobs (SerpApi).  (query, ubicación).
# OJO: free tier = 250 búsquedas/mes. 3 corridas/día x 2 queries ≈ 180/mes. No agregues más.
SERPAPI_QUERIES = [
    ("desarrollador full stack react python", "Colombia"),
    ("junior full stack developer python react remote", "Colombia"),
]

# --- Tu perfil: palabras clave para rankear y filtrar ---------------------
STRONG_KEYWORDS = [
    "react", "typescript", "javascript", "python", "fastapi", "node",
    "postgresql", "postgres", "rest api", "full stack", "fullstack",
    "full-stack", "frontend", "front-end", "front end", "backend", "back-end",
    "back end", "software engineer", "software developer", "web developer",
    "desarrollador", "programador", "ingeniero de software", "developer",
]
BONUS_KEYWORDS = [
    "remote", "remoto", "colombia", "latam", "latin america", "americas", "worldwide",
    "spanish", "español", "git", "github", "automation", "automatizaci",
    "react native", "next.js", "nextjs", "tailwind", "html", "css", "api", "postman",
]

# --- Enfoque junior / menos ruido -----------------------------------------
HIDE_SENIOR = True     # oculta vacantes claramente senior (ponlo en False para verlas)
JUNIOR_TERMS = [
    "junior", "jr", "entry", "entry-level", "entry level", "trainee",
    "graduate", "intern", "pasant", "early career", "associate", "semi senior", "semi-senior",
]
SENIOR_TERMS = [
    "senior", "sr.", "sr ", "staff", "principal", "lead", "head of",
    "manager", "director", "architect", "vp ",
    "5+ years", "6+ years", "7+ years", "8+ years", "10+ years",
]
JUNIOR_BOOST = 4       # puntos extra si la vacante es junior/entry
SENIOR_PENALTY = 6     # puntos menos si es senior (cuando HIDE_SENIOR = False)

# --- Filtro de ubicación ---------------------------------------------------
HIDE_FOREIGN_ONSITE = True   # oculta vacantes PRESENCIALES en otro país (no remotas y no Colombia)
COLOMBIA_TERMS = [
    "colombia", "colombie", "neiva", "huila", "bogotá", "bogota", "medellín", "medellin",
    "cali", "barranquilla", "cartagena", "bucaramanga", "pereira", "manizales",
    "cúcuta", "cucuta", "ibagué", "ibague", "villavicencio", "santa marta", "armenia",
]

# --- Frescura (aplicar temprano = más chances) -----------------------------
MAX_AGE_DAYS = 21      # descarta vacantes más viejas que esto (0 = no filtrar)
FRESH_BOOST = 3        # puntos extra si se publicó hace menos de 2 días

# --- Vacantes sospechosas (solo avisa, no las oculta) ----------------------
SUSPICIOUS_TERMS = [
    "confidencial", "empresa confidencial", "importante empresa del sector",
    "ingresos ilimitados", "sin experiencia necesaria", "gana desde casa",
    "inversión inicial", "inversion inicial", "multinivel", "network marketing",
    "solo comisión", "solo comision", "100% comisión", "100% comision",
    "reclutamiento", "headhunt", "staffing", "consultora de talento", "temporal services",
]

# --- Coach de CV: qué skills piden en el mercado ---------------------------
# Lo que YA tienes (no aparecerá como "te falta")
MY_SKILLS = [
    "react", "typescript", "javascript", "python", "fastapi", "postgresql", "postgres",
    "sql", "rest", "api", "git", "github", "html", "css", "node", "postman",
]
# Vocabulario que se busca en las vacantes para detectar tus vacíos
SKILL_VOCAB = [
    "docker", "kubernetes", "aws", "azure", "gcp", "django", "flask", "express",
    "next.js", "nestjs", "graphql", "redis", "mongodb", "mysql", ".net", "c#",
    "java", "spring", "php", "laravel", "angular", "vue", "svelte", "tailwind",
    "redux", "jest", "cypress", "ci/cd", "github actions", "jenkins", "terraform",
    "linux", "microservicios", "microservices", "kafka", "rabbitmq", "elasticsearch",
    "scrum", "agile", "react native", "flutter", "power bi", "etl", "pandas",
    "machine learning", "openai", "langchain", "websockets", "kotlin", "swift",
]

# --- Comportamiento --------------------------------------------------------
MIN_SCORE = 3          # puntaje mínimo por keywords para considerar una vacante
MAX_PER_RUN = 20       # máximo de ofertas nuevas por corrida (anti-spam)
FIRST_RUN_TOP = 10     # en la 1ª corrida, cuántas de las mejores enviarte
MAX_SEEN = 4000        # cuántos IDs recordar para no repetir
QUIET_START, QUIET_END = 21, 7   # entre 9 p.m. y 7 a.m. (Colombia) llega sin sonido

# --- Matching con IA (Groq) -----------------------------------------------
AI_ENABLED = True                       # necesita el secret GROQ_API_KEY
GROQ_MODEL = "llama-3.3-70b-versatile"  # si Groq lo deprecia, cámbialo aquí
AI_SCORE_TOP = 12   # cuántas de las mejores (por keywords) pasan a la IA por corrida
AI_MIN_FIT = 50     # si la IA da un encaje menor a esto, no te la manda (0 = enviar todas)
