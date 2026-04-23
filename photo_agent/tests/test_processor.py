"""
Tests for processor module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from PIL import Image

from photo_agent.src.core.processor import Processor
from photo_agent.src.core.config import Config


class TestProcessorInitialization:
    """Test Processor initialization."""
    
    @patch('photo_agent.src.core.processor.new_session')
    @patch('photo_agent.src.core.processor.Brain')
    def test_processor_init(self, mock_brain, mock_session):
        """Test processor initializes correctly."""
        mock_session.return_value = Mock()
        mock_brain.return_value = Mock()
        
        processor = Processor(knowledge_base_dir="test_kb")
        
        assert processor.session is not None
        assert processor.brain is not None
        mock_brain.assert_called_once_with("test_kb")


class TestShapeClassification:
    """Test shape classification logic."""
    
    @patch('photo_agent.src.core.processor.new_session')
    @patch('photo_agent.src.core.processor.Brain')
    def setup_method(self, mock_brain, mock_session):
        """Set up test fixtures."""
        mock_session.return_value = Mock()
        mock_brain.return_value = Mock()
        self.processor = Processor()
    
    def test_classify_thin_vertical(self):
        """Test thin vertical shape classification."""
        # Aspect ratio < 0.5 (very narrow)
        bbox = (0, 0, 100, 500)  # width=100, height=500, aspect=0.2
        shape = self.processor._classify_shape(bbox)
        assert shape == "THIN_VERT"
    
    def test_classify_thick_vertical(self):
        """Test thick vertical shape classification."""
        # 0.5 <= aspect ratio < 1.15
        bbox = (0, 0, 300, 500)  # width=300, height=500, aspect=0.6
        shape = self.processor._classify_shape(bbox)
        assert shape == "THICK_VERT"
    
    def test_classify_long_horizontal(self):
        """Test long horizontal shape classification."""
        # Aspect ratio > 1.75
        bbox = (0, 0, 700, 200)  # width=700, height=200, aspect=3.5
        shape = self.processor._classify_shape(bbox)
        assert shape == "LONG_HORIZ"
    
    def test_classify_normal_horizontal(self):
        """Test normal horizontal shape classification."""
        # 1.15 <= aspect ratio <= 1.75
        bbox = (0, 0, 400, 300)  # width=400, height=300, aspect=1.33
        shape = self.processor._classify_shape(bbox)
        assert shape == "NORMAL_HORIZ"
    
    def test_classify_handles_zero_dimensions(self):
        """Test classification handles zero dimensions gracefully."""
        bbox = (0, 0, 0, 0)
        shape = self.processor._classify_shape(bbox)
        assert shape in ["THIN_VERT", "THICK_VERT", "NORMAL_HORIZ", "LONG_HORIZ"]


class TestContextTypeDecision:
    """Test context type decision logic."""
    
    @patch('photo_agent.src.core.processor.new_session')
    @patch('photo_agent.src.core.processor.Brain')
    def setup_method(self, mock_brain, mock_session):
        """Set up test fixtures."""
        mock_session.return_value = Mock()
        mock_brain_instance = Mock()
        mock_brain.return_value = mock_brain_instance
        self.processor = Processor()
        self.mock_rgb = Mock(spec=Image.Image)
        self.mock_mask = Mock(spec=Image.Image)
    
    def test_kb_match_respected(self):
        """Test that KB_MATCH source is respected."""
        result = self.processor._decide_context_type(
            ai_label="PLATE",
            ai_confidence=0.95,
            ai_source="KB_MATCH",
            laplacian_variance=50.0,
            orig_rgb=self.mock_rgb,
            mask_img=self.mock_mask
        )
        assert result == "PLATE"
    
    def test_high_laplacian_forces_lifestyle(self):
        """Test high background texture forces LIFESTYLE."""
        with patch.object(Config, 'BG_LAPLACIAN_THRESHOLD', 32.0):
            result = self.processor._decide_context_type(
                ai_label="PRODUCT",
                ai_confidence=0.5,
                ai_source="ZERO_SHOT",
                laplacian_variance=50.0,  # Above threshold
                orig_rgb=self.mock_rgb,
                mask_img=self.mock_mask
            )
            assert result == "LIFESTYLE"
    
    def test_low_confidence_defaults_to_product(self):
        """Test low confidence defaults to PRODUCT."""
        with patch.object(Config, 'AI_CONFIDENCE_THRESHOLD', 0.80):
            result = self.processor._decide_context_type(
                ai_label="PLATE",
                ai_confidence=0.5,  # Below threshold
                ai_source="ZERO_SHOT",
                laplacian_variance=10.0,  # Below threshold
                orig_rgb=self.mock_rgb,
                mask_img=self.mock_mask
            )
            assert result == "PRODUCT"
