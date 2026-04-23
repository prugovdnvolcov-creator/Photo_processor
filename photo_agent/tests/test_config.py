"""
Tests for configuration module.
"""

import pytest
from photo_agent.src.core.config import (
    Config,
    CanvasConfig,
    AnalysisConfig,
    AIConfig,
    MarginConfig,
)


class TestCanvasConfig:
    """Test canvas configuration."""
    
    def test_canvas_dimensions(self):
        """Test default canvas dimensions."""
        assert CanvasConfig.WIDTH == 1280
        assert CanvasConfig.HEIGHT == 840
    
    def test_bg_color(self):
        """Test background color format."""
        color = CanvasConfig.PRODUCT_BG_COLOR
        assert color.startswith("#")
        assert len(color) == 7


class TestAnalysisConfig:
    """Test analysis configuration."""
    
    def test_thresholds_are_positive(self):
        """Test that all thresholds are positive values."""
        assert AnalysisConfig.BG_LAPLACIAN_THRESHOLD > 0
        assert AnalysisConfig.BG_ENTROPY_THRESHOLD > 0
        assert 0 < AnalysisConfig.STRIP_WIDTH_RATIO < 1


class TestAIConfig:
    """Test AI configuration."""
    
    def test_confidence_threshold_range(self):
        """Test confidence threshold is valid probability."""
        assert 0 <= AIConfig.CONFIDENCE_THRESHOLD <= 1
    
    def test_similarity_threshold_range(self):
        """Test similarity threshold is valid probability."""
        assert 0 <= AIConfig.SIMILARITY_THRESHOLD <= 1
    
    def test_model_name_not_empty(self):
        """Test model name is specified."""
        assert AIConfig.MODEL_NAME
        assert isinstance(AIConfig.MODEL_NAME, str)


class TestMarginConfig:
    """Test margin configuration."""
    
    def test_product_margins_exist(self):
        """Test product margins dictionary has expected keys."""
        margins = MarginConfig.PRODUCT
        assert "DEFAULT" in margins
        assert "THIN_VERT" in margins
    
    def test_margin_values_are_positive(self):
        """Test all margin values are non-negative."""
        for shape, margins in MarginConfig.PRODUCT.items():
            for direction, value in margins.items():
                assert value >= 0, f"Negative margin in {shape}.{direction}"
    
    def test_plate_margins_structure(self):
        """Test plate margins have required keys."""
        margins = MarginConfig.PLATE
        assert "top" in margins
        assert "bottom" in margins
        assert "side" in margins


class TestConfig:
    """Test main Config class aggregation."""
    
    def test_config_has_canvas_settings(self):
        """Test Config aggregates canvas settings."""
        assert hasattr(Config, 'CANVAS_W')
        assert hasattr(Config, 'CANVAS_H')
        assert hasattr(Config, 'PRODUCT_BG_COLOR')
    
    def test_config_has_ai_settings(self):
        """Test Config aggregates AI settings."""
        assert hasattr(Config, 'AI_CONFIDENCE_THRESHOLD')
        assert hasattr(Config, 'SIMILARITY_THRESHOLD')
    
    def test_config_has_margins(self):
        """Test Config aggregates margin settings."""
        assert hasattr(Config, 'MARGINS_PRODUCT')
        assert hasattr(Config, 'MARGINS_PLATE')
        assert hasattr(Config, 'MARGINS_LIFESTYLE')
