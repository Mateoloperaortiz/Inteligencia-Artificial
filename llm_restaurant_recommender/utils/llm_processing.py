import json
import os
import re
from typing import Dict, List, Optional


class ModelWrapper:
    """Wrapper that tries multiple free/local LLM backends in order:
    1. Hugging Face `transformers` local pipeline (if a model is installed locally).
    2. GPT4All python binding (if installed and model available).
    3. Fallback: returns None so callers can use template explanations.

    Installation notes (choose one):
    - Hugging Face (local):
      * pip install transformers accelerate
      * Download a compatible model (for CPU you may need a small model). Example (requires large disk/RAM):
        - Use `transformers` to load `HuggingFaceH4/zephyr-7b-alpha` only if you have the hardware.
      * Set environment variable HF_MODEL to the model id or local path.

    - GPT4All (local):
      * pip install gpt4all
      * Download a quantized model from https://gpt4all.io and place it where gpt4all expects or pass path by editing `models/local_model_integration.py`.

    Note: This wrapper avoids hard dependencies at import time; imports are attempted when generating text.
    """

    def __init__(self, hf_model: Optional[str] = None):
        self.hf_model = hf_model or os.environ.get("HF_MODEL")

    def generate(self, prompt: str, max_new_tokens: int = 128) -> Optional[str]:
        # Try Hugging Face transformers local pipeline
        if self.hf_model:
            try:
                from transformers import pipeline

                pipe = pipeline("text-generation", model=self.hf_model, device_map="auto")
                out = pipe(prompt, max_new_tokens=max_new_tokens, do_sample=True, top_p=0.95)
                if out and isinstance(out, list):
                    return out[0].get("generated_text")
            except Exception:
                # fall through to next option
                pass

        # Try GPT4All python binding
        try:
            from gpt4all import GPT4All

            model_name = "gpt4all-lora-quantized"
            gpt = GPT4All(model_name)
            resp = gpt.generate(prompt, max_tokens=max_new_tokens)
            return resp
        except Exception:
            pass

        # No model available
        return None


_MODEL = ModelWrapper()


def analyze_query(query: str) -> Dict:
    """Analyze a Spanish user query and return a JSON-like dict with keys:
    - cuisine: string (or empty)
    - price_range: 'low'|'high'|'any'
    - location: string (or empty)

    The function will try to use a local/free LLM to parse the query more robustly if
    a model is configured (see ModelWrapper). If not available, it falls back to heuristics.
    """
    # Try LLM-based parsing first (prompt expects JSON only)
    prompt = (
        "Extract from the user's query the following fields as JSON: cuisine, price_range, location. "
        "Return only a JSON object. Fields should be the empty string when the information is missing. "
        f"User query: '''{query}'''.\n\nExample output:\n{{\n  \"cuisine\": \"italiano\",\n  \"price_range\": \"low\",\n  \"location\": \"El Poblado\"\n}}"
    )

    try:
        txt = _MODEL.generate(prompt, max_new_tokens=128)
        if txt:
            # Extract JSON from response
            j = _extract_json_from_text(txt)
            if j and isinstance(j, dict):
                # normalize keys
                return {
                    "cuisine": j.get("cuisine", "") or "",
                    "price_range": j.get("price_range", "any") or "any",
                    "location": j.get("location", "") or "",
                    "raw": query,
                }
    except Exception:
        pass

    # Fallback heuristics (simple)
    q = query.lower()
    result = {"raw": query, "cuisine": "", "price_range": "any", "location": ""}

    cuisines = [
        "italiano",
        "italiana",
        "chino",
        "china",
        "japonés",
        "japones",
        "sushi",
        "mexicano",
        "mexicana",
        "vegetariano",
        "vegano",
        "vegana",
        "hamburguesa",
        "pizza",
        "peruano",
        "peruana",
        "francés",
        "frances",
        "india",
        "thai",
        "tailandés",
        "tapas",
    ]
    for c in cuisines:
        if c in q:
            result["cuisine"] = c
            break

    if any(k in q for k in ["barato", "económico", "economico", "económica", "economica", "económicos", "economicos", "asequible", "asequibles"]):
        result["price_range"] = "low"
    elif any(k in q for k in ["caro", "costoso", "costosa", "lujoso", "lujosa", "exclusivo", "exclusiva"]):
        result["price_range"] = "high"
    elif any(k in q for k in ["medio", "media", "moderado", "moderada"]):
        result["price_range"] = "medium"

    m = re.search(r"cerca de ([\w\sáéíóúñ]+)", q)
    if not m:
        m = re.search(r"(en|por|alrededor de) ([\w\sáéíóúñ]+)", q)
    if m:
        place = m.groups()[-1].strip()
        place = re.sub(r"\b(barato|barata|baratos|baratas|económico|economico|cerca|por|en|alrededor|medio|moderado)\b", "", place).strip()
        result["location"] = place

    if not result["location"]:
        neighborhoods = ["poblado", "el poblado", "centro", "laureles", "envigado", "belén", "belen", "sabaneta", "itagüí", "itagui"]
        for n in neighborhoods:
            if n in q:
                result["location"] = n
                break

    return result


def generate_explanations(user_query: str, restaurants: List[Dict]) -> List[str]:
    """Generate short Spanish explanations for each restaurant.

    Tries ModelWrapper.generate; if no model available or generation fails, falls back to a template.
    """
    out = []
    for r in restaurants:
        prompt = _build_explanation_prompt(user_query, r)
        try:
            txt = _MODEL.generate(prompt, max_new_tokens=80)
            if txt:
                # Keep only the first 1-2 sentences
                s = _first_sentences(txt, max_sentences=2)
                out.append(s)
                continue
        except Exception:
            pass
        out.append(_fallback_explanation(user_query, r))
    return out


def _build_explanation_prompt(user_query: str, r: Dict) -> str:
    name = r.get("name") or "Este restaurante"
    cuisine = r.get("cuisine") or "varios"
    dist = r.get("distance_m") or r.get("distance") or "desconocida"
    tags = r.get("tags") or {}
    prompt = (
        f"Eres un asistente conciso en español. Usuario: '{user_query}'. Restaurante: {name}, "
        f"cocina: {cuisine}, distancia: {dist} m, tags: {tags}. "
        "Genera una explicación corta (1-2 oraciones) que explique por qué es relevante para la consulta e incluya un consejo práctico. "
        "No inventes horarios ni precios exactos; si falta información, indica 'información no disponible'. Responde solo con la explicación."
    )
    return prompt


def _first_sentences(text: str, max_sentences: int = 2) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(parts[:max_sentences]).strip()


def _fallback_explanation(user_query: str, r: Dict) -> str:
    name = r.get("name") or "Este restaurante"
    cuisine = r.get("cuisine") or "cocina variada"
    dist = r.get("distance_m") or r.get("distance") or "cerca"
    price_range = r.get("price_range") or r.get("price") or "precio no disponible"
    if isinstance(price_range, (int, float)):
        price_text = f"precio aproximado {price_range}"
    else:
        price_text = str(price_range)
    hint = "pensado en opciones económicas" if ("barato" in user_query.lower() or "econ" in user_query.lower()) else ""
    return f"{name}: Cocina {cuisine}. A {dist} metros. {price_text}. {hint}".strip()


def _extract_json_from_text(text: str) -> Optional[Dict]:
    # find the first {...} in text
    try:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return None
        jtext = m.group(0)
        return json.loads(jtext)
    except Exception:
        return None
