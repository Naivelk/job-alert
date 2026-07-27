# 🤖 Job Alert Bot

Bot que busca vacantes que encajan con tu perfil (Full Stack / React / Python / FastAPI),
las **puntúa con IA leyendo tu CV**, te escribe un **borrador para aplicar** y te las manda
por **Telegram**. Corre solo en **GitHub Actions** cada 8 horas — sin tu PC prendida.

Busca en fuentes **gratis y legales** (nada de scrapear LinkedIn/Computrabajo):

| Fuente | Qué trae | Key |
|---|---|---|
| **RemoteOK** | Remoto global (tech) | — |
| **Remotive** | Remoto global (software-dev) | — |
| **We Work Remotely** | Full-stack / back / front remoto | — |
| **Arbeitnow** | Remoto + Europa | — |
| **Himalayas** | Remoto global (con seniority) | — |
| **Jobicy** | Remoto global (marca geo LATAM) | — |
| **Jooble** | Colombia (Neiva + remoto CO) | `JOOBLE_API_KEY` |
| **Careerjet** | Agregador Colombia | `CAREERJET_AFFID` |
| **Google Jobs** (SerpApi) | LinkedIn / Computrabajo / Indeed vía Google | `SERPAPI_KEY` |

> 🧠 **Matching con IA (Groq):** con `GROQ_API_KEY`, la IA lee tu `perfil.md` + cada vacante,
> te da un **% de encaje**, una razón y un **borrador de mensaje** para aplicar. Sin la key,
> el bot igual funciona con el ranking por palabras clave.

---

## 🔑 Secrets (en GitHub → Settings → Secrets and variables → Actions)

| Secret | ¿Para qué? | Cómo obtenerlo |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | mandarte los avisos | @BotFather → `/newbot` |
| `TELEGRAM_CHAT_ID` | a quién avisar | @userinfobot |
| `GROQ_API_KEY` | matching con IA + borradores | gratis en <https://console.groq.com/keys> |
| `JOOBLE_API_KEY` | vacantes Colombia | gratis en <https://jooble.org/api/about> |
| `CAREERJET_AFFID` | agregador Colombia | gratis en <https://www.careerjet.com/partners/> |
| `SERPAPI_KEY` | Google Jobs (LinkedIn/Computrabajo) | gratis (100/mes) en <https://serpapi.com/> |

Los 2 primeros son **obligatorios**; el resto son opcionales — el bot omite la fuente si falta su key.

Enlace directo para agregarlos: <https://github.com/Naivelk/job-alert/settings/secrets/actions/new>

---

## 🚀 Encenderlo
GitHub → pestaña **Actions** → **Job Alert Bot** → **Run workflow**.
En la 1ª corrida te llegan las **10 mejores** vacantes. Después corre solo cada 8h.

---

## ⚙️ Ajustar a tu gusto (`config.py`)
- **`STRONG_KEYWORDS` / `BONUS_KEYWORDS`** → tus tecnologías/roles.
- **`HIDE_SENIOR`** → `True` oculta vacantes senior/lead/principal (ideal early-career). Ponlo en `False` para verlas.
- **`HIDE_FOREIGN_ONSITE`** → `True` oculta vacantes presenciales en otro país (deja pasar remotas y las de Colombia).
- **`MIN_SCORE`** → súbelo si quieres menos ofertas, más precisas.
- **`AI_MIN_FIT`** → % mínimo de encaje IA para avisarte (baja el ruido).
- **`AI_SCORE_TOP`** → cuántas vacantes pasa a la IA por corrida (controla el gasto).
- **`GROQ_MODEL`** → si Groq deprecia el modelo, cámbialo aquí.
- **`*_QUERIES`** → qué buscar en Jooble / Careerjet / Google Jobs.
- **Frecuencia** → el `cron` en `.github/workflows/job-alert.yml`.
- **Tu CV** → edita `perfil.md` (la IA lo usa como contexto).

## 📁 Estructura
```
job-alert/
├── job_bot.py          # lógica: dedup, filtros, IA, Telegram
├── sources.py          # fetchers de cada bolsa de empleo
├── ai_match.py         # matching con IA (Groq)
├── weekly_summary.py   # resumen semanal
├── config.py           # tu perfil y ajustes  ← edita aquí
├── perfil.md           # tu CV resumido (contexto para la IA)
├── seen.json           # memoria de ofertas ya enviadas (se actualiza sola)
├── stats.json          # métricas de la semana (se actualiza sola)
├── requirements.txt
└── .github/workflows/
    ├── job-alert.yml   # búsqueda cada 8h
    └── weekly.yml      # resumen semanal (lunes)
```

## 📧 Alertas nativas de LinkedIn y Computrabajo (recomendado, 0 código)
Además del bot, activa las alertas **oficiales** de estas plataformas — son gratis, legales
y te llegan al correo. Cubren lo que el bot no alcanza a ver:

**LinkedIn**
1. Entra a **Jobs** (Empleos) y busca tu rol, ej. *"Desarrollador Full Stack"*, ubicación *Colombia* (o *Remoto*).
2. Activa el interruptor **"Crear alerta de empleo"** (Job alert) → elige frecuencia (diaria).
3. Bonus: en tu perfil activa **"Open to work"** (visible solo para reclutadores).

**Computrabajo**
1. Crea tu cuenta en computrabajo.com.co y busca tu rol + ciudad.
2. En los resultados, dale a **"Crear alerta"** → te llegan las nuevas por email.

## 📝 Notas
- El bot **no aplica por ti** ni scrapea LinkedIn/Computrabajo (eso viola sus términos y
  arriesga tu cuenta). Te trae las vacantes — incluidas las de LinkedIn/Computrabajo vía
  Google Jobs — para que **tú apliques**, que es lo que sí funciona.
- Respeta los términos de las APIs (enlaza de vuelta a la fuente, uso personal).
- `perfil.md` no incluye tu teléfono a propósito (el repo es público).
