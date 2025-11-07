import json
import os
import re
from typing import Dict, List, Optional

import config

from .logger import get_logger

logger = get_logger(__name__)


class ModelWrapper:
    """Wrapper for Hugging Face transformers LLM (Phi-4).
    
    Uses the model specified in HF_MODEL environment variable.
    The model is cached after first load to avoid reloading on every call.
    
    Installation:
      pip install transformers accelerate torch
      
    Set environment variable:
      $env:HF_MODEL = "microsoft/Phi-4-mini-instruct"
    
    If no model is available, returns None and callers use template explanations.
    """

    def __init__(self, hf_model: Optional[str] = None):
        self.hf_model = hf_model or os.environ.get("HF_MODEL")
        self._hf_pipeline = None  # Cache for HF pipeline

    def _load_hf_pipeline(self):
        """Lazy load and cache the HuggingFace pipeline."""
        if self._hf_pipeline is None and self.hf_model:
            try:
                logger.info(f"Loading HuggingFace model: {self.hf_model}")
                from transformers import pipeline
                self._hf_pipeline = pipeline(
                    "text-generation", 
                    model=self.hf_model, 
                    device_map="auto"
                )
                logger.info(f"HuggingFace model loaded successfully: {self.hf_model}")
            except Exception as e:
                logger.error(f"Failed to load HuggingFace model: {e}")
        return self._hf_pipeline

    def generate(self, prompt: str, max_new_tokens: int = 128) -> Optional[str]:
        """Generate text using Phi-4 model.
        
        Args:
            prompt: Input prompt for generation
            max_new_tokens: Maximum tokens to generate
            
        Returns:
            Generated text or None if model not available
        """
        pipe = self._load_hf_pipeline()
        if pipe is not None:
            try:
                logger.debug(f"Generating text with HuggingFace (max_tokens={max_new_tokens})")
                out = pipe(prompt, max_new_tokens=max_new_tokens, do_sample=True, top_p=0.95)
                if out and isinstance(out, list):
                    logger.debug("HuggingFace generation successful")
                    return out[0].get("generated_text")
            except Exception as e:
                logger.error(f"HuggingFace generation failed: {e}")
                return None

        # No model available
        logger.warning("No LLM model available (HF_MODEL not set or transformers not installed)")
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
        txt = _MODEL.generate(prompt, max_new_tokens=config.LLM_MAX_TOKENS)
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

    patterns = [
        r"cerca\s+(?:de|del|de la|de los|de las|al|a la|a los|a las)\s+([\w\sáéíóúñ]+)",
        r"(?:en|por|alrededor\s+de)\s+([\w\sáéíóúñ]+)",
    ]
    m = None
    for pat in patterns:
        m = re.search(pat, q)
        if m:
            place = m.group(1).strip()
            break
    if m:
        place = re.sub(r"\b(barato|barata|baratos|baratas|económico|economico|económica|economica|económicos|economicos|cerca|por|en|alrededor|del|de|de la|de los|de las|al|a|la|los|las|medio|media|moderado|moderada)\b", "", place).strip()
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
            txt = _MODEL.generate(prompt, max_new_tokens=config.LLM_EXPLANATION_MAX_TOKENS)
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
