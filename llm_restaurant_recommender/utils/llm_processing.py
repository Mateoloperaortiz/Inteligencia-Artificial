import re
from typing import Dict, List

from models import local_model_integration


def parse_query(query: str) -> Dict:
    """Extract simple preferences (cuisine, location, price) from a Spanish NL query using heuristics."""
    q = query.lower()
    prefs = {"raw": query}

    # cuisine extraction (look for common words)
    cuisines = ["italiano", "chino", "japonés", "japones", "mexicano", "vegetariano", "vegano", "hamburguesa", "pizza", "peruano", "francés", "frances"]
    for c in cuisines:
        if c in q:
            prefs["cuisine"] = c
            break

    # price
    if any(k in q for k in ["barato", "económico", "económico"]):
        prefs["price"] = "low"
    elif any(k in q for k in ["caro", "costoso", "lujoso"]):
        prefs["price"] = "high"
    else:
        prefs.setdefault("price", "any")

    # location — try to match 'cerca de X' or 'en X'
    m = re.search(r"cerca de ([\w\sáéíóúÑñ]+)", q)
    if not m:
        m = re.search(r"en ([\w\sáéíóúÑñ]+)", q)
    if m:
        place = m.group(1).strip()
        # strip trailing words like 'barato'
        place = re.sub(r"\b(barato|barata|baratos|baratas|económico|cerca)\b", "", place).strip()
        prefs["location"] = place

    # fallback: if query contains a known neighborhood token
    if "location" not in prefs:
        neighborhoods = ["poblado", "centro", "laureles", "envigado", "belén"]
        for n in neighborhoods:
            if n in q:
                prefs["location"] = n
                break

    return prefs


def generate_explanations(user_query: str, restaurants: List[Dict]) -> List[str]:
    """Generate short explanations for each restaurant. Try local model first; fallback to template."""
    try:
        texts = []
        for r in restaurants:
            prompt = _build_prompt(user_query, r)
            txt = local_model_integration.generate_text(prompt)
            if not txt:
                txt = _fallback_explanation(user_query, r)
            texts.append(txt)
        return texts
    except Exception:
        return [_fallback_explanation(user_query, r) for r in restaurants]


def _build_prompt(user_query: str, r: Dict) -> str:
    name = r.get("name") or "Este restaurante"
    cuisine = r.get("cuisine") or "varios"
    dist = r.get("distance_m", "desconocida")
    tags = r.get("tags", {})
    return (
        f"Eres un asistente que resume por qué un restaurante es una buena opción. "
        f"Usuario: '{user_query}'. Restaurante: {name}, cocina: {cuisine}, distancia: {dist} m, tags: {tags}. "
        f"Genera una explicación breve (1-2 oraciones) indicando por qué puede interesar y un consejo práctico."
    )


def _fallback_explanation(user_query: str, r: Dict) -> str:
    name = r.get("name") or "Este restaurante"
    cuisine = r.get("cuisine") or "cocina variada"
    dist = r.get("distance_m", "cerca")
    price_hint = "precio económico" if "price" in user_query.lower() or "barato" in user_query.lower() else ""
    return f"{name}: Cocina {cuisine}. A {dist} metros — buena opción si buscas {user_query}. {price_hint}".strip()
