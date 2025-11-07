"""Common utilities shared across modules."""
import ast
from typing import Any, Dict


def safe_parse_tags(raw: Any) -> Dict:
    """Parse tags from various formats to dict.
    
    Args:
        raw: Can be dict, string representation of dict, or other types.
        
    Returns:
        Dictionary of tags, empty dict if parsing fails.
    """
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return {}
    try:
        return ast.literal_eval(raw)
    except Exception:
        return {}
