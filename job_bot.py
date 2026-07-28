# ============================================================================
#  BOT DE EMPLEOS  —  busca vacantes que encajan con tu perfil, las puntúa con
#  IA (Groq) y te avisa por Telegram. Corre en GitHub Actions 3 veces al día.
# ============================================================================
import email.utils
import html as _html
import json
import os
import re
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone

import requests

import ai_match
import config as cfg
import sources

STATE_FILE = "seen.json"
STATS_FILE = "stats.json"

COL_TZ = timezone(timedelta(hours=-5))   # Colombia (UTC-5, sin horario de verano)

_REMOTE_WORDS = ["remote", "remoto", "anywhere", "worldwide", "distributed",
                 "virtual", "teletrabajo", "home office", "en casa"]


def _norm(s):
    """Normaliza título/empresa para deduplicar (quita paréntesis y puntuación)."""
    s = re.sub(r"\([^)]*\)", " ", str(s).lower())
    s = re.sub(r"[^0-9a-záéíóúüñ ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# --- Fechas / frescura -----------------------------------------------------
_REL_RE = re.compile(r"hace\s+(\d+)\s*(minuto|hora|d[ií]a|semana|mes)", re.I)
_REL_EN_RE = re.compile(r"(\d+)\s*(minute|hour|day|week|month)s?\s+ago", re.I)
_UNIT_SECONDS = {"minuto": 60, "hora": 3600, "dia": 86400, "día": 86400,
                 "semana": 604800, "mes": 2592000, "minute": 60, "hour": 3600,
                 "day": 86400, "week": 604800, "month": 2592000}


def parse_ts(value):
    """Convierte la fecha de cualquier fuente a epoch (segundos). None si no se puede."""
    if value in (None, ""):
        return None
    now = time.time()

    # 1) epoch numérico (Arbeitnow, Himalayas, RemoteOK)
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if s.isdigit():
        return float(s)

    # 2) texto relativo: "hace 3 días" / "3 days ago" (Google Jobs)
    m = _REL_RE.search(s) or _REL_EN_RE.search(s)
    if m:
        unit = m.group(2).lower()
        return now - int(m.group(1)) * _UNIT_SECONDS.get(unit, 86400)
    if re.search(r"\b(hoy|today|just posted|reci[eé]n)\b", s, re.I):
        return now

    # 3) ISO 8601 (recorta fracciones de más de 6 dígitos, ej. Jooble)
    iso = re.sub(r"(\.\d{6})\d+", r"\1", s).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(iso)
        return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).timestamp()
    except ValueError:
        pass

    # 4) RFC 2822 (feeds RSS, Careerjet)
    try:
        dt = email.utils.parsedate_to_datetime(s)
        return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).timestamp()
    except (TypeError, ValueError):
        return None


def age_hours(job):
    ts = parse_ts(job.get("date"))
    if ts is None:
        return None
    return max(0.0, (time.time() - ts) / 3600)


