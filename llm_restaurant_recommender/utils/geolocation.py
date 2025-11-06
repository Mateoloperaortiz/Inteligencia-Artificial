import requests
import pandas as pd
from geopy.geocoders import Nominatim
from math import radians, cos, sin, asin, sqrt

OVERPASS_URL = "http://overpass-api.de/api/interpreter"

geolocator = Nominatim(user_agent="llm_restaurant_recommender")


def geocode_location(place: str):
    """Return (lat, lon) for a text place using Nominatim or None."""
    try:
        loc = geolocator.geocode(place)
        if not loc:
            return None
        return (loc.latitude, loc.longitude)
    except Exception:
        return None


def haversine(lat1, lon1, lat2, lon2):
    # distance in meters
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    R = 6371000
    return R * c


def search_restaurants_overpass(lat, lon, radius=1500, cuisine=None, max_results=50):
    """Query Overpass for restaurants near lat,lon within radius (meters). Returns DataFrame."""
    # Build Overpass QL
    cuisine_filter = ''
    if cuisine:
        cuisine_filter = f'["cuisine"~"{cuisine}",i]'

    query = f"""
[out:json][timeout:25];
(
  node["amenity"="restaurant"]{cuisine_filter}(around:{radius},{lat},{lon});
  way["amenity"="restaurant"]{cuisine_filter}(around:{radius},{lat},{lon});
  relation["amenity"="restaurant"]{cuisine_filter}(around:{radius},{lat},{lon});
);
out center {max_results};
""".replace("{cuisine_filter}", cuisine_filter).strip()

    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        # Return empty DataFrame on error
        return pd.DataFrame()

    elements = data.get("elements", [])
    rows = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("operator") or ""
        cuisine_tag = tags.get("cuisine", "").split(';')[0] if tags.get("cuisine") else ""
        if el.get("type") == "node":
            rlat = el.get("lat")
            rlon = el.get("lon")
        else:
            center = el.get("center") or {}
            rlat = center.get("lat")
            rlon = center.get("lon")
        if rlat is None or rlon is None:
            continue
        dist = haversine(lat, lon, rlat, rlon)
        rows.append({"id": el.get("id"), "name": name, "lat": rlat, "lon": rlon, "cuisine": cuisine_tag, "tags": tags, "distance_m": int(dist)})

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.sort_values(by=["distance_m"]).reset_index(drop=True)
    return df
