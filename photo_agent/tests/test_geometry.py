"""Tests for geometry module."""

import pytest
from PIL import Image
import numpy as np

from photo_agent.src.core.geometry import GeometryExpert


class TestGeometryExpert:
    """Test GeometryExpert class."""
    
    def test_get_bboxes_basic(self):
        """Test basic bounding box detection."""
        # Create simple test image with white rectangle on black background
        img = Image.new("RGB", (100, 100), color="black")
        mask = Image.new("L", (100, 100), color=0)
        
        # Draw white rectangle in center
        for x in range(30, 70):
            for y in range(30, 70):
                mask.putpixel((x, y), 255)
        
        core_bbox, full_bbox, solidity, circularity = GeometryExpert.get_bboxes(
            img, mask, "PRODUCT"
        )
        
        # Check bbox is roughly correct
        assert core_bbox[0] >= 25  # x1
        assert core_bbox[1] >= 25  # y1
        assert core_bbox[2] <= 75  # x2
        assert core_bbox[3] <= 75  # y2
    
    def test_get_bboxes_plate_vs_product(self):
        """Test that plate and product return different bboxes when appropriate."""
        img = Image.new("RGB", (100, 100), color="white")
        mask = Image.new("L", (100, 100), color=0)
        
        # Draw circle in center
        center_x, center_y = 50, 50
        radius = 20
        for x in range(100):
            for y in range(100):
                if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2:
                    mask.putpixel((x, y), 255)
        
        core_bbox_prod, _, _, _ = GeometryExpert.get_bboxes(img, mask, "PRODUCT")
        core_bbox_plate, full_bbox_plate, _, _ = GeometryExpert.get_bboxes(
            img, mask, "PLATE"
        )
        
        # For plates, full_bbox might be expanded
        assert core_bbox_prod == core_bbox_plate
    
    def test_fallback_expand(self):
        """Test fallback expansion method."""
        core_bbox = (40, 40, 60, 60)
        width, height = 100, 100
        
        expanded = GeometryExpert._fallback_expand(core_bbox, width, height)
        
        # Expanded should be larger than core
        assert expanded[0] < core_bbox[0]  # x1 smaller
        assert expanded[1] < core_bbox[1]  # y1 smaller
        assert expanded[2] > core_bbox[2]  # x2 larger
        assert expanded[3] > core_bbox[3]  # y2 larger
        
        # Should not exceed image bounds
        assert expanded[0] >= 0
        assert expanded[1] >= 0
        assert expanded[2] <= width
        assert expanded[3] <= height
    
    def test_solidity_calculation(self):
        """Test that solidity is calculated correctly."""
        img = Image.new("RGB", (100, 100), color="black")
        mask = Image.new("L", (100, 100), color=0)
        
        # Fill entire mask
        for x in range(100):
            for y in range(100):
                mask.putpixel((x, y), 255)
        
        _, _, solidity, _ = GeometryExpert.get_bboxes(img, mask, "PRODUCT")
        
        # Full rectangle should have solidity close to 1.0
        assert 0.9 <= solidity <= 1.0
