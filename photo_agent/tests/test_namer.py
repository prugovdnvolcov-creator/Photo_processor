"""
Tests for name generator utility.
"""

import pytest
from photo_agent.src.utils.namer import NameGenerator


class TestNameGenerator:
    """Test NameGenerator class."""
    
    def test_extract_long_number(self):
        """Test extraction of long numeric sequences."""
        assert NameGenerator.extract_article("product_12345_image") == "12345"
        assert NameGenerator.extract_article("IMG_987654321.jpg") == "987654321"
    
    def test_extract_short_number(self):
        """Test extraction of short numeric sequences."""
        assert NameGenerator.extract_article("item_42.png") == "42"
        assert NameGenerator.extract_article("photo7.jpg") == "7"
    
    def test_extract_no_numbers(self):
        """Test handling of text without numbers."""
        result = NameGenerator.extract_article("product_image")
        assert result == "product_image"
        
        result = NameGenerator.extract_article("test-file")
        assert result == "test-file"
    
    def test_extract_empty_string(self):
        """Test handling of empty input."""
        assert NameGenerator.extract_article("") == "unknown"
        assert NameGenerator.extract_article("   ") == "unknown"
    
    def test_extract_special_characters(self):
        """Test sanitization of special characters."""
        result = NameGenerator.extract_article("prod@#$uct!")
        assert "prod" in result or "_" in result
    
    def test_generate_output_name_plate(self):
        """Test output name generation for plates."""
        name = NameGenerator.generate_output_name("12345", "PLATE", 0)
        assert name == "12345_1.png"
    
    def test_generate_output_name_product(self):
        """Test output name generation for products."""
        name = NameGenerator.generate_output_name("67890", "PRODUCT", 0)
        assert name == "67890_2.png"
    
    def test_generate_output_name_lifestyle(self):
        """Test output name generation for lifestyle."""
        name = NameGenerator.generate_output_name("11111", "LIFESTYLE", 0)
        assert name == "11111_3.png"
    
    def test_generate_output_name_with_index(self):
        """Test output name with multiple items of same type."""
        name = NameGenerator.generate_output_name("12345", "PRODUCT", 1)
        assert name == "12345_2(1).png"
        
        name = NameGenerator.generate_output_name("12345", "PRODUCT", 2)
        assert name == "12345_2(2).png"
    
    def test_generate_output_name_custom_extension(self):
        """Test custom file extension."""
        name = NameGenerator.generate_output_name(
            "12345", "PRODUCT", 0, extension=".jpg"
        )
        assert name == "12345_2.jpg"
