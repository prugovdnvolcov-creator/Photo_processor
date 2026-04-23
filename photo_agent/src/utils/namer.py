"""
Name generation utilities for processed images.

Provides article extraction and naming logic for output files.
"""

import re
from typing import Optional


class NameGenerator:
    """
    Utility class for generating output filenames from input metadata.
    
    Extracts article numbers or generates clean identifiers from
    folder names and filenames.
    """
    
    @staticmethod
    def extract_article(text: str) -> str:
        """
        Extract article number or generate clean identifier from text.
        
        Priority order:
        1. Long numeric sequences (4-10 digits)
        2. Any numeric sequence
        3. Cleaned text with special characters replaced
        
        Args:
            text: Input text (filename, folder name, etc.)
            
        Returns:
            Extracted article number or cleaned identifier
        """
        # Try to find long numeric sequences first (likely article numbers)
        match_long = re.search(r'(\d{4,10})', text)
        if match_long:
            return match_long.group(1)
        
        # Fall back to any numeric sequence
        match_any = re.search(r'(\d+)', text)
        if match_any:
            return match_any.group(1)
        
        # No numbers found: clean the text
        clean = re.sub(r'[^\w\-]', '_', text)
        return clean if clean else "unknown"
    
    @staticmethod
    def generate_output_name(
        article: str,
        context_type: str,
        index: int,
        extension: str = ".png"
    ) -> str:
        """
        Generate complete output filename.
        
        Args:
            article: Article number or identifier
            context_type: One of "PLATE", "PRODUCT", "LIFESTYLE"
            index: Sequence number within type (0 for first)
            extension: File extension (default: .png)
            
        Returns:
            Complete filename string
        """
        type_suffixes = {
            'PLATE': '_1',
            'PRODUCT': '_2',
            'LIFESTYLE': '_3'
        }
        
        suffix = type_suffixes.get(context_type, '_0')
        index_part = "" if index == 0 else f"({index})"
        
        return f"{article}{suffix}{index_part}{extension}"
