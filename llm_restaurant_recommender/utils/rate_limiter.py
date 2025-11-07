"""Rate limiting utilities to avoid exceeding API quotas."""
import time
from collections import defaultdict
from threading import Lock
from typing import Dict

from .logger import get_logger
import config

logger = get_logger(__name__)


class RateLimiter:
    """Simple rate limiter using sliding window approach.
    
    Limits:
    - Nominatim: 1 request per second
    - Overpass: 2 requests per second (conservative)
    """
    
    def __init__(self):
        self._last_call: Dict[str, float] = defaultdict(float)
        self._lock = Lock()
        
        # Minimum seconds between calls
        rl = getattr(config, "RATE_LIMITS", {}) or {}
        self._limits = {
            "nominatim": float(rl.get("nominatim", 1.0)),
            "overpass": float(rl.get("overpass", 0.5)),
            "default": float(rl.get("default", 0.1)),
        }
    
    def wait_if_needed(self, service: str = "default") -> None:
        """Block if necessary to respect rate limits.
        
        Args:
            service: Name of the service (nominatim, overpass, default)
        """
        with self._lock:
            now = time.time()
            last = self._last_call.get(service, 0.0)
            min_interval = self._limits.get(service, self._limits["default"])
            
            elapsed = now - last
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                logger.debug(f"Rate limiting {service}: waiting {wait_time:.2f}s")
                time.sleep(wait_time)
            
            self._last_call[service] = time.time()


# Global rate limiter instance
_rate_limiter = RateLimiter()


def wait_for_nominatim():
    """Wait if needed to respect Nominatim rate limits."""
    _rate_limiter.wait_if_needed("nominatim")


def wait_for_overpass():
    """Wait if needed to respect Overpass API rate limits."""
    _rate_limiter.wait_if_needed("overpass")
