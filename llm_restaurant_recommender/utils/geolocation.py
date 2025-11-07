import time
from typing import Tuple, Optional, Union

import requests
import pandas as pd
from geopy.geocoders import Nominatim

OVERPASS_URL = "http://overpass-api.de/api/interpreter"

_geolocator = Nominatim(user_agent="llm_restaurant_recommender")


def resolve_location(place_or_coords: Union[str, Tuple[float, float]]) -> Optional[Tuple[float, float]]:
    """Resolve a place name or return coordinates tuple.

    Args:
        place_or_coords: either a string with place name/address or a (lat, lon) tuple.

    Returns:
        (lat, lon) or None if resolution failed.
    """
    if not place_or_coords:
        return None

    # If already coordinates
    if isinstance(place_or_coords, (list, tuple)) and len(place_or_coords) == 2:
        try:
            lat = float(place_or_coords[0])
            lon = float(place_or_coords[1])
            return lat, lon
        except Exception:
            return None

    # Treat as string place name
    try:
        loc = _geolocator.geocode(str(place_or_coords), timeout=10)
        if loc:
            return float(loc.latitude), float(loc.longitude)
    except Exception:
        return None
    return None


def _build_address_from_tags(tags: dict) -> str:
    parts = []
    if not tags:
        return ""
    for key in ["addr:street", "addr:housenumber", "addr:postcode", "addr:city", "addr:neighbourhood"]:
        v = tags.get(key)
        if v:
            parts.append(str(v))
    return ", ".join(parts)


def search_restaurants(place_or_coords: Union[str, Tuple[float, float]], cuisine: Optional[str] = None, radius: int = 1500, timeout: int = 25, retries: int = 2) -> pd.DataFrame:
    """Query Overpass API for restaurants near a location.

    Args:
        place_or_coords: place name (str) or (lat, lon) tuple.
        cuisine: optional cuisine type (e.g., 'italiano'). If None, searches for generic restaurants.
        radius: search radius in meters.
        timeout: Overpass timeout in seconds.
        retries: number of retries on HTTP/network errors.

    Returns:
        pandas.DataFrame with columns: name, cuisine, lat, lon, address, opening_hours
    """
    coords = resolve_location(place_or_coords)
    if coords is None:
        # Unable to resolve location — return empty DataFrame with columns
        return pd.DataFrame(columns=["name", "cuisine", "lat", "lon", "address", "opening_hours"])

    lat, lon = coords

    # Build cuisine filter: if cuisine provided, filter by cuisine tag; otherwise search amenity=restaurant
    cuisine_filter = ""
    if cuisine:
        # match cuisine value or ingredient keywords
        cuisine_filter = f'["cuisine"~"{cuisine}",i]'

    # Overpass QL
    query = f"""
[out:json][timeout:{timeout}];
(
  node["amenity"="restaurant"]{cuisine_filter}(around:{radius},{lat},{lon});
  way["amenity"="restaurant"]{cuisine_filter}(around:{radius},{lat},{lon});
  relation["amenity"="restaurant"]{cuisine_filter}(around:{radius},{lat},{lon});
);
out center;
""".replace("{cuisine_filter}", cuisine_filter).strip()

    attempt = 0
    while attempt <= retries:
        try:
            resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=timeout + 5)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception:
            attempt += 1
            if attempt > retries:
                # return empty dataframe on persistent failure
                return pd.DataFrame(columns=["name", "cuisine", "lat", "lon", "address", "opening_hours"])
            time.sleep(1 + attempt * 1.5)

    elements = data.get("elements", [])
    rows = []
    for el in elements:
        tags = el.get("tags", {}) or {}
        name = tags.get("name") or tags.get("operator") or ""
        cuisine_tag = tags.get("cuisine", "")
        opening = tags.get("opening_hours") or ""

        if el.get("type") == "node":
            rlat = el.get("lat")
            rlon = el.get("lon")
        else:
            center = el.get("center") or {}
            rlat = center.get("lat")
            rlon = center.get("lon")

        if rlat is None or rlon is None:
            continue

        address = _build_address_from_tags(tags)

        rows.append({
            "name": name,
            "cuisine": cuisine_tag,
            "lat": float(rlat),
            "lon": float(rlon),
            "address": address,
            "opening_hours": opening,
        })

    df = pd.DataFrame(rows, columns=["name", "cuisine", "lat", "lon", "address", "opening_hours"])
    return df