def age_label(job):
    h = age_hours(job)
    if h is None:
        return ""
    if h < 1:
        return "🔥 Publicada hace minutos"
    if h < 24:
        return f"🔥 Publicada hace {int(h)} h"
    d = int(h // 24)
    if d == 1:
        return "🔥 Publicada ayer"
    if d <= 7:
        return f"🕒 Publicada hace {d} días"
    return f"⏳ Publicada hace {d} días"


# --- Estado ----------------------------------------------------------------
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


def load_stats():
    try:
        with open(STATS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_stats(st):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False)


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


# --- Puntaje / filtros -----------------------------------------------------
def job_text(job):
    return " ".join([job.get("title", ""), " ".join(job.get("tags", [])),
                     job.get("company", ""), job.get("location", ""),
                     job.get("snippet", ""), job.get("level", "")]).lower()


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


def location_ok(job):
    """False solo si es presencial en otro país (no remota y no Colombia)."""
    loc = (job.get("location", "") or "").lower()
    text = (loc + " " + job.get("title", "") + " " + " ".join(job.get("tags", []))).lower()
    if any(t in text for t in cfg.COLOMBIA_TERMS):
        return True
    if any(w in text for w in _REMOTE_WORDS):
        return True
    if not loc or loc in ("—", "remote"):
        return True
    return False


def suspicious_reason(job):
    """Devuelve el motivo si la vacante tiene señales de alerta, si no ''."""
    text = job_text(job)
    if not job.get("company"):
        return "no dice qué empresa es"
    for t in cfg.SUSPICIOUS_TERMS:
        if t in text:
            return f"menciona «{t}»"
    return ""


def build_scored(all_jobs):
    scored = []
    for job in all_jobs:
        s = score_job(job)
        if s <= 0:
            continue
        is_jr, is_sr = seniority_flags(job)
        if cfg.HIDE_SENIOR and is_sr and not is_jr:
            continue
        if cfg.HIDE_FOREIGN_ONSITE and not location_ok(job):
            continue

        h = age_hours(job)
        if h is not None:
            if cfg.MAX_AGE_DAYS and h > cfg.MAX_AGE_DAYS * 24:
                continue
            if h <= 48:
                s += cfg.FRESH_BOOST
            elif h <= 24 * 7:
                s += 1

        if is_jr:
            s += cfg.JUNIOR_BOOST
        elif is_sr:
            s -= cfg.SENIOR_PENALTY
        if s >= cfg.MIN_SCORE:
            scored.append((job, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


# --- Coach de CV: qué piden las vacantes que no tienes ---------------------
def collect_skills(jobs):
    counts = {}
    my = [m.lower() for m in cfg.MY_SKILLS]
    for job in jobs:
        text = job_text(job)
        for skill in cfg.SKILL_VOCAB:
            k = skill.lower()
            if k in my:
                continue
            # Los límites evitan falsos positivos como "java" dentro de "javascript"
            if re.search(r"(?<![a-z0-9+#.])" + re.escape(k) + r"(?![a-z0-9])", text):
                counts[skill] = counts.get(skill, 0) + 1
    return counts


# --- Telegram --------------------------------------------------------------
def esc(s):
    return _html.escape(str(s or ""))


def _bar(pct):
    """Barra visual de 10 bloques, ej. 90% -> █████████░"""
    filled = max(0, min(10, round(pct / 10)))
    return "█" * filled + "░" * (10 - filled)


def _verdict(pct):
    if pct >= 80:
        return "🟢", "Excelente para ti"
    if pct >= 65:
        return "🟢", "Muy compatible"
    if pct >= 50:
        return "🟡", "Compatible (con peros)"
    return "🟠", "Encaje parcial"


def _modality(job):
    text = job_text(job)
    if any(w in text for w in ["hybrid", "híbrido", "hibrido"]):
        return "🏠 Híbrido"
    if any(w in text for w in _REMOTE_WORDS):
        if any(w in text for w in ["latam", "latin america", "americas"]):
            return "💻 Remoto (LATAM)"
        return "💻 Remoto"
    return ""


def format_job(job, score, ai=None):
    line2 = f"🏢 {esc(job.get('company') or '—')}   📍 {esc(job.get('location') or '—')}"
    mod = _modality(job)
    if mod:
        line2 += f"   ·   {mod}"
    lines = [f"🆕 <b>{esc(job['title'])}</b>", line2]

    age = age_label(job)
    if age:
        lines.append(age)
    lines.append("")

    if ai:
        emoji, verdict = _verdict(ai["fit"])
        lines.append(f"{emoji} <b>{verdict} · {ai['fit']}% compatible contigo</b>")
        lines.append(f"<code>{_bar(ai['fit'])}</code>")
        if ai.get("reason"):
            lines.append(f"💬 <b>Por qué:</b> {esc(ai['reason'])}")
    else:
        lines.append(f"⭐ <b>Relevancia:</b> {score} (por palabras clave)")

    if job.get("salary"):
        lines.append(f"💵 {esc(job['salary'])}")

    warn = suspicious_reason(job)
    if warn:
        lines.append(f"⚠️ <b>Ojo:</b> {esc(warn)}. Verifica antes de dar datos personales.")

    lines.append(f"🔎 <i>vía {esc(job['source'])}</i>")
    lines.append(f'🔗 <a href="{esc(job["url"])}">Abrir vacante / Postularme</a>')

    if ai and (ai.get("dm") or ai.get("email_body")):
        lines.append("")
        if ai.get("dm"):
            lines.append("✍️ <b>Mensaje corto</b> (LinkedIn/DM):")
            lines.append(f"<blockquote expandable>{esc(ai['dm'])}</blockquote>")
        if ai.get("email_body"):
            subj = ai.get("email_subject", "")
            body = (f"Asunto: {subj}\n\n" if subj else "") + ai["email_body"]
            lines.append("📧 <b>Correo formal</b>:")
            lines.append(f"<blockquote expandable>{esc(body)}</blockquote>")
    return "\n".join(lines)


def is_quiet_now():
    hour = datetime.now(COL_TZ).hour
    start, end = cfg.QUIET_START, cfg.QUIET_END
    return hour >= start or hour < end


def send_telegram(token, chat_id, text, silent=None):
    if silent is None:
        silent = is_quiet_now()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": chat_id, "text": text,
            "parse_mode": "HTML", "disable_web_page_preview": True,
            "disable_notification": bool(silent),
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


# --- Registro de postulaciones (lee tus respuestas en Telegram) ------------
_APPLIED_RE = re.compile(r"apliqu|postul|applied|✅|👍", re.I)


def read_replies(token, st):
    """Cuenta los mensajes tuyos que dicen que aplicaste. Devuelve cuántos nuevos."""
    offset = st.get("tg_offset", 0)
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates",
                         params={"offset": offset + 1, "timeout": 0}, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[telegram] getUpdates error: {e}")
        return 0

    applied = st.get("applied", [])
    count = 0
    for upd in data.get("result", []):
        st["tg_offset"] = max(st.get("tg_offset", 0), upd.get("update_id", 0))
        msg = upd.get("message") or {}
        text = msg.get("text", "") or ""
        if not _APPLIED_RE.search(text):
            continue
        # Si respondió citando una vacante, guarda su título
        quoted = (msg.get("reply_to_message") or {}).get("text", "")
        title = ""
        for line in quoted.split("\n"):
            line = line.strip()
            if line and not line.startswith(("🏢", "📍", "🔥", "🕒", "⏳")):
                title = line.lstrip("🆕 ").strip()
                break
        applied.append({"title": title or text[:60], "at": int(time.time())})
        count += 1
    st["applied"] = applied[-100:]
    return count


# --- Estadísticas ----------------------------------------------------------
def update_stats(st, all_jobs, sent_items, relevant_jobs):
    st["runs"] = st.get("runs", 0) + 1
    st["found"] = st.get("found", 0) + len(all_jobs)
    st["sent"] = st.get("sent", 0) + len(sent_items)

    by_src = st.get("by_source", {})
    fits = st.get("fits", [])
    top = st.get("top", [])
    for (j, s, a) in sent_items:
        src = j.get("source", "?").split("·")[0].split(" (")[0].strip()
        by_src[src] = by_src.get(src, 0) + 1
        if a:
            fits.append(a["fit"])
            top.append({"title": j.get("title", ""), "company": j.get("company", ""),
                        "fit": a["fit"], "url": j.get("url", "")})
    top.sort(key=lambda x: x.get("fit", 0), reverse=True)
    seen_k, uniq = set(), []
    for t in top:
        k = (t.get("title", "").lower(), t.get("company", "").lower())
        if k in seen_k:
            continue
        seen_k.add(k)
        uniq.append(t)

    # Coach de CV: qué skills piden las vacantes que te encajan
    skills = st.get("skills", {})
    for skill, n in collect_skills(relevant_jobs).items():
        skills[skill] = skills.get(skill, 0) + n
    st["skills"] = skills
    st["skill_jobs"] = st.get("skill_jobs", 0) + len(relevant_jobs)

    st["by_source"] = by_src
    st["fits"] = fits[-300:]
    st["top"] = uniq[:8]


# --- Lógica principal ------------------------------------------------------
def run(token, chat_id):
    seen = load_seen()
    st = load_stats()
    first_run = len(seen) == 0

    n_applied = read_replies(token, st)
    if n_applied:
        print(f"Registradas {n_applied} postulaciones nuevas.")

    all_jobs = gather_jobs()
    print(f"Recolectadas {len(all_jobs)} ofertas (sin duplicados).")
    if not all_jobs:
        send_telegram(token, chat_id,
                      "⚠️ <b>Aviso:</b> ninguna fuente devolvió ofertas esta vez. "
                      "Puede ser algo temporal; reviso en la próxima corrida.")
        save_stats(st)
        return

    scored = build_scored(all_jobs)
    relevant = [j for (j, _s) in scored]
    print(f"{len(scored)} pasan los filtros (score, junior, ubicación, frescura).")

    new = [(j, s) for (j, s) in scored if j["id"] not in seen]
    for j in all_jobs:
        seen.add(j["id"])

    if not new:
        print("No hay ofertas nuevas.")
        update_stats(st, all_jobs, [], relevant)
        save_stats(st)
        save_seen(seen)
        return

    # --- IA: puntúa las mejores por keywords -------------------------------
    ai_map = {}
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if cfg.AI_ENABLED and groq_key:
        top_for_ai = [j for (j, _s) in new[:cfg.AI_SCORE_TOP]]
        ai_map = ai_match.score_with_ai(load_cv(), top_for_ai, cfg.GROQ_MODEL, groq_key)
        print(f"IA puntuó {len(ai_map)} vacantes.")

    def rank_key(item):
        j, s = item
        a = ai_map.get(j["id"])
        return (a["fit"] if a else -1, s)

    new.sort(key=rank_key, reverse=True)

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
            f"Aquí van las <b>{len(to_send)}</b> mejores:\n\n"
            "📊 El <b>% compatible</b> = qué tanto encaja la vacante con tu CV (lo calcula la IA).\n"
            "💡 Cuando apliques a una, <b>respóndele «apliqué»</b> a ese mensaje y llevo la cuenta."
        )
    else:
        header = f"🔔 <b>{len(final)} vacante(s) nueva(s)</b> para ti"
        if extra > 0:
            header += f"  <i>(top {len(to_send)}; +{extra} guardadas)</i>"
        header += "\n<i>El % = compatibilidad con tu CV. Responde «apliqué» a la que apliques.</i>"

    blocks = [format_job(j, s, a) for (j, s, a) in to_send]
    send_batches(token, chat_id, header, blocks)
    print(f"Enviadas {len(to_send)} ofertas.")

    update_stats(st, all_jobs, to_send, relevant)
    save_stats(st)
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
                      f"<code>{esc(str(e))[:500]}</code>", silent=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
