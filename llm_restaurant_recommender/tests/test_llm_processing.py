"""Tests for LLM processing utilities."""
import pytest
from utils.llm_processing import analyze_query, _extract_json_from_text, _fallback_explanation


class TestAnalyzeQuery:
    """Tests for query analysis function."""
    
    def test_analyze_italian_query(self):
        """Test detection of Italian cuisine."""
        query = "Quiero un restaurante italiano barato"
        result = analyze_query(query)
        
        assert result["cuisine"] == "italiano"
        assert result["price_range"] == "low"
        assert result["raw"] == query
    
    def test_analyze_location_detection(self):
        """Test location detection."""
        query = "Busco comida cerca del Poblado"
        result = analyze_query(query)
        
        assert "poblado" in result["location"].lower()
    
    def test_analyze_price_detection(self):
        """Test price range detection."""
        queries_and_prices = [
            ("Quiero algo barato", "low"),
            ("Busco un lugar costoso", "high"),
            ("Restaurante de precio medio", "medium"),
        ]
        
        for query, expected_price in queries_and_prices:
            result = analyze_query(query)
            assert result["price_range"] == expected_price
    
    def test_analyze_multiple_cuisines(self):
        """Test that only one cuisine is detected."""
        query = "Busco sushi japonés"
        result = analyze_query(query)
        
        # Should detect either sushi or japonés
        assert result["cuisine"] in ["sushi", "japones", "japonés"]


class TestExtractJsonFromText:
    """Tests for JSON extraction from text."""
    
    def test_extract_valid_json(self):
        """Test extraction of valid JSON."""
        text = 'Some text before {"key": "value", "number": 123} and after'
        result = _extract_json_from_text(text)
        
        assert result is not None
        assert result["key"] == "value"
        assert result["number"] == 123
    
    def test_extract_no_json(self):
        """Test when no JSON is present."""
        text = "Just plain text with no JSON"
        result = _extract_json_from_text(text)
        
        assert result is None
    
    def test_extract_invalid_json(self):
        """Test when malformed JSON is present."""
        text = "Text with {invalid json} here"
        result = _extract_json_from_text(text)
        
        assert result is None


class TestFallbackExplanation:
    """Tests for fallback explanation generation."""
    
    def test_fallback_basic(self):
        """Test basic fallback explanation."""
        restaurant = {
            "name": "Test Restaurant",
            "cuisine": "italiano",
            "distance_m": 500,
            "price_range": "low"
        }
        query = "Quiero comida italiana barata"
        
        result = _fallback_explanation(query, restaurant)
        
        assert "Test Restaurant" in result
        assert "italiano" in result or "italian" in result.lower()
        assert "500" in result
    
    def test_fallback_with_missing_data(self):
        """Test fallback when data is missing."""
        restaurant = {
            "name": None,
            "cuisine": None,
            "distance_m": None
        }
        query = "Busco restaurante"
        
        result = _fallback_explanation(query, restaurant)
        
        # Should handle None values gracefully
        assert isinstance(result, str)
        assert len(result) > 0
