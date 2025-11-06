import pandas as pd


def rank_restaurants(df: pd.DataFrame, prefs: dict) -> pd.DataFrame:
    """Score restaurants based on distance and whether cuisine matches preference."""
    df = df.copy()
    # base score: inverse distance
    df["score"] = 1 / (df["distance_m"].astype(float) + 1)

    pref_cuisine = prefs.get("cuisine")
    if pref_cuisine:
        df["score"] += df["cuisine"].fillna("").str.contains(pref_cuisine, case=False).astype(float) * 1.0

    # price preference placeholder — could be extended if tags include pricing
    price = prefs.get("price")
    if price == "low":
        # no real price data: boost all slightly so user sees cheaper-sounding options
        df["score"] += 0.05

    return df.sort_values(by="score", ascending=False).reset_index(drop=True)
