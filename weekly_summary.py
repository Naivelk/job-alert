# ============================================================================
#  RESUMEN SEMANAL  —  métricas de la semana, coach de CV (qué skills te piden)
#  y tus postulaciones. Lo dispara .github/workflows/weekly.yml (lunes).
# ============================================================================
import os

import job_bot as jb


def build_message(st):
    found = st.get("found", 0)
    sent = st.get("sent", 0)
    fits = st.get("fits", [])
    avg = round(sum(fits) / len(fits)) if fits else 0
    by_src = st.get("by_source", {})
    top = st.get("top", [])
    applied = st.get("applied", [])

    lines = ["📊 <b>Tu resumen semanal de búsqueda</b>", ""]
    lines.append(f"🔎 Vacantes revisadas: <b>{found}</b>")
    lines.append(f"📨 Enviadas a ti: <b>{sent}</b>")
    lines.append(f"🎯 Compatibilidad promedio: <b>{avg}%</b>")
    lines.append(f"✅ Postulaciones registradas: <b>{len(applied)}</b>")
    if by_src:
        top_src = sorted(by_src.items(), key=lambda x: x[1], reverse=True)[:4]
        lines.append("📡 Fuentes top: " + ", ".join(f"{k} ({v})" for k, v in top_src))

    # --- Coach de CV -------------------------------------------------------
    skills = st.get("skills", {})
    total = st.get("skill_jobs", 0)
    if skills and total >= 10:
        ranked = sorted(skills.items(), key=lambda x: x[1], reverse=True)[:5]
        lines.append("")
        lines.append("🎓 <b>Coach de CV — lo que más te piden y no tienes:</b>")
        for skill, n in ranked:
            pct = round(n * 100 / total)
            if pct < 5:
                continue
            lines.append(f"• <b>{jb.esc(skill)}</b> — en el {pct}% de las vacantes que te encajan")
        lines.append("<i>Aprender la primera de la lista es tu mayor palanca ahora mismo.</i>")

    if top:
        lines.append("")
        lines.append("🏆 <b>Mejores matches de la semana:</b>")
        for t in top[:5]:
            lines.append(
                f'• <a href="{jb.esc(t.get("url", ""))}">{jb.esc(t.get("title", ""))}</a>'
                f' — {t.get("fit", 0)}% · {jb.esc(t.get("company", "—"))}'
            )

    if applied:
        lines.append("")
        lines.append(f"💪 Aplicaste a <b>{len(applied)}</b> esta semana. ¡Sigue así, Kevin!")
    else:
        lines.append("")
        lines.append("💡 <i>Meta de esta semana: aplicar al menos a 5. "
                     "Responde «apliqué» a una vacante para llevar la cuenta.</i>")
    return "\n".join(lines)


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("Faltan TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID")
        return

    st = jb.load_stats()
    jb.read_replies(token, st)   # cuenta las postulaciones de última hora

    if not st.get("found") and not st.get("sent"):
        jb.send_telegram(token, chat_id,
                         "📊 <b>Resumen semanal</b>\nEsta semana no hubo vacantes nuevas. "
                         "¡El bot sigue atento! 💪")
    else:
        jb.send_telegram(token, chat_id, build_message(st))

    # Reinicia la semana, pero conserva el offset de Telegram
    jb.save_stats({"tg_offset": st.get("tg_offset", 0)})


if __name__ == "__main__":
    main()
