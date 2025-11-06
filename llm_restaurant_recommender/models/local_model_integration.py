"""Integration point for a local or free LLM.

This module tries to use a local GPT4All model (if `gpt4all` package is installed) or
falls back to a very small stub. The user can modify this file to connect to other local
models or to a free Hugging Face endpoint (if they have one).
"""
from typing import Optional


def generate_text(prompt: str, max_tokens: int = 150) -> Optional[str]:
    """Try local model generation. Return string or None on failure.

    This default implementation is conservative: it tries to import gpt4all and use it.
    If not available, it returns None so caller can fallback.
    """
    try:
        # lazy import to avoid hard dependency
        from gpt4all import GPT4All

        model = GPT4All("gpt4all-lora-quantized")
        resp = model.generate(prompt, max_tokens=max_tokens)
        return resp
    except Exception:
        # No local model available or error — return None for fallback
        return None
