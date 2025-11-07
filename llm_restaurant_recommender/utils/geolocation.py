import ast
import time
from pathlib import Path
from typing import Optional, Tuple, Union

import pandas as pd
import requests
from geopy.geocoders import Nominatim

from .ranking import PRICE_SYMBOLS, haversine_meters

OVERPASS_URL = "http://overpass-api.de/api/interpreter"

_geolocator = Nominatim(user_agent="llm_restaurant_recommender")

LOCAL_DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "restaurants_sample.csv"


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


def _normalize_price_label(value: Optional[str]) -> str:
    if not value:
        return ""
    value = str(value).strip()
    if value in PRICE_SYMBOLS:
        return PRICE_SYMBOLS[value]
    lowered = value.lower()
    return {
        "low": "low",
        "medio": "medium",
        "media": "medium",
        "medium": "medium",
        "moderado": "medium",
        "moderada": "medium",
        "high": "high",
        "alto": "high",
        "alta": "high",
        "bajo": "low",
        "baja": "low",
    }.get(lowered, "")


def _safe_parse_tags(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return {}
    try:
        return ast.literal_eval(raw)
    except Exception:
        return {}


def _load_local_dataset() -> pd.DataFrame:
    if not LOCAL_DATASET_PATH.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(LOCAL_DATASET_PATH)
    except Exception:
        return pd.DataFrame()

    if df.empty or "lat" not in df.columns or "lon" not in df.columns:
        return pd.DataFrame()

    if "cuisine" not in df.columns:
        df["cuisine"] = ""

    if "tags" in df.columns:
        parsed = df["tags"].apply(_safe_parse_tags)
        df["tags"] = parsed
        if "price" not in df.columns:
            df["price"] = parsed.apply(lambda t: t.get("price") if isinstance(t, dict) else None)
        if "price_range" not in df.columns:
            df["price_range"] = parsed.apply(lambda t: _normalize_price_label(t.get("price")) if isinstance(t, dict) else "")
        else:
            mask = df["price_range"].isna() | (df["price_range"].astype(str).str.strip() == "")
            df.loc[mask, "price_range"] = parsed[mask].apply(lambda t: _normalize_price_label(t.get("price")) if isinstance(t, dict) else "")
    else:
        df["tags"] = [{}] * len(df)

    if "price_range" not in df.columns:
        df["price_range"] = df.get("price", "").apply(_normalize_price_label)

    df["source"] = "local_dataset"
    return df


def _filter_within_radius(df: pd.DataFrame, center: Tuple[float, float], radius: int) -> pd.DataFrame:
    if df.empty:
        return df
    lat, lon = center
    df = df.copy()
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])
    df["distance_m"] = df.apply(lambda row: haversine_meters(lat, lon, float(row["lat"]), float(row["lon"])), axis=1)
    return df[df["distance_m"] <= radius].reset_index(drop=True)


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
""".strip()

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
                data = None
                break
            time.sleep(1 + attempt * 1.5)

    rows = []
    if data:
        elements = data.get("elements", [])
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
            price = tags.get("price") or tags.get("price:class")
            price_range = _normalize_price_label(price)

            rows.append({
                "name": name,
                "cuisine": cuisine_tag,
                "lat": float(rlat),
                "lon": float(rlon),
                "address": address,
                "opening_hours": opening,
                "price": price,
                "price_range": price_range,
                "tags": tags,
                "source": "overpass",
            })

    df_overpass = pd.DataFrame(rows)

    local_df = _load_local_dataset()
    if cuisine:
        cuisine_lower = cuisine.lower()
        local_df = local_df[local_df["cuisine"].fillna("").str.lower().str.contains(cuisine_lower, na=False)] if not local_df.empty else local_df
    local_df = _filter_within_radius(local_df, coords, radius) if not local_df.empty else local_df

    if df_overpass.empty and local_df.empty:
        return pd.DataFrame(columns=["name", "cuisine", "lat", "lon", "address", "opening_hours", "price", "price_range", "tags", "source", "distance_m"])

    frames = []
    if not df_overpass.empty:
        df_overpass = _filter_within_radius(df_overpass, coords, radius)
        frames.append(df_overpass)
    if not local_df.empty:
        frames.append(local_df)

    if not frames:
        return pd.DataFrame(columns=["name", "cuisine", "lat", "lon", "address", "opening_hours", "price", "price_range", "tags", "source", "distance_m"])

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["name", "lat", "lon"], keep="first")
    return combined.reset_index(drop=True)
