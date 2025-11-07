"""Tests for ranking utilities."""
import pandas as pd
import pytest
from utils.ranking import haversine_meters, rank_restaurants, PRICE_SYMBOLS


class TestHaversineMeters:
    """Tests for haversine distance calculation."""
    
    def test_same_point(self):
        """Test distance between same point is 0."""
        dist = haversine_meters(6.2100, -75.5710, 6.2100, -75.5710)
        assert dist < 1.0  # Should be very close to 0
    
    def test_known_distance(self):
        """Test approximate distance between two known points."""
        # ~1.5 km apart
        dist = haversine_meters(6.2100, -75.5710, 6.2250, -75.5710)
        assert 1400 < dist < 1700  # Approximate validation


class TestPriceSymbols:
    """Test price symbol mappings."""
    
    def test_price_symbols_exist(self):
        """Verify all price symbols are defined."""
        assert "$" in PRICE_SYMBOLS
        assert "$$" in PRICE_SYMBOLS
        assert "$$$" in PRICE_SYMBOLS
        assert "$$$$" in PRICE_SYMBOLS


class TestRankRestaurants:
    """Tests for restaurant ranking function."""
    
    def test_rank_with_empty_dataframe(self):
        """Test ranking with empty DataFrame raises error."""
        df = pd.DataFrame()
        prefs = {"cuisine": "italian", "price_range": "low"}
        
        with pytest.raises(ValueError):
            rank_restaurants(df, prefs, user_coords=(6.21, -75.57))
    
    def test_rank_basic(self):
        """Test basic ranking functionality."""
        df = pd.DataFrame({
            "name": ["Restaurant A", "Restaurant B"],
            "lat": [6.2100, 6.2200],
            "lon": [-75.5710, -75.5720],
            "cuisine": ["italiano", "japonés"],
            "price_range": ["low", "high"],
            "rating": [4.5, 4.0]
        })
        
        prefs = {"cuisine": "italiano", "price_range": "low"}
        result = rank_restaurants(df, prefs, user_coords=(6.21, -75.57))
        
        assert len(result) == 2
        assert "score" in result.columns
        assert "distance_m" in result.columns
        # First result should be Italian restaurant (cuisine match)
        assert result.iloc[0]["cuisine"] == "italiano"
