import json
import re
from datetime import date
from pathlib import Path
import time
import requests
from backend.tools.geo import geocode

API_URL = "https://en.wikivoyage.org/w/api.php"
USER_AGENT = USER_AGENT = "adk-weather-assistant/1.0 (student project; szuflora@gmail.com)"
CACHE_DIR = Path(__file__).resolve().parents[3] / "data" / "activities"
MAX_PER_TYPE = 25      # listings kept per type ("see" / "do") in the cache
MIN_LISTINGS = 6       # fewer than this on the city page: also read district pages
MAX_DISTRICTS = 3
DESCRIPTION_CHARS = 220

def _api(**params) -> dict:
    params.update({"format": "json", "formatversion": 2, "redirects": 1})
    for attempt in range(4):
        resp = requests.get(API_URL, params=params, headers={"User-Agent": USER_AGENT}, timeout=10)
        if resp.status_code == 429:
            try:
                wait = int(resp.headers.get("Retry-After", 2 ** (attempt + 1)))
            except ValueError:
                wait = 2 ** (attempt + 1)
            time.sleep(min(wait, 20))
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()  # still 429 after the retries
    return {}

def _page_sections(page: str) -> dict:
    """Whole page in ONE request; returns {level-2 heading (lowercase): its wikitext}."""
    data = _api(action="parse", page=page, prop="wikitext")
    if "error" in data:
        return {}
    text = data["parse"]["wikitext"]
    parts = re.split(r"^==\s*([^=\n][^\n]*?)\s*==\s*$", text, flags=re.M)
    return {parts[i].strip().lower(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def _clean(text: str) -> str:
    """Remove wiki markup from a listing text."""
    text = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>|<[^>]+>", "", text, flags=re.S)
    for _ in range(3):  # simple nested templates, innermost first
        text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", text)   # [[a|b]] -> b
    text = re.sub(r"\[https?://\S+\s+([^\]]+)\]", r"\1", text)      # [url text] -> text
    text = re.sub(r"\[https?://\S+\]", "", text)
    text = text.replace("'''", "").replace("''", "")
    return " ".join(text.split())


def _listings(wikitext: str, kind: str) -> list[dict]:
    """Parse {{see|...}} or {{do|...}} templates into dicts."""
    out, pos = [], 0
    opener = re.compile(r"\{\{\s*" + kind + r"\s*\|", re.I)
    while True:
        m = opener.search(wikitext, pos)
        if not m:
            break
        j, depth_t, depth_l, cur, fields = m.end(), 1, 0, [], []
        while j < len(wikitext):
            two = wikitext[j:j + 2]
            if two == "{{":
                depth_t += 1; cur.append(two); j += 2; continue
            if two == "}}":
                depth_t -= 1
                if depth_t == 0:
                    break
                cur.append(two); j += 2; continue
            if two == "[[":
                depth_l += 1; cur.append(two); j += 2; continue
            if two == "]]":
                depth_l -= 1; cur.append(two); j += 2; continue
            if wikitext[j] == "|" and depth_t == 1 and depth_l == 0:
                fields.append("".join(cur)); cur = []
            else:
                cur.append(wikitext[j])
            j += 1
        fields.append("".join(cur))
        pos = j + 2

        values = {}
        for f in fields:
            key, sep, value = f.partition("=")
            if sep and re.fullmatch(r"\s*[\w-]+\s*", key):
                values[key.strip().lower()] = value.strip()
        name = _clean(values.get("name") or values.get("alt") or "")
        if not name:
            continue
        item = {"name": name, "type": kind}
        desc = _clean(values.get("content", ""))
        if desc:
            item["description"] = desc[:DESCRIPTION_CHARS]
        for key in ("lat", "long"):
            try:
                item["latitude" if key == "lat" else "longitude"] = float(values[key])
            except (KeyError, ValueError):
                pass
        for key in ("url", "hours", "price"):
            value = _clean(values.get(key, ""))
            if value:
                item[key] = value
        out.append(item)
    return out


def _page_listings(page: str) -> dict:
    sections = _page_sections(page)
    return {kind: _listings(sections.get(kind, ""), kind) for kind in ("see", "do")}

def _district_pages(city: str) -> list[str]:
    data = _api(action="query", list="allpages", apprefix=f"{city}/", apnamespace=0, aplimit=MAX_DISTRICTS)
    return [p["title"] for p in data.get("query", {}).get("allpages", [])]


def get_city_activities(city: str, limit: int = 10) -> dict:
    """Gets things to see and things to do in a city from Wikivoyage (a travel guide).

    Use this to suggest real places and activities. Each listing has a name, a short
    description and often coordinates. The data is imported from Wikivoyage
    (CC BY-SA) and saved locally after the first request.

    Args:
        city (str): City name. Add a country or region to disambiguate,
            e.g. "Paris, Texas".
        limit (int): Maximum number of "see" and of "do" listings returned, 1 to 25. Defaults to 10.

    Returns:
        dict: status, lists 'see' and 'do' of listings (name, description, latitude,
            longitude, url), the source pages, or status and error_message.
    """
    limit = max(1, min(int(limit), MAX_PER_TYPE))
    try:
        place = geocode(city)
    except requests.RequestException as exc:
        return {"status": "error", "error_message": f"Geocoding request failed: {exc}"}
    if not place:
        return {"status": "error", "error_message": f"Could not find a place called '{city}'."}

    title, country = place["name"], place.get("country")
    slug = re.sub(r"[^a-z0-9]+", "_", f"{title}_{country}".lower()).strip("_")
    cache_file = CACHE_DIR / f"{slug}.json"
    if cache_file.exists():
        result = json.loads(cache_file.read_text(encoding="utf-8"))
    else:
        try:
            found = _page_listings(title)
            sources = ["https://en.wikivoyage.org/wiki/" + title.replace(" ", "_")]
            if len(found["see"]) + len(found["do"]) < MIN_LISTINGS:
                for district in _district_pages(title):
                    time.sleep(0.5)
                    extra = _page_listings(district)
                    for kind in ("see", "do"):
                        found[kind] += extra[kind]
                    sources.append("https://en.wikivoyage.org/wiki/" + district.replace(" ", "_"))
        except (requests.RequestException, KeyError, ValueError) as exc:
            return {"status": "error", "error_message": f"Wikivoyage request failed: {exc}"}
        result = {
            "status": "success", "city": title, "country": country,
            "see": found["see"][:MAX_PER_TYPE], "do": found["do"][:MAX_PER_TYPE],
            "sources": sources, "license": "Wikivoyage, CC BY-SA 4.0",
            "retrieved": date.today().isoformat(),
        }
        if result["see"] or result["do"]:  # do not cache an empty result
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    result = dict(result, see=result["see"][:limit], do=result["do"][:limit])
    result["report"] = (f"{title}, {country}: {len(result['see'])} sights and {len(result['do'])} activities "
                        f"from Wikivoyage." if result["see"] or result["do"]
                        else f"No sights or activities found on Wikivoyage for {title}.")
    return result

    result = dict(result, see=result["see"][:limit], do=result["do"][:limit])
    result["report"] = (f"{title}, {country}: {len(result['see'])} sights and {len(result['do'])} activities "
                        f"from Wikivoyage." if result["see"] or result["do"]
                        else f"No sights or activities found on Wikivoyage for {title}.")
    return result