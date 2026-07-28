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
> te da un **% de compatibilidad**, la razón y **2 borradores** (mensaje corto y correo formal).
> Sin la key, el bot igual funciona con el ranking por palabras clave.

### ✨ Qué más hace
- 🔥 **Frescura:** muestra hace cuánto se publicó, prioriza las de menos de 48 h y descarta las de más de 21 días (aplicar temprano = más chances).
- 🎓 **Coach de CV:** en el resumen semanal te dice qué skills piden más las vacantes que te encajan y **no tienes** (ej. *"Docker: en el 60%"*) — tu guía de qué aprender.
- ✅ **Registro de postulaciones:** responde **«apliqué»** a una vacante en Telegram y el bot lleva la cuenta.
- 🌍 **Filtro de ubicación:** oculta presenciales en otro país (deja remotas y Colombia).
- ⚠️ **Detector de sospechosas:** marca empresas confidenciales, intermediarias o con señales de estafa.
- 🌙 **Horario humano:** corre 7 a.m. / 12 m. / 6 p.m. (Colombia) y de noche llega sin sonido.
- 🧪 **CI:** `smoke_test.py` valida la lógica en cada push.

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
- **`MAX_AGE_DAYS`** → antigüedad máxima de una vacante (21 días). `FRESH_BOOST` prioriza las recién publicadas.
- **`QUIET_START` / `QUIET_END`** → franja en que los avisos llegan sin sonido (9 p.m.–7 a.m.).
- **`MY_SKILLS` / `SKILL_VOCAB`** → alimentan el coach de CV (qué te falta según el mercado).
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
├── weekly_summary.py   # resumen semanal + coach de CV
├── panel.py            # genera el panel web (docs/index.html)
├── matches.json        # historial de vacantes para el panel (se actualiza solo)
├── smoke_test.py       # pruebas de la lógica (corren en CI)
├── config.py           # tu perfil y ajustes  ← edita aquí
├── perfil.md           # tu CV resumido (contexto para la IA)
├── seen.json           # memoria de ofertas ya enviadas (se actualiza sola)
├── stats.json          # métricas de la semana (se actualiza sola)
├── requirements.txt
└── .github/workflows/
    ├── job-alert.yml   # búsqueda 7am / 12m / 6pm (Colombia)
    ├── weekly.yml      # resumen semanal (lunes 8am)
    └── ci.yml          # pruebas en cada push
```

## 🖥️ Panel web (GitHub Pages)
El bot genera `docs/index.html` con todas tus vacantes: buscador, filtro por %,
estado (aplicada / pendiente), orden, modo oscuro y responsive.

**Actívalo una sola vez:** repo → **Settings → Pages** → *Source:* **Deploy from a branch**
→ rama **main**, carpeta **/docs** → **Save**.

Queda en 👉 **https://naivelk.github.io/job-alert/** y se actualiza en cada corrida.

> El botón **"Marcar como aplicada"** abre Telegram con el mensaje ya escrito: un clic y el
> bot registra la postulación. Nunca editas la tabla a mano. (Detectar por sí solo que
> aplicaste en LinkedIn no es posible sin acceder a tus cuentas, así que no se hace.)

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
