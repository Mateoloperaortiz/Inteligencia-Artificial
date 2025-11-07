"""Integration point for a local or free LLM.

This module attempts to generate text using a local LLM (GPT4All) if available.
It is conservative: if no model or binding is available it returns None and the
caller should fall back to template-based text.

Configuration:
- To use GPT4All with a downloaded model file, set the environment variable
  `GPT4ALL_MODEL_PATH` to the full path of the model file (eg. C:\models\gpt4all-model.bin).
- Alternatively, if you have a model name that `gpt4all` recognizes (installed models),
  you can leave the env var unset and the code will try a default model id.

Installation (PowerShell examples):
    pip install gpt4all

Download models from: https://gpt4all.io/models/  and point `GPT4ALL_MODEL_PATH` to the file.
"""
import os
from typing import Optional


def generate_text(prompt: str, max_tokens: int = 150) -> Optional[str]:
    """Try local model generation via GPT4All. Return string or None on failure.

    The function looks for the environment variable `GPT4ALL_MODEL_PATH`. If present,
    it will pass that path to GPT4All. Otherwise it will try a default model id.
    """
    try:
        # lazy import to avoid hard dependency at module import time
        from gpt4all import GPT4All

        model_path = os.environ.get("GPT4ALL_MODEL_PATH")
        if model_path:
            gpt = GPT4All(model_path)
        else:
            # fallback to a commonly used local model id (may or may not be installed)
            gpt = GPT4All("gpt4all-lora-quantized")

        resp = gpt.generate(prompt, max_tokens=max_tokens)
        return resp
    except Exception:
        # No local model available or error — return None for fallback
        return None
