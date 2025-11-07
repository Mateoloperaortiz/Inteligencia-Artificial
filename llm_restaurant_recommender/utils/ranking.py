import math
from typing import Tuple, Optional

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


def rank_restaurants(df: pd.DataFrame, prefs: dict, user_coords: Optional[Tuple[float, float]] = None, weights: dict = None) -> pd.DataFrame:
    """Score and sort restaurants combining distance (Haversine), cuisine match, and rating.

    Args:
        df: DataFrame with at least 'lat' and 'lon' columns. May include 'rating'.
        prefs: dict containing optional 'cuisine' and 'price' keys.
        user_coords: optional tuple (lat, lon). If provided, distance is computed with Haversine.
        weights: optional dict with keys 'distance', 'cuisine', 'rating' specifying weights (sum not required).

    Returns:
        DataFrame sorted by 'score' descending and containing new columns 'distance_m' and 'score'.

    Notes:
    - If user_coords is not provided but df already has 'distance_m', that value will be used.
    - If neither is available, distances will be NaN and ranking will rely on cuisine/rating only.
    """
    df = df.copy()

    if weights is None:
        weights = {"distance": 0.6, "cuisine": 0.3, "rating": 0.1}

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

    # Rating score: normalize rating column (assume 0-5 scale). If no rating, 0.
    if "rating" in df.columns:
        df["rating_norm"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0) / 5.0
    else:
        df["rating_norm"] = 0.0

    # Combine weighted score
    df["score"] = (
        weights.get("distance", 0.0) * df["score_distance"]
        + weights.get("cuisine", 0.0) * df["score_cuisine"]
        + weights.get("rating", 0.0) * df["rating_norm"]
    )

    # Small tie-breaker: prefer nearer restaurants when scores equal
    df = df.sort_values(by=["score", "distance_m"], ascending=[False, True]).reset_index(drop=True)
    return df
