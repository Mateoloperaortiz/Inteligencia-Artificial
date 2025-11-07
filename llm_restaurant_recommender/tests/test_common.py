"""Tests for common utilities."""
import pytest
from utils.common import safe_parse_tags


class TestSafeParseTags:
    """Tests for safe_parse_tags function."""
    
    def test_dict_input(self):
        """Test that dict input is returned as-is."""
        tags = {"key": "value", "price": "$"}
        result = safe_parse_tags(tags)
        assert result == tags
    
    def test_string_dict_input(self):
        """Test parsing string representation of dict."""
        tags_str = "{'addr:street':'Cra 35', 'price':'$'}"
        result = safe_parse_tags(tags_str)
        assert isinstance(result, dict)
        assert result.get("price") == "$"
    
    def test_invalid_string(self):
        """Test that invalid string returns empty dict."""
        result = safe_parse_tags("not a dict")
        assert result == {}
    
    def test_none_input(self):
        """Test that None returns empty dict."""
        result = safe_parse_tags(None)
        assert result == {}
    
    def test_number_input(self):
        """Test that number returns empty dict."""
        result = safe_parse_tags(123)
        assert result == {}
