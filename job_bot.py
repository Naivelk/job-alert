# ============================================================================
#  BOT DE EMPLEOS  —  busca vacantes que encajan con tu perfil, las puntúa con
#  IA (Groq) y te avisa por Telegram. Corre en GitHub Actions cada 8h.
# ============================================================================
import html as _html
import json
import os
import re
import sys
import time
import traceback

import requests

import ai_match
import config as cfg
import sources

STATE_FILE = "seen.json"


def _norm(s):
    """Normaliza título/empresa para deduplicar (quita paréntesis y puntuación)."""
    s = re.sub(r"\([^)]*\)", " ", str(s).lower())
    s = re.sub(r"[^0-9a-záéíóúüñ ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# --- Estado (para no repetir ofertas) --------------------------------------
def load_seen():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_seen(seen):
    data = list(seen)[-cfg.MAX_SEEN:]
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def load_cv():
    for fn in ("perfil.md", "cv.txt", "cv.md"):
        try:
            with open(fn, encoding="utf-8") as f:
                return f.read()
        except Exception:
            continue
    return ""


# --- Recolección -----------------------------------------------------------
def gather_jobs():
    jobs = []
    if cfg.ENABLE_REMOTEOK:
        jobs += sources.fetch_remoteok()
    if cfg.ENABLE_REMOTIVE:
        jobs += sources.fetch_remotive()
    if cfg.ENABLE_WWR:
        jobs += sources.fetch_wwr()
    if cfg.ENABLE_ARBEITNOW:
        jobs += sources.fetch_arbeitnow()
    if cfg.ENABLE_HIMALAYAS:
        jobs += sources.fetch_himalayas()
    if cfg.ENABLE_JOBICY:
        jobs += sources.fetch_jobicy(cfg.JOBICY_TAGS)
    if cfg.ENABLE_JOOBLE:
        jobs += sources.fetch_jooble(os.environ.get("JOOBLE_API_KEY", "").strip(), cfg.JOOBLE_QUERIES)
    if cfg.ENABLE_CAREERJET:
        jobs += sources.fetch_careerjet(os.environ.get("CAREERJET_AFFID", "").strip(), cfg.CAREERJET_QUERIES)
    if cfg.ENABLE_SERPAPI:
        jobs += sources.fetch_serpapi(os.environ.get("SERPAPI_KEY", "").strip(), cfg.SERPAPI_QUERIES)

    # Quita duplicados: por id y por (título, empresa) entre fuentes distintas
    by_id, seen_keys, out = {}, set(), []
    for j in jobs:
        if not j.get("id") or j["id"] in by_id:
            continue
        by_id[j["id"]] = j
        key = (_norm(j.get("title", "")), _norm(j.get("company", "")))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        out.append(j)
    return out


# --- Puntaje / relevancia --------------------------------------------------
def score_job(job):
    title = job.get("title", "").lower()
    tagtext = " ".join(job.get("tags", [])).lower()
    rest = f"{job.get('company','')} {job.get('location','')} {job.get('snippet','')}".lower()

    score, strong_hit = 0, False
    for kw in cfg.STRONG_KEYWORDS:
        k = kw.lower()
        pts = (3 if k in title else 0) + (2 if k in tagtext else 0) + (1 if k in rest else 0)
        if pts:
            score += pts
            strong_hit = True
    if not strong_hit:
        return 0
    for kw in cfg.BONUS_KEYWORDS:
        k = kw.lower()
        if k in title or k in tagtext or k in rest:
            score += 1
    return score


def seniority_flags(job):
    text = (job.get("title", "") + " " + job.get("level", "")).lower()
    is_junior = any(t in text for t in cfg.JUNIOR_TERMS)
    is_senior = any(t in text for t in cfg.SENIOR_TERMS)
    return is_junior, is_senior


def build_scored(all_jobs):
    scored = []
    for job in all_jobs:
        s = score_job(job)
        if s <= 0:
            continue
        is_jr, is_sr = seniority_flags(job)
        if cfg.HIDE_SENIOR and is_sr and not is_jr:
            continue
        if is_jr:
            s += cfg.JUNIOR_BOOST
        elif is_sr:
            s -= cfg.SENIOR_PENALTY
        if s >= cfg.MIN_SCORE:
            scored.append((job, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


# --- Telegram --------------------------------------------------------------
def esc(s):
    return _html.escape(str(s or ""))


def format_job(job, score, ai=None):
    tags = ", ".join(job.get("tags", [])[:6])
    lines = [
        f"🆕 <b>{esc(job['title'])}</b>",
        f"🏢 {esc(job['company'] or '—')}   📍 {esc(job['location'] or '—')}",
    ]
    if tags:
        lines.append(f"🏷 {esc(tags)}")
    if ai:
        lines.append(f"🎯 <b>Encaje IA: {ai['fit']}%</b> — {esc(ai['reason'])}")
    else:
        lines.append(f"⭐ Match: {score}")
    lines.append(f"<i>vía {esc(job['source'])}</i>")
    lines.append(f'🔗 <a href="{esc(job["url"])}">Ver / Aplicar</a>')
    if ai and ai.get("message"):
        lines.append(f"✍️ <i>Borrador:</i> {esc(ai['message'])}")
    return "\n".join(lines)


def send_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": chat_id, "text": text,
            "parse_mode": "HTML", "disable_web_page_preview": True,
        }, timeout=30)
        if r.status_code != 200:
            print(f"[telegram] {r.status_code}: {r.text[:300]}")
        return r.status_code == 200
    except Exception as e:
        print(f"[telegram] error: {e}")
        return False


def send_batches(token, chat_id, header, blocks):
    """Agrupa las ofertas en mensajes por debajo del límite de Telegram (4096)."""
    chunks, cur, cur_len = [], [], 0
    for block in blocks:
        b = block + "\n\n"
        if cur and cur_len + len(b) > 3500:
            chunks.append("".join(cur))
            cur, cur_len = [], 0
        cur.append(b)
        cur_len += len(b)
    if cur:
        chunks.append("".join(cur))

    for i, ch in enumerate(chunks):
        msg = (header + "\n\n" + ch) if i == 0 else ch
        send_telegram(token, chat_id, msg.strip())
        time.sleep(1)   # respeta el rate limit de Telegram


# --- Lógica principal ------------------------------------------------------
def run(token, chat_id):
    seen = load_seen()
    first_run = len(seen) == 0

    all_jobs = gather_jobs()
    print(f"Recolectadas {len(all_jobs)} ofertas (sin duplicados).")
    if not all_jobs:
        send_telegram(token, chat_id,
                      "⚠️ <b>Aviso:</b> ninguna fuente devolvió ofertas esta vez. "
                      "Puede ser algo temporal; reviso en la próxima corrida.")
        return

    scored = build_scored(all_jobs)
    print(f"{len(scored)} pasan el filtro (score >= {cfg.MIN_SCORE}, junior-friendly).")

    new = [(j, s) for (j, s) in scored if j["id"] not in seen]

    # Marca TODO lo recolectado como visto (aunque no pase el filtro)
    for j in all_jobs:
        seen.add(j["id"])

    if not new:
        print("No hay ofertas nuevas.")
        save_seen(seen)
        return

    # --- IA: puntúa las mejores por keywords -------------------------------
    ai_map = {}
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if cfg.AI_ENABLED and groq_key:
        top_for_ai = [j for (j, _s) in new[:cfg.AI_SCORE_TOP]]
        cv_text = load_cv()
        ai_map = ai_match.score_with_ai(cv_text, top_for_ai, cfg.GROQ_MODEL, groq_key)
        print(f"IA puntuó {len(ai_map)} vacantes.")

    # Reordena: primero por encaje de IA (si hay), luego por score de keywords
    def rank_key(item):
        j, s = item
        a = ai_map.get(j["id"])
        return (a["fit"] if a else -1, s)

    new.sort(key=rank_key, reverse=True)

    # Filtra por encaje mínimo de IA (solo a las que la IA evaluó)
    final = []
    for (j, s) in new:
        a = ai_map.get(j["id"])
        if a and cfg.AI_MIN_FIT and a["fit"] < cfg.AI_MIN_FIT:
            continue
        final.append((j, s, a))

    limit = cfg.FIRST_RUN_TOP if first_run else cfg.MAX_PER_RUN
    to_send = final[:limit]
    extra = len(final) - len(to_send)

    if first_run:
        header = (
            "🤖 <b>Bot de Empleos activado</b> ✅\n"
            f"Encontré <b>{len(final)}</b> vacantes que encajan contigo. "
            f"Aquí van las <b>{len(to_send)}</b> mejores para arrancar:"
        )
    else:
        header = f"🔔 <b>{len(final)} vacante(s) nueva(s)</b> para tu perfil:"
        if extra > 0:
            header += f"\n<i>(mostrando las {len(to_send)} mejores; +{extra} guardadas)</i>"

    blocks = [format_job(j, s, a) for (j, s, a) in to_send]
    send_batches(token, chat_id, header, blocks)
    print(f"Enviadas {len(to_send)} ofertas.")
    save_seen(seen)


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("ERROR: faltan los secrets TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
        sys.exit(1)
    try:
        run(token, chat_id)
    except Exception as e:
        print(traceback.format_exc())
        send_telegram(token, chat_id,
                      "⚠️ <b>El bot de empleos falló</b>\n"
                      f"<code>{esc(str(e))[:500]}</code>")
        sys.exit(1)


if __name__ == "__main__":
    main()
