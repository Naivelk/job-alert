# 🤖 Job Alert Bot

Bot que busca vacantes que encajan con tu perfil (Full Stack / React / Python / FastAPI)
y te las manda por **Telegram**. Corre solo en **GitHub Actions** cada 6 horas —
no necesitas tu PC prendida ni instalar Python.

Busca en fuentes **gratis y legales** (nada de scrapear LinkedIn):

| Fuente | Qué trae | Necesita key |
|---|---|---|
| **RemoteOK** | Remoto global (tech) | No |
| **Remotive** | Remoto global (software-dev) | No |
| **We Work Remotely** | Full-stack / back / front remoto | No |
| **Arbeitnow** | Remoto + Europa | No |
| **Jooble** | Colombia (Neiva + remoto CO) | Sí (gratis, opcional) |

---

## 🚀 Puesta en marcha (una sola vez, ~10 min)

### 1) Sube esta carpeta a un repo de GitHub
```bash
cd job-alert
git init
git add .
git commit -m "feat: bot de empleos"
git branch -M main
git remote add origin https://github.com/Naivelk/job-alert.git
git push -u origin main
```
(Primero crea el repo vacío `job-alert` en GitHub.)

### 2) Crea tu bot de Telegram
1. En Telegram, abre **@BotFather** → escribe `/newbot` → dale un nombre.
2. Te dará un **TOKEN** parecido a `8123456789:AAH...`. Guárdalo.
3. **Escríbele algo a tu bot** (dale a "Start" / manda "hola"). Importante para el paso 3.

### 3) Consigue tu CHAT_ID
- La forma fácil: en Telegram abre **@userinfobot** y te dice tu `Id` (un número).
- (Alternativa: entra a `https://api.telegram.org/bot<TU_TOKEN>/getUpdates` en el navegador
  después de escribirle al bot, y busca `"chat":{"id":...}`.)

### 4) Guarda los secrets en GitHub
En tu repo → **Settings → Secrets and variables → Actions → New repository secret**.
Crea estos:

| Nombre | Valor |
|---|---|
| `TELEGRAM_BOT_TOKEN` | el token de BotFather |
| `TELEGRAM_CHAT_ID` | tu chat id |
| `JOOBLE_API_KEY` | *(opcional)* tu key de Jooble — ver abajo |

### 5) Enciéndelo
En tu repo → pestaña **Actions** → activa los workflows si te lo pide →
elige **"Job Alert Bot"** → **Run workflow**.

En la 1ª corrida te llegan las **10 mejores** ofertas para arrancar. Después,
cada 6 horas solo te avisa de las **nuevas**.

---

## 🇨🇴 (Opcional) Activar vacantes de Colombia con Jooble
1. Pide tu key gratis en <https://jooble.org/api/about> (registro rápido).
2. Agrégala como secret `JOOBLE_API_KEY` (paso 4).
Sin este key el bot igual funciona; solo omite Jooble.

---

## ⚙️ Ajustar a tu gusto (`config.py`)
- **`STRONG_KEYWORDS` / `BONUS_KEYWORDS`** → tus tecnologías/roles. Cambia el ranking.
- **`MIN_SCORE`** → súbelo (ej. 5) si quieres menos ofertas pero más precisas.
- **`MAX_PER_RUN`** → tope de ofertas por corrida (anti-spam).
- **`JOOBLE_QUERIES`** → qué buscar en Colombia.
- Cambiar la frecuencia: edita el `cron` en `.github/workflows/job-alert.yml`.

## 📁 Estructura
```
job-alert/
├── job_bot.py        # lógica principal (dedup, ranking, Telegram)
├── sources.py        # fetchers de cada bolsa de empleo
├── config.py         # tu perfil y ajustes  ← edita aquí
├── seen.json         # memoria de ofertas ya enviadas (se actualiza sola)
├── requirements.txt
└── .github/workflows/job-alert.yml   # el cron de GitHub Actions
```

## 📝 Notas
- El bot **no aplica por ti** (eso viola los términos de LinkedIn y te puede costar la cuenta).
  Te manda las ofertas para que **tú apliques** con tu toque humano — que es lo que sí funciona.
- Respeta los términos de las APIs: enlaza de vuelta a la fuente y uso personal.
- GitHub desactiva los cron si el repo lleva 60 días sin actividad; con las corridas
  automáticas eso no pasa, pero si lo pausas, reactívalo desde la pestaña Actions.
