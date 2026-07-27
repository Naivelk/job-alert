# ============================================================================
#  BOT DE EMPLEOS  —  busca vacantes que encajan con tu perfil y te avisa por
#  Telegram. Corre solo en GitHub Actions (ver .github/workflows/job-alert.yml)
# ============================================================================
import html as _html
import json
import os
import sys
import time

import requests

import config as cfg
import sources

STATE_FILE = "seen.json"


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
    if cfg.ENABLE_JOOBLE:
        key = os.environ.get("JOOBLE_API_KEY", "").strip()
        jobs += sources.fetch_jooble(key, cfg.JOOBLE_QUERIES)
    # Quita duplicados dentro de esta corrida (misma oferta en varias fuentes)
    uniq = {}
    for j in jobs:
        if j.get("id"):
            uniq[j["id"]] = j
    return list(uniq.values())


# --- Puntaje / relevancia --------------------------------------------------
def score_job(job):
    title = job.get("title", "").lower()
    tagtext = " ".join(job.get("tags", [])).lower()
    rest = f"{job.get('company','')} {job.get('location','')} {job.get('snippet','')}".lower()

    score = 0
    strong_hit = False
    for kw in cfg.STRONG_KEYWORDS:
        k = kw.lower()
        pts = 0
        if k in title:
            pts += 3
        if k in tagtext:
            pts += 2
        if k in rest:
            pts += 1
        if pts:
            score += pts
            strong_hit = True

    if not strong_hit:
        return 0  # sin ninguna palabra fuerte -> no es para tu perfil

    for kw in cfg.BONUS_KEYWORDS:
        k = kw.lower()
        if k in title or k in tagtext or k in rest:
            score += 1
    return score


# --- Telegram --------------------------------------------------------------
def esc(s):
    return _html.escape(str(s or ""))


def format_job(job, score):
    tags = ", ".join(job.get("tags", [])[:6])
    lines = [
        f"🆕 <b>{esc(job['title'])}</b>",
        f"🏢 {esc(job['company'] or '—')}   📍 {esc(job['location'] or '—')}",
    ]
    if tags:
        lines.append(f"🏷 {esc(tags)}")
    lines.append(f"⭐ Match: {score}   ·   <i>vía {esc(job['source'])}</i>")
    lines.append(f'🔗 <a href="{esc(job["url"])}">Ver / Aplicar</a>')
    return "\n".join(lines)


def send_telegram(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
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
        time.sleep(1)  # respeta el rate limit de Telegram


# --- Principal -------------------------------------------------------------
def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("ERROR: faltan los secrets TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
        sys.exit(1)

    seen = load_seen()
    first_run = len(seen) == 0

    all_jobs = gather_jobs()
    print(f"Recolectadas {len(all_jobs)} ofertas de todas las fuentes.")

    scored = []
    for job in all_jobs:
        s = score_job(job)
        if s >= cfg.MIN_SCORE:
            scored.append((job, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    print(f"{len(scored)} pasan el filtro (score >= {cfg.MIN_SCORE}).")

    new = [(j, s) for (j, s) in scored if j["id"] not in seen]

    # Marca TODO lo recolectado como visto (aunque no pase el filtro), para no re-evaluarlo.
    for j in all_jobs:
        seen.add(j["id"])

    if not new:
        print("No hay ofertas nuevas.")
        save_seen(seen)
        return

    has_jooble = bool(os.environ.get("JOOBLE_API_KEY", "").strip())
    if first_run:
        top = new[:cfg.FIRST_RUN_TOP]
        header = (
            "🤖 <b>Bot de Empleos activado</b> ✅\n"
            "Monitoreando RemoteOK · Remotive · WeWorkRemotely · Arbeitnow"
            + (" · Jooble" if has_jooble else "")
            + f".\nAquí van las <b>{len(top)}</b> mejores para arrancar:"
        )
        blocks = [format_job(j, s) for (j, s) in top]
        send_batches(token, chat_id, header, blocks)
        print(f"1ª corrida: enviadas {len(top)}; {len(new) - len(top)} marcadas como vistas.")
    else:
        to_send = new[:cfg.MAX_PER_RUN]
        extra = len(new) - len(to_send)
        header = f"🔔 <b>{len(new)} vacante(s) nueva(s)</b> para tu perfil:"
        if extra > 0:
            header += f"\n<i>(mostrando las {len(to_send)} mejores; +{extra} quedaron guardadas)</i>"
        blocks = [format_job(j, s) for (j, s) in to_send]
        send_batches(token, chat_id, header, blocks)
        print(f"Enviadas {len(to_send)} ofertas nuevas.")

    save_seen(seen)


if __name__ == "__main__":
    main()
