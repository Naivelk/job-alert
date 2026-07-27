# ============================================================================
#  FUENTES DE EMPLEO  —  cada función devuelve una lista de ofertas normalizadas
# ============================================================================
#  Formato normalizado de cada oferta (dict):
#    id, title, company, location, tags(list), url, source, date, snippet, level
# ============================================================================
import hashlib
import html
import re

import feedparser
import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept": "application/json"}
RSS_HEADERS = {"User-Agent": UA}   # los feeds RSS no quieren Accept: application/json
TIMEOUT = 25


def _clean(text):
    """Quita etiquetas HTML, decodifica entidades y colapsa espacios."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(text))
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _short(s):
    """Hash corto para IDs largos (ej. Google Jobs job_id)."""
    return hashlib.md5(str(s).encode("utf-8", "ignore")).hexdigest()[:16]


# ---------------------------------------------------------------------------
def fetch_remoteok():
    jobs = []
    try:
        r = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[remoteok] error: {e}")
        return jobs
    for item in data:
        if not isinstance(item, dict) or "position" not in item:
            continue  # el 1er elemento es un aviso legal/metadata
        slug = item.get("slug", "")
        url = item.get("url") or (f"https://remoteok.com/remote-jobs/{slug}" if slug else "https://remoteok.com")
        jobs.append({
            "id": f"remoteok:{item.get('id', slug)}",
            "title": _clean(item.get("position", "")),
            "company": _clean(item.get("company", "")),
            "location": _clean(item.get("location", "")) or "Remote",
            "tags": [str(t) for t in item.get("tags", []) if t],
            "url": url,
            "source": "RemoteOK",
            "date": item.get("date", ""),
            "snippet": "",
            "level": "",
        })
    return jobs


# ---------------------------------------------------------------------------
def fetch_remotive():
    jobs = []
    try:
        r = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"category": "software-dev"},
            headers=HEADERS, timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[remotive] error: {e}")
        return jobs
    for item in data.get("jobs", []):
        jobs.append({
            "id": f"remotive:{item.get('id')}",
            "title": _clean(item.get("title", "")),
            "company": _clean(item.get("company_name", "")),
            "location": _clean(item.get("candidate_required_location", "")) or "Remote",
            "tags": [str(t) for t in item.get("tags", []) if t],
            "url": item.get("url", ""),
            "source": "Remotive",
            "date": item.get("publication_date", ""),
            "snippet": "",
            "level": "",
        })
    return jobs


# ---------------------------------------------------------------------------
WWR_FEEDS = [
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss",
]


def fetch_wwr():
    jobs = []
    for feed_url in WWR_FEEDS:
        try:
            parsed = feedparser.parse(feed_url, request_headers=RSS_HEADERS)
        except Exception as e:
            print(f"[wwr] error {feed_url}: {e}")
            continue
        for e in parsed.entries:
            title = _clean(e.get("title", ""))
            company, sep, position = title.partition(":")   # WWR usa "Empresa: Puesto"
            region = _clean(e.get("region", "")) or "Remote"
            skills = _clean(e.get("skills", ""))
            tags = [s.strip() for s in re.split(r"[,/]", skills) if s.strip()]
            jobs.append({
                "id": f"wwr:{e.get('id') or e.get('link')}",
                "title": position.strip() if sep else title,
                "company": company.strip() if sep else "",
                "location": region,
                "tags": tags,
                "url": e.get("link", ""),
                "source": "WeWorkRemotely",
                "date": e.get("published", ""),
                "snippet": "",
                "level": "",
            })
    return jobs


# ---------------------------------------------------------------------------
def fetch_arbeitnow():
    jobs = []
    try:
        r = requests.get("https://www.arbeitnow.com/api/job-board-api",
                         headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[arbeitnow] error: {e}")
        return jobs
    for item in data.get("data", []):
        loc = _clean(item.get("location", ""))
        if item.get("remote"):
            loc = (loc + " · Remote").strip(" ·")
        tags = [str(t) for t in item.get("tags", []) if t]
        tags += [str(t) for t in item.get("job_types", []) if t]
        jobs.append({
            "id": f"arbeitnow:{item.get('slug')}",
            "title": _clean(item.get("title", "")),
            "company": _clean(item.get("company_name", "")),
            "location": loc or "—",
            "tags": tags,
            "url": item.get("url", ""),
            "source": "Arbeitnow",
            "date": item.get("created_at", ""),
            "snippet": "",
            "level": "",
        })
    return jobs


# ---------------------------------------------------------------------------
def fetch_himalayas(limit=50):
    jobs = []
    try:
        r = requests.get("https://himalayas.app/jobs/api",
                         params={"limit": limit}, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[himalayas] error: {e}")
        return jobs
    for it in data.get("jobs", []):
        locs = it.get("locationRestrictions") or []
        seniority = it.get("seniority") or []
        jobs.append({
            "id": f"himalayas:{it.get('guid') or it.get('applicationLink')}",
            "title": _clean(it.get("title", "")),
            "company": _clean(it.get("companyName", "")),
            "location": ", ".join(str(x) for x in locs) if locs else "Remote",
            "tags": [str(c) for c in (it.get("categories") or [])][:8],
            "url": it.get("applicationLink") or it.get("guid") or "",
            "source": "Himalayas",
            "date": "",
            "snippet": _clean(it.get("excerpt", "")),
            "level": ", ".join(str(x) for x in seniority),
        })
    return jobs


# ---------------------------------------------------------------------------
def fetch_jobicy(tags):
    jobs = []
    for tag in tags:
        try:
            r = requests.get("https://jobicy.com/api/v2/remote-jobs",
                             params={"count": 20, "tag": tag},
                             headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[jobicy] error ({tag}): {e}")
            continue
        for it in data.get("jobs", []):
            industry = [str(x) for x in (it.get("jobIndustry") or [])]
            jtype = [str(x) for x in (it.get("jobType") or [])]
            jobs.append({
                "id": f"jobicy:{it.get('id')}",
                "title": _clean(it.get("jobTitle", "")),
                "company": _clean(it.get("companyName", "")),
                "location": _clean(it.get("jobGeo", "")) or "Remote",
                "tags": industry + jtype,
                "url": it.get("url", ""),
                "source": "Jobicy",
                "date": it.get("pubDate", ""),
                "snippet": "",
                "level": str(it.get("jobLevel", "")),
            })
    return jobs


# ---------------------------------------------------------------------------
def fetch_jooble(api_key, queries):
    """Colombia. Solo corre si hay api_key (secret JOOBLE_API_KEY)."""
    jobs = []
    if not api_key:
        return jobs
    for kw, loc in queries:
        try:
            r = requests.post(
                f"https://jooble.org/api/{api_key}",
                json={"keywords": kw, "location": loc},
                headers={"Content-Type": "application/json", "User-Agent": UA},
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[jooble] error ({kw} / {loc}): {e}")
            continue
        for item in data.get("jobs", []):
            src = item.get("source", "")
            jobs.append({
                "id": f"jooble:{item.get('id') or item.get('link')}",
                "title": _clean(item.get("title", "")),
                "company": _clean(item.get("company", "")),
                "location": _clean(item.get("location", "")),
                "tags": [],
                "url": item.get("link", ""),
                "source": f"Jooble·{src}" if src else "Jooble",
                "date": item.get("updated", ""),
                "snippet": _clean(item.get("snippet", "")),
                "level": "",
            })
    return jobs


# ---------------------------------------------------------------------------
def fetch_careerjet(affid, queries):
    """Agregador (Colombia). Solo corre si hay affid (secret CAREERJET_AFFID)."""
    jobs = []
    if not affid:
        return jobs
    for kw, loc, locale in queries:
        try:
            r = requests.get(
                "http://public.api.careerjet.net/search",
                params={
                    "affid": affid, "keywords": kw, "location": loc,
                    "locale_code": locale, "pagesize": 20, "page": 1,
                    "sort": "date", "user_ip": "11.22.33.44", "user_agent": UA,
                },
                headers={"User-Agent": UA, "Referer": "https://github.com/Naivelk/job-alert"},
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[careerjet] error ({kw} / {loc}): {e}")
            continue
        for it in data.get("jobs", []):
            jobs.append({
                "id": f"careerjet:{_short(it.get('url', ''))}",
                "title": _clean(it.get("title", "")),
                "company": _clean(it.get("company", "")),
                "location": _clean(it.get("locations", "")),
                "tags": [],
                "url": it.get("url", ""),
                "source": "Careerjet",
                "date": it.get("date", ""),
                "snippet": _clean(it.get("description", "")),
                "level": "",
            })
    return jobs


# ---------------------------------------------------------------------------
def fetch_serpapi(api_key, queries):
    """Google Jobs (surfacea LinkedIn/Computrabajo/Indeed). Necesita SERPAPI_KEY."""
    jobs = []
    if not api_key:
        return jobs
    for q, loc in queries:
        try:
            r = requests.get(
                "https://serpapi.com/search.json",
                params={
                    "engine": "google_jobs", "q": q, "location": loc,
                    "hl": "es", "gl": "co", "api_key": api_key,
                },
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[serpapi] error ({q} / {loc}): {e}")
            continue
        for it in data.get("jobs_results", []):
            opts = it.get("apply_options") or []
            link = (opts[0].get("link") if opts else "") or it.get("share_link", "")
            via = it.get("via", "")
            jobs.append({
                "id": f"serpapi:{_short(it.get('job_id') or it.get('title', ''))}",
                "title": _clean(it.get("title", "")),
                "company": _clean(it.get("company_name", "")),
                "location": _clean(it.get("location", "")),
                "tags": [],
                "url": link,
                "source": f"Google Jobs ({via})" if via else "Google Jobs",
                "date": "",
                "snippet": _clean(it.get("description", ""))[:400],
                "level": "",
            })
    return jobs
