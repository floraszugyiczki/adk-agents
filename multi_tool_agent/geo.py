import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"


def geocode(place: str) -> dict | None:
    """Resolve 'Paris' or 'Paris, Texas' / 'Paris, France' to a location record."""
    parts = [p.strip() for p in place.split(",") if p.strip()]
    if not parts:
        return None
    resp = requests.get(
        GEOCODE_URL,
        params={"name": parts[0], "count": 10, "language": "en"},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json().get("results") or []
    if not results:
        return None
    hints = [h.lower() for h in parts[1:]]
    if hints:
        for r in results:
            fields = {str(r.get(k, "")).lower() for k in ("country", "country_code", "admin1")}
            if any(h in fields for h in hints):
                return r
    return results[0]


def label(place: dict) -> str:
    """Readable name: 'Paris, Île-de-France, France'."""
    parts = [place.get("name"), place.get("admin1"), place.get("country")]
    return ", ".join(p for p in parts if p)