# ============================================================================
#  MATCHING CON IA (Groq)  —  lee tu CV + cada vacante y devuelve:
#    fit (0-100), reason (por qué encaja) y message (borrador para aplicar)
# ============================================================================
#  Usa la API de Groq (compatible con OpenAI). Gratis con tu GROQ_API_KEY.
#  Si no hay key o algo falla, devuelve {} y el bot sigue con el ranking normal.
# ============================================================================
import json

import requests

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def score_with_ai(cv_text, jobs, model, api_key, timeout=60):
    """Devuelve dict {job_id: {"fit": int, "reason": str, "message": str}}."""
    if not api_key or not jobs:
        return {}

    listing = []
    for i, j in enumerate(jobs):
        listing.append({
            "i": i,
            "title": j.get("title", ""),
            "company": j.get("company", ""),
            "location": j.get("location", ""),
            "level": j.get("level", ""),
            "tags": ", ".join(j.get("tags", [])[:8]),
            "desc": (j.get("snippet", "") or "")[:400],
        })

    system = (
        "Eres un asistente experto en búsqueda de empleo tech. Evalúas qué tan bien "
        "encaja cada vacante con el CV del candidato. Respondes SOLO con JSON válido."
    )
    user = (
        f"CV DEL CANDIDATO:\n{cv_text[:3500]}\n\n"
        f"VACANTES (JSON):\n{json.dumps(listing, ensure_ascii=False)}\n\n"
        "Para CADA vacante devuelve un objeto con:\n"
        "- i: el índice de la vacante\n"
        "- fit: entero 0-100 según el encaje REAL con el CV (stack, seniority, "
        "ubicación/remoto; penaliza roles senior o fuera de su stack)\n"
        "- reason: 1 frase corta en español de por qué encaja (o no)\n"
        "- message: borrador breve (máx 55 palabras, 2-3 frases) para aplicar, en PRIMERA "
        "persona y en el MISMO idioma de la vacante (español o inglés). Personalízalo: "
        "menciona 1 tecnología o requisito concreto de esa vacante y conéctalo con una "
        "fortaleza o proyecto real del CV. Varía el inicio en cada una, suena natural y "
        "humano, y evita frases cliché repetidas como 'candidato sólido' o 'dispuesto a aprender'.\n"
        'Responde EXACTAMENTE con este formato: '
        '{"results":[{"i":0,"fit":85,"reason":"...","message":"..."}]}'
    )

    try:
        r = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
            },
            timeout=timeout,
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
    except Exception as e:
        print(f"[ai] error: {e}")
        return {}

    out = {}
    for item in data.get("results", []):
        try:
            job = jobs[int(item["i"])]
            out[job["id"]] = {
                "fit": max(0, min(100, int(item.get("fit", 0)))),
                "reason": str(item.get("reason", "")).strip(),
                "message": str(item.get("message", "")).strip(),
            }
        except (ValueError, KeyError, IndexError, TypeError):
            continue
    return out
