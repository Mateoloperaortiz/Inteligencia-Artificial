"""Configuration file for the restaurant recommender application."""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"

# API URLs
OVERPASS_URL = "http://overpass-api.de/api/interpreter"

# API Rate Limits (requests per second)
RATE_LIMITS = {
    "nominatim": 1.0,  # 1 request per second
    "overpass": 0.5,   # 2 requests per second (conservative)
    "default": 0.1,
}

# Search defaults
DEFAULT_SEARCH_RADIUS = 1500  # meters
MAX_SEARCH_RADIUS = 10000  # meters
MIN_SEARCH_RADIUS = 200  # meters
DEFAULT_TOP_K = 5
MAX_TOP_K = 20

# Query validation
MIN_QUERY_LENGTH = 3
MAX_QUERY_LENGTH = 500

# Ranking weights
RANKING_WEIGHTS = {
    "distance": 0.5,
    "cuisine": 0.25,
    "price": 0.15,
    "rating": 0.1,
}

# Price categories
PRICE_SYMBOLS = {
    "$": "low",
    "$$": "medium",
    "$$$": "high",
    "$$$$": "high",
}

# LLM Model configuration
LLM_MODEL = os.environ.get("HF_MODEL", None)
LLM_MAX_TOKENS = 128
LLM_EXPLANATION_MAX_TOKENS = 80

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Cache TTL (seconds)
SEARCH_CACHE_TTL = 600  # 10 minutes
