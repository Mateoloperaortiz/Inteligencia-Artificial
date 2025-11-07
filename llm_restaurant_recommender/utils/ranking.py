import ast
import math
from typing import Optional, Tuple

import pandas as pd


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth (in meters)."""
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    R = 6371000  # Radius of earth in meters
    return R * c


PRICE_SYMBOLS = {"$": "low", "$$": "medium", "$$$": "high", "$$$$": "high"}


def _safe_parse_tags(raw):
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return {}
    try:
        return ast.literal_eval(raw)
    except Exception:
        return {}


def _infer_price_bucket(row: pd.Series) -> str:
    price = row.get("price_range")
    if isinstance(price, str) and price.strip():
        normalized = price.strip().lower()
        if normalized in {"low", "medio", "medium", "high", "alto", "bajo"}:
            return {"medio": "medium", "alto": "high", "bajo": "low"}.get(normalized, normalized)

    symbolic_price = row.get("price")
    if isinstance(symbolic_price, str) and symbolic_price.strip():
        cleaned = symbolic_price.strip()
        if cleaned in PRICE_SYMBOLS:
            return PRICE_SYMBOLS[cleaned]
        lowered = cleaned.lower()
        if lowered in {"low", "medium", "high"}:
            return lowered

    numeric_price = row.get("average_price") or row.get("avg_price")
    if numeric_price is not None:
        try:
            value = float(numeric_price)
            if value < 30000:
                return "low"
            if value < 60000:
                return "medium"
            return "high"
        except Exception:
            pass

    tags = _safe_parse_tags(row.get("tags"))
    if tags:
        tag_price = tags.get("price") or tags.get("price:class") or tags.get("cost")
        if tag_price:
            if isinstance(tag_price, str):
                tag_price = tag_price.strip()
                if tag_price in PRICE_SYMBOLS:
                    return PRICE_SYMBOLS[tag_price]
                lowered = tag_price.lower()
                if lowered in {"low", "medium", "high"}:
                    return lowered

    return "unknown"


def rank_restaurants(df: pd.DataFrame, prefs: dict, user_coords: Optional[Tuple[float, float]] = None, weights: dict = None) -> pd.DataFrame:
    """Score and sort restaurants combining distance (Haversine), cuisine match, price alignment and rating.

    Args:
        df: DataFrame with at least 'lat' and 'lon' columns. May include 'rating'.
        prefs: dict containing optional 'cuisine' and 'price_range' keys.
        user_coords: optional tuple (lat, lon). If provided, distance is computed with Haversine.
        weights: optional dict with keys 'distance', 'cuisine', 'price', 'rating'.

    Returns:
        DataFrame sorted by 'score' descending and containing new columns 'distance_m' and 'score'.

    Notes:
    - If user_coords is not provided but df already has 'distance_m', that value will be used.
    - If neither is available, distances will be NaN and ranking will rely on cuisine/rating only.
    """
    df = df.copy()

    if weights is None:
        weights = {"distance": 0.5, "cuisine": 0.25, "price": 0.15, "rating": 0.1}

    # Ensure lat/lon exist
    if "lat" not in df.columns or "lon" not in df.columns:
        raise ValueError("DataFrame must contain 'lat' and 'lon' columns to compute distances")

    # Compute distance (meters) if user_coords provided
    if user_coords is not None:
        ulat, ulon = float(user_coords[0]), float(user_coords[1])
        df["distance_m"] = df.apply(lambda row: haversine_meters(ulat, ulon, float(row["lat"]), float(row["lon"])), axis=1)

    # Normalize distance to a score in [0,1]: closer => higher. Use a simple linear decay up to max_dist.
    # Determine max distance observed (or default to 5000 m)
    df["distance_m"] = pd.to_numeric(df.get("distance_m"), errors="coerce")
    max_dist = df["distance_m"].max(skipna=True)
    if pd.isna(max_dist) or max_dist <= 0:
        max_dist = 5000.0

    # score_distance: 1.0 for distance 0, 0.0 for distance >= max_dist
    df["score_distance"] = df["distance_m"].apply(lambda d: max(0.0, 1.0 - (d / max_dist)) if pd.notna(d) else 0.0)

    # Cuisine match score: 1 if matches preference (case-insensitive substring), else 0
    pref_cuisine = (prefs or {}).get("cuisine") or ""
    if pref_cuisine:
        df["score_cuisine"] = df["cuisine"].fillna("").str.contains(pref_cuisine, case=False).astype(float)
    else:
        df["score_cuisine"] = 0.0

    # Price alignment score: encourage matches with preferred range
    pref_price = (prefs or {}).get("price_range", "any")
    df["price_bucket"] = df.apply(_infer_price_bucket, axis=1)
    if pref_price and pref_price.lower() not in {"any", ""}:
        pref_price = pref_price.lower().strip()
        pref_price = {"medio": "medium", "media": "medium", "moderado": "medium", "moderada": "medium", "alto": "high", "alta": "high", "bajo": "low", "baja": "low"}.get(pref_price, pref_price)

        def _score_price(bucket: str) -> float:
            if bucket == pref_price:
                return 1.0
            if bucket in {"unknown", ""}:
                return 0.2
            if {bucket, pref_price} == {"low", "medium"} or {bucket, pref_price} == {"medium", "high"}:
                return 0.5
            return 0.0

        df["score_price"] = df["price_bucket"].apply(_score_price)
    else:
        df["score_price"] = 0.0

    # Rating score: normalize rating column (assume 0-5 scale). If no rating, 0.
    if "rating" in df.columns:
        df["rating_norm"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0) / 5.0
    else:
        df["rating_norm"] = 0.0

    # Combine weighted score
    df["score"] = (
        weights.get("distance", 0.0) * df["score_distance"]
        + weights.get("cuisine", 0.0) * df["score_cuisine"]
        + weights.get("price", 0.0) * df["score_price"]
        + weights.get("rating", 0.0) * df["rating_norm"]
    )

    # Small tie-breaker: prefer nearer restaurants when scores equal
    df = df.sort_values(by=["score", "distance_m"], ascending=[False, True]).reset_index(drop=True)
    return df
