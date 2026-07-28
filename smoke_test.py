# ============================================================================
#  SMOKE TEST  —  prueba la lógica pura del bot SIN llamar a ninguna API.
#  Corre solo en cada push (.github/workflows/ci.yml). Si algo se rompe,
#  te enteras antes de que el bot falle en una corrida real.
# ============================================================================
import time

import job_bot as jb

fails = []


def check(name, got, want):
    if got != want:
        fails.append(f"{name}: esperaba {want!r}, obtuvo {got!r}")


def check_true(name, cond):
    if not cond:
        fails.append(name)


# --- Fechas: cada fuente manda un formato distinto -------------------------
now = time.time()
check_true("epoch int (Arbeitnow/Himalayas)", abs(jb.parse_ts(1785096257) - 1785096257) < 1)
check_true("epoch string", abs(jb.parse_ts("1785096257") - 1785096257) < 1)
check_true("ISO con zona (RemoteOK)", jb.parse_ts("2026-07-26T20:04:17+00:00") is not None)
check_true("ISO sin zona (Jobicy)", jb.parse_ts("2026-07-27 08:40:02") is not None)
check_true("ISO fracción larga (Jooble)", jb.parse_ts("2026-07-26T00:00:00.0000000") is not None)
check_true("RFC 2822 (Careerjet/RSS)", jb.parse_ts("Sun, 26 Jul 2026 22:59:36 GMT") is not None)
check_true("relativo español (Google Jobs)", abs(jb.parse_ts("hace 3 días") - (now - 3 * 86400)) < 60)
check_true("relativo inglés", abs(jb.parse_ts("2 days ago") - (now - 2 * 86400)) < 60)
check("fecha vacía", jb.parse_ts(""), None)
check("fecha basura", jb.parse_ts("no soy fecha"), None)

# --- Frescura --------------------------------------------------------------
fresh = {"date": now - 3600}
old = {"date": now - 10 * 86400}
check_true("etiqueta fresca", "🔥" in jb.age_label(fresh))
check_true("etiqueta vieja", "días" in jb.age_label(old))
check("sin fecha no muestra etiqueta", jb.age_label({"date": ""}), "")

# --- Coach de CV: el bug de java/javascript --------------------------------
js_job = [{"title": "Frontend Developer", "tags": ["javascript", "react"],
           "company": "X", "location": "Remote", "snippet": "", "level": ""}]
check_true("'java' NO debe contarse en una vacante de javascript",
           "java" not in jb.collect_skills(js_job))

java_job = [{"title": "Backend Java Developer", "tags": ["java", "spring"],
             "company": "X", "location": "Bogotá", "snippet": "", "level": ""}]
check_true("'java' sí se cuenta cuando es Java de verdad",
           "java" in jb.collect_skills(java_job))

docker_job = [{"title": "Dev", "tags": [], "company": "X", "location": "Remote",
               "snippet": "Experiencia con Docker y AWS", "level": ""}]
sk = jb.collect_skills(docker_job)
check_true("detecta docker", "docker" in sk)
check_true("detecta aws", "aws" in sk)

mine = [{"title": "React Developer", "tags": ["react", "python"], "company": "X",
         "location": "Remote", "snippet": "", "level": ""}]
check_true("no sugiere lo que ya sabes", "react" not in jb.collect_skills(mine))

# --- Filtro de ubicación ---------------------------------------------------
check_true("acepta Colombia", jb.location_ok({"title": "Dev", "location": "Bogotá", "tags": []}))
check_true("acepta Neiva", jb.location_ok({"title": "Dev", "location": "Neiva, Huila", "tags": []}))
check_true("acepta remoto", jb.location_ok({"title": "Dev", "location": "Remote", "tags": []}))
check_true("acepta LATAM", jb.location_ok({"title": "Dev", "location": "LATAM remote", "tags": []}))
check_true("rechaza presencial extranjero",
           not jb.location_ok({"title": "Dev", "location": "Poland", "tags": []}))

# --- Vacantes sospechosas --------------------------------------------------
check_true("marca empresa confidencial",
           jb.suspicious_reason({"title": "Dev", "company": "Confidencial",
                                 "location": "", "tags": [], "snippet": "", "level": ""}))
check_true("marca empresa vacía",
           jb.suspicious_reason({"title": "Dev", "company": "", "location": "",
                                 "tags": [], "snippet": "", "level": ""}))
check("no marca una vacante normal",
      jb.suspicious_reason({"title": "Dev", "company": "BairesDev", "location": "Remote",
                            "tags": ["react"], "snippet": "", "level": ""}), "")

# --- Render de la tarjeta --------------------------------------------------
job = {"id": "x:1", "title": "Full-Stack Dev <script>", "company": "BairesDev",
       "location": "Remote LATAM", "tags": ["python", "react"], "url": "https://ex.com",
       "source": "Google Jobs (LinkedIn)", "date": now - 7200, "salary": "USD 3k–4k/mes",
       "snippet": "", "level": ""}
ai = {"fit": 90, "reason": "Encaja con tu stack", "dm": "Hola, me interesa",
      "email_subject": "Postulación", "email_body": "Estimado equipo..."}
card = jb.format_job(job, 12, ai)
check_true("muestra el %", "90% compatible contigo" in card)
check_true("muestra la barra", "█" in card)
check_true("muestra veredicto", "Excelente para ti" in card)
check_true("muestra frescura", "🔥" in card)
check_true("muestra salario", "USD 3k" in card)
check_true("muestra modalidad LATAM", "Remoto (LATAM)" in card)
check_true("incluye los 2 borradores", "Mensaje corto" in card and "Correo formal" in card)
check_true("escapa HTML peligroso", "<script>" not in card)
check_true("no rompe el largo de Telegram", len(card) < 4096)

card_sin_ia = jb.format_job(job, 12, None)
check_true("funciona sin IA", "Relevancia" in card_sin_ia)

# --- Dedup y puntaje -------------------------------------------------------
check("normaliza para dedup", jb._norm("Mid Fullstack Developer (Bogotá)"),
      jb._norm("Mid Fullstack Developer"))
check_true("puntúa una vacante de tu stack",
           jb.score_job({"title": "Full Stack Developer React Python", "tags": [],
                         "company": "", "location": "Remote", "snippet": ""}) > 0)
check("ignora vacantes fuera de tu perfil",
      jb.score_job({"title": "Enfermera jefe", "tags": [], "company": "",
                    "location": "Neiva", "snippet": ""}), 0)

# --- Seniority -------------------------------------------------------------
jr, sr = jb.seniority_flags({"title": "Junior Developer", "level": ""})
check_true("detecta junior", jr and not sr)
jr, sr = jb.seniority_flags({"title": "Senior Staff Engineer", "level": ""})
check_true("detecta senior", sr)

# --- Resultado -------------------------------------------------------------
if fails:
    print("❌ FALLARON estas pruebas:")
    for f in fails:
        print("  -", f)
    raise SystemExit(1)
print("✅ Todas las pruebas pasaron.")
