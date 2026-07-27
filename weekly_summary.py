# ============================================================================
#  RESUMEN SEMANAL  —  envía por Telegram un resumen de la semana y reinicia
#  las estadísticas. Lo dispara .github/workflows/weekly.yml (lunes).
# ============================================================================
import json
import os

import job_bot  # reutiliza send_telegram() y esc()

STATS_FILE = "stats.json"


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("Faltan TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID")
        return

    try:
        with open(STATS_FILE, encoding="utf-8") as f:
            st = json.load(f)
    except Exception:
        st = {}

    found = st.get("found", 0)
    sent = st.get("sent", 0)
    fits = st.get("fits", [])
    avg = round(sum(fits) / len(fits)) if fits else 0
    by_src = st.get("by_source", {})
    top = st.get("top", [])

    if not sent and not found:
        job_bot.send_telegram(token, chat_id,
                              "📊 <b>Resumen semanal</b>\nEsta semana no hubo vacantes nuevas. "
                              "¡El bot sigue atento! 💪")
        _reset()
        return

    lines = ["📊 <b>Tu resumen semanal de búsqueda</b>\n"]
    lines.append(f"🔎 Vacantes revisadas: <b>{found}</b>")
    lines.append(f"📨 Enviadas a ti: <b>{sent}</b>")
    lines.append(f"🎯 Compatibilidad promedio: <b>{avg}%</b>")
    if by_src:
        top_src = sorted(by_src.items(), key=lambda x: x[1], reverse=True)[:4]
        lines.append("📡 Fuentes top: " + ", ".join(f"{k} ({v})" for k, v in top_src))
    if top:
        lines.append("\n🏆 <b>Mejores matches de la semana:</b>")
        for t in top[:5]:
            lines.append(
                f'• <a href="{job_bot.esc(t.get("url", ""))}">{job_bot.esc(t.get("title", ""))}</a>'
                f' — {t.get("fit", 0)}% · {job_bot.esc(t.get("company", "—"))}'
            )
    lines.append("\n💪 ¡A seguir aplicando! Suerte esta semana, Kevin.")

    job_bot.send_telegram(token, chat_id, "\n".join(lines))
    _reset()


def _reset():
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)


if __name__ == "__main__":
    main()
