"""Generate a sample restaurants dataset by querying Overpass (OpenStreetMap).

Usage:
    python data/generate_dataset.py

Options:
    --city CITY       City or place name to center the search (default: "Medellín, Colombia")
    --radius METERS   Search radius in meters (default: 5000)
    --limit N         Maximum number of elements to fetch (default: 1000)
    --out PATH        Output CSV path (default: data/restaurants_sample.csv)

Notes:
- This script uses Nominatim (geopy) to geocode the city name and Overpass public API to fetch
  nodes/ways/relations with amenity=restaurant. Respect Overpass usage limits.
- To change the default city, pass --city "City, Country".
"""

import argparse
import json
import time
from typing import Optional

import pandas as pd
import requests
from geopy.geocoders import Nominatim

OVERPASS_URL = "http://overpass-api.de/api/interpreter"


def geocode(place: str, timeout: int = 10) -> Optional[tuple]:
    try:
        geolocator = Nominatim(user_agent="llm_restaurant_recommender_dataset")
        loc = geolocator.geocode(place, timeout=timeout)
        if loc:
            return float(loc.latitude), float(loc.longitude)
    except Exception as e:
        print("Geocoding error:", e)
    return None


def build_overpass_query(lat: float, lon: float, radius: int, limit: int, cuisine: Optional[str] = None) -> str:
    cuisine_filter = ''
    if cuisine:
        cuisine_filter = f'["cuisine"~"{cuisine}",i]'

    q = f"""
[out:json][timeout:60];
(
  node["amenity"="restaurant"]{cuisine_filter}(around:{radius},{lat},{lon});
  way["amenity"="restaurant"]{cuisine_filter}(around:{radius},{lat},{lon});
  relation["amenity"="restaurant"]{cuisine_filter}(around:{radius},{lat},{lon});
);
out center {limit};
""".replace("{cuisine_filter}", cuisine_filter).strip()
    return q


def fetch_overpass(query: str, retries: int = 2, pause: float = 2.0) -> Optional[dict]:
    attempt = 0
    while attempt <= retries:
        try:
            resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            attempt += 1
            print(f"Overpass request failed (attempt {attempt}): {e}")
            if attempt > retries:
                return None
            time.sleep(pause * attempt)
    return None


def parse_elements_to_rows(elements: list, center_lat: float, center_lon: float) -> list:
    rows = []
    for el in elements:
        tags = el.get("tags", {}) or {}
        name = tags.get("name") or tags.get("operator") or ""
        cuisine = tags.get("cuisine", "")
        opening = tags.get("opening_hours", "")

        if el.get("type") == "node":
            lat = el.get("lat")
            lon = el.get("lon")
        else:
            center = el.get("center") or {}
            lat = center.get("lat")
            lon = center.get("lon")

        # Address build
        address_parts = []
        for k in ["addr:street", "addr:housenumber", "addr:city", "addr:postcode", "addr:neighbourhood"]:
            if tags.get(k):
                address_parts.append(tags.get(k))
        address = ", ".join(address_parts)

        rows.append({
            "id": el.get("id"),
            "name": name,
            "cuisine": cuisine,
            "lat": lat,
            "lon": lon,
            "address": address,
            "opening_hours": opening,
            "tags": json.dumps(tags, ensure_ascii=False),
        })
    return rows


def main():
    p = argparse.ArgumentParser(description="Generate restaurants_sample.csv from Overpass (OSM)")
    p.add_argument("--city", type=str, default="Medellín, Colombia", help="City or place name (default: Medellín, Colombia)")
    p.add_argument("--radius", type=int, default=5000, help="Search radius in meters (default:5000)")
    p.add_argument("--limit", type=int, default=1000, help="Max elements to request (default:1000)")
    p.add_argument("--out", type=str, default="data/restaurants_sample.csv", help="Output CSV path")
    args = p.parse_args()

    print(f"Resolving city: {args.city}")
    coords = geocode(args.city)
    if not coords:
        print("Could not resolve city. Exiting.")
        return
    lat, lon = coords
    print(f"City center: {lat}, {lon}")

    print("Building Overpass query...")
    query = build_overpass_query(lat, lon, args.radius, args.limit)

    print("Querying Overpass...")
    data = fetch_overpass(query)
    if not data:
        print("No data returned from Overpass. Exiting.")
        return

    elements = data.get("elements", [])
    print(f"Fetched {len(elements)} elements from Overpass")

    rows = parse_elements_to_rows(elements, lat, lon)
    if not rows:
        print("No restaurants parsed. Exiting.")
        return

    df = pd.DataFrame(rows)
    out_path = args.out
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Saved {len(df)} restaurants to {out_path}")


if __name__ == "__main__":
    main()
