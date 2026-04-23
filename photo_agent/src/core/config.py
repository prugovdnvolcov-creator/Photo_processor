"""
Configuration module for the Photo Agent.

Contains all configurable parameters, thresholds, and constants
used throughout the image processing pipeline.

Supports environment variable overrides and YAML configuration files.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from pathlib import Path


def _get_env_float(name: str, default: float) -> float:
    """Get float value from environment variable or return default."""
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _get_env_int(name: str, default: int) -> int:
    """Get int value from environment variable or return default."""
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_env_str(name: str, default: str) -> str:
    """Get string value from environment variable or return default."""
    return os.environ.get(name, default)


@dataclass
class CanvasConfig:
    """Canvas dimensions and background settings."""
    WIDTH: int = 1280
    HEIGHT: int = 840
    PRODUCT_BG_COLOR: str = "#FAFAFA"
    
    def __post_init__(self):
        # Apply environment variable overrides
        self.WIDTH = _get_env_int('CANVAS_WIDTH', self.WIDTH)
        self.HEIGHT = _get_env_int('CANVAS_HEIGHT', self.HEIGHT)
        self.PRODUCT_BG_COLOR = _get_env_str('PRODUCT_BG_COLOR', self.PRODUCT_BG_COLOR)


@dataclass
class AnalysisConfig:
    """Context analysis thresholds."""
    STRIP_WIDTH_RATIO: float = 0.15
    BG_LAPLACIAN_THRESHOLD: float = 32.0
    BG_ENTROPY_THRESHOLD: float = 5.2
    
    def __post_init__(self):
        self.STRIP_WIDTH_RATIO = _get_env_float('STRIP_WIDTH_RATIO', self.STRIP_WIDTH_RATIO)
        self.BG_LAPLACIAN_THRESHOLD = _get_env_float('BG_LAPLACIAN_THRESHOLD', self.BG_LAPLACIAN_THRESHOLD)
        self.BG_ENTROPY_THRESHOLD = _get_env_float('BG_ENTROPY_THRESHOLD', self.BG_ENTROPY_THRESHOLD)


@dataclass
class AIConfig:
    """AI model parameters."""
    CONFIDENCE_THRESHOLD: float = 0.80
    SIMILARITY_THRESHOLD: float = 0.92
    MODEL_NAME: str = "openai/clip-vit-base-patch32"
    CACHE_DIR: Optional[str] = None
    ENABLE_AI: bool = True
    
    def __post_init__(self):
        self.CONFIDENCE_THRESHOLD = _get_env_float('AI_CONFIDENCE_THRESHOLD', self.CONFIDENCE_THRESHOLD)
        self.SIMILARITY_THRESHOLD = _get_env_float('SIMILARITY_THRESHOLD', self.SIMILARITY_THRESHOLD)
        self.MODEL_NAME = _get_env_str('AI_MODEL_NAME', self.MODEL_NAME)
        self.CACHE_DIR = os.environ.get('AI_CACHE_DIR', self.CACHE_DIR)
        self.ENABLE_AI = os.environ.get('ENABLE_AI', 'true').lower() != 'false'


@dataclass
class BackgroundPhysicsConfig:
    """Background physics detection thresholds."""
    WHITE_PEAK_THRESHOLD: int = 230
    MAX_SATURATION_THRESHOLD: int = 15
    HIST_SPIKE_MIN: float = 0.75
    
    def __post_init__(self):
        self.WHITE_PEAK_THRESHOLD = _get_env_int('WHITE_PEAK_THRESHOLD', self.WHITE_PEAK_THRESHOLD)
        self.MAX_SATURATION_THRESHOLD = _get_env_int('MAX_SATURATION_THRESHOLD', self.MAX_SATURATION_THRESHOLD)
        self.HIST_SPIKE_MIN = _get_env_float('HIST_SPIKE_MIN', self.HIST_SPIKE_MIN)


@dataclass
class PlateGeometryConfig:
    """Plate geometry detection parameters."""
    SOLIDITY_MIN: float = 0.93
    CIRCULARITY_MIN: float = 0.74
    RIM_SENSITIVITY: int = 8
    
    def __post_init__(self):
        self.SOLIDITY_MIN = _get_env_float('PLATE_SOLIDITY_MIN', self.SOLIDITY_MIN)
        self.CIRCULARITY_MIN = _get_env_float('PLATE_CIRCULARITY_MIN', self.CIRCULARITY_MIN)
        self.RIM_SENSITIVITY = _get_env_int('PLATE_RIM_SENSITIVITY', self.RIM_SENSITIVITY)


@dataclass
class VisualEnhancementConfig:
    """Final visual enhancement settings."""
    FINAL_SHARPNESS: float = 1.15
    FINAL_CONTRAST: float = 1.05
    
    def __post_init__(self):
        self.FINAL_SHARPNESS = _get_env_float('FINAL_SHARPNESS', self.FINAL_SHARPNESS)
        self.FINAL_CONTRAST = _get_env_float('FINAL_CONTRAST', self.FINAL_CONTRAST)


@dataclass
class ShapeConfig:
    """Object shape classification thresholds."""
    BOTTLE_MAX_ASPECT_RATIO: float = 0.65
    BOTTLE_NECK_THRESHOLD: float = 0.82
    THIN_ASPECT_THRESHOLD: float = 0.45
    NORMAL_ASPECT_THRESHOLD: float = 1.15
    LONG_ASPECT_THRESHOLD: float = 1.75
    SMALL_COVERAGE_THRESHOLD: float = 0.15
    
    def __post_init__(self):
        self.BOTTLE_MAX_ASPECT_RATIO = _get_env_float('BOTTLE_MAX_ASPECT_RATIO', self.BOTTLE_MAX_ASPECT_RATIO)
        self.BOTTLE_NECK_THRESHOLD = _get_env_float('BOTTLE_NECK_THRESHOLD', self.BOTTLE_NECK_THRESHOLD)
        self.THIN_ASPECT_THRESHOLD = _get_env_float('THIN_ASPECT_THRESHOLD', self.THIN_ASPECT_THRESHOLD)
        self.NORMAL_ASPECT_THRESHOLD = _get_env_float('NORMAL_ASPECT_THRESHOLD', self.NORMAL_ASPECT_THRESHOLD)
        self.LONG_ASPECT_THRESHOLD = _get_env_float('LONG_ASPECT_THRESHOLD', self.LONG_ASPECT_THRESHOLD)
        self.SMALL_COVERAGE_THRESHOLD = _get_env_float('SMALL_COVERAGE_THRESHOLD', self.SMALL_COVERAGE_THRESHOLD)


@dataclass
class MarginConfig:
    """Margin configurations for different object types."""
    PRODUCT: Dict[str, Dict[str, int]] = field(default_factory=dict)
    PLATE: Dict[str, int] = field(default_factory=dict)
    LIFESTYLE: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.PRODUCT:
            self.PRODUCT = {
                "THIN_VERT":     {"top": 90, "bottom": 90, "side": 430},
                "THICK_VERT":    {"top": 350, "bottom": 350, "side": 400},
                "THIN_BOTTLE":   {"top": 60, "bottom": 60, "side": 430},
                "THICK_BOTTLE":  {"top": 60, "bottom": 60, "side": 350},
                "SMALL_SQUARE":  {"top": 350, "bottom": 350, "side": 400},
                "NORMAL_SQUARE": {"top": 180, "bottom": 180, "side": 180},
                "SHORT_HORIZ":   {"top": 140, "bottom": 140, "side": 280},
                "NORMAL_HORIZ":  {"top": 350, "bottom": 350, "side": 400},
                "LONG_HORIZ":    {"top": 160, "bottom": 160, "side": 100},
                "DEFAULT":       {"top": 85, "bottom": 85, "side": 300}
            }
        if not self.PLATE:
            self.PLATE = {"top": 350, "bottom": 350, "side": 400}
        if not self.LIFESTYLE:
            self.LIFESTYLE = {"top": 0, "bottom": 0, "side": 0}


# Default margin instances
MARGIN_CONFIG = MarginConfig()


@dataclass
class PathConfig:
    """Directory and file path configurations."""
    DOWNLOAD_DIR: str = field(default_factory=lambda: _get_env_str('DOWNLOAD_DIR', 'downloads_temp'))
    OUTPUT_DIR: str = field(default_factory=lambda: _get_env_str('OUTPUT_DIR', 'output_processed'))
    KNOWLEDGE_BASE_DIR: str = field(default_factory=lambda: _get_env_str('KNOWLEDGE_BASE_DIR', 'knowledge_base'))
    LOG_FILE: str = field(default_factory=lambda: _get_env_str('LOG_FILE', 'agent_v107.log'))


@dataclass
class SecurityConfig:
    """Security-related configuration settings."""
    MAX_FILE_SIZE_MB: int = field(default_factory=lambda: _get_env_int('MAX_FILE_SIZE_MB', 50))
    ALLOWED_EXTENSIONS: tuple = field(default_factory=lambda: ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.tiff', '.heic'))
    MAX_URL_LENGTH: int = field(default_factory=lambda: _get_env_int('MAX_URL_LENGTH', 2048))
    ENABLE_PATH_SANITIZATION: bool = field(default_factory=lambda: os.environ.get('ENABLE_PATH_SANITIZATION', 'true').lower() != 'false')


@dataclass
class PerformanceConfig:
    """Performance tuning configuration."""
    ENABLE_GPU: bool = field(default_factory=lambda: os.environ.get('ENABLE_GPU', 'true').lower() != 'false')
    BATCH_SIZE: int = field(default_factory=lambda: _get_env_int('BATCH_SIZE', 1))
    NUM_WORKERS: int = field(default_factory=lambda: _get_env_int('NUM_WORKERS', 4))
    MEMORY_LIMIT_MB: int = field(default_factory=lambda: _get_env_int('MEMORY_LIMIT_MB', 4096))


class Config:
    """
    Main configuration class aggregating all sub-configurations.
    
    Provides centralized access to all configuration parameters
    with support for environment variable overrides.
    """
    
    # Paths
    PATHS = PathConfig()
    
    # Canvas
    CANVAS_W = CanvasConfig.WIDTH
    CANVAS_H = CanvasConfig.HEIGHT
    PRODUCT_BG_COLOR = CanvasConfig.PRODUCT_BG_COLOR
    
    # Analysis
    STRIP_WIDTH_RATIO = AnalysisConfig.STRIP_WIDTH_RATIO
    BG_LAPLACIAN_THRESHOLD = AnalysisConfig.BG_LAPLACIAN_THRESHOLD
    BG_ENTROPY_THRESHOLD = AnalysisConfig.BG_ENTROPY_THRESHOLD
    
    # AI
    AI_CONFIDENCE_THRESHOLD = AIConfig.CONFIDENCE_THRESHOLD
    SIMILARITY_THRESHOLD = AIConfig.SIMILARITY_THRESHOLD
    AI_MODEL_NAME = AIConfig.MODEL_NAME
    AI_CACHE_DIR = AIConfig.CACHE_DIR
    ENABLE_AI = AIConfig.ENABLE_AI
    
    # Background Physics
    WHITE_PEAK_THRESHOLD = BackgroundPhysicsConfig.WHITE_PEAK_THRESHOLD
    MAX_SATURATION_THRESHOLD = BackgroundPhysicsConfig.MAX_SATURATION_THRESHOLD
    HIST_SPIKE_MIN = BackgroundPhysicsConfig.HIST_SPIKE_MIN
    
    # Plate Geometry
    PLATE_SOLIDITY_MIN = PlateGeometryConfig.SOLIDITY_MIN
    PLATE_CIRCULARITY_MIN = PlateGeometryConfig.CIRCULARITY_MIN
    PLATE_RIM_SENSITIVITY = PlateGeometryConfig.RIM_SENSITIVITY
    
    # Visual Enhancement
    FINAL_SHARPNESS = VisualEnhancementConfig.FINAL_SHARPNESS
    FINAL_CONTRAST = VisualEnhancementConfig.FINAL_CONTRAST
    
    # Shape Classification
    BOTTLE_MAX_ASPECT_RATIO = ShapeConfig.BOTTLE_MAX_ASPECT_RATIO
    BOTTLE_NECK_THRESHOLD = ShapeConfig.BOTTLE_NECK_THRESHOLD
    THIN_ASPECT_THRESHOLD = ShapeConfig.THIN_ASPECT_THRESHOLD
    NORMAL_ASPECT_THRESHOLD = ShapeConfig.NORMAL_ASPECT_THRESHOLD
    LONG_ASPECT_THRESHOLD = ShapeConfig.LONG_ASPECT_THRESHOLD
    SMALL_COVERAGE_THRESHOLD = ShapeConfig.SMALL_COVERAGE_THRESHOLD
    
    # Margins
    MARGINS_PRODUCT = MARGIN_CONFIG.PRODUCT
    MARGINS_PLATE = MARGIN_CONFIG.PLATE
    MARGINS_LIFESTYLE = MARGIN_CONFIG.LIFESTYLE
    
    # Security
    SECURITY = SecurityConfig()
    
    # Performance
    PERFORMANCE = PerformanceConfig()
