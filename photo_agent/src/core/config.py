"""
Configuration module for the Photo Agent.

Contains all configurable parameters, thresholds, and constants
used throughout the image processing pipeline.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class CanvasConfig:
    """Canvas dimensions and background settings."""
    WIDTH: int = 1280
    HEIGHT: int = 840
    PRODUCT_BG_COLOR: str = "#FAFAFA"


@dataclass
class AnalysisConfig:
    """Context analysis thresholds."""
    STRIP_WIDTH_RATIO: float = 0.15
    BG_LAPLACIAN_THRESHOLD: float = 32.0
    BG_ENTROPY_THRESHOLD: float = 5.2


@dataclass
class AIConfig:
    """AI model parameters."""
    CONFIDENCE_THRESHOLD: float = 0.80
    SIMILARITY_THRESHOLD: float = 0.92
    MODEL_NAME: str = "openai/clip-vit-base-patch32"


@dataclass
class BackgroundPhysicsConfig:
    """Background physics detection thresholds."""
    WHITE_PEAK_THRESHOLD: int = 230
    MAX_SATURATION_THRESHOLD: int = 15
    HIST_SPIKE_MIN: float = 0.75


@dataclass
class PlateGeometryConfig:
    """Plate geometry detection parameters."""
    SOLIDITY_MIN: float = 0.93
    CIRCULARITY_MIN: float = 0.74
    RIM_SENSITIVITY: int = 8


@dataclass
class VisualEnhancementConfig:
    """Final visual enhancement settings."""
    FINAL_SHARPNESS: float = 1.15
    FINAL_CONTRAST: float = 1.05


@dataclass
class ShapeConfig:
    """Object shape classification thresholds."""
    BOTTLE_MAX_ASPECT_RATIO: float = 0.65
    BOTTLE_NECK_THRESHOLD: float = 0.82
    THIN_ASPECT_THRESHOLD: float = 0.45
    NORMAL_ASPECT_THRESHOLD: float = 1.15
    LONG_ASPECT_THRESHOLD: float = 1.75
    SMALL_COVERAGE_THRESHOLD: float = 0.15


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
    DOWNLOAD_DIR: str = 'downloads_temp'
    OUTPUT_DIR: str = 'output_processed'
    KNOWLEDGE_BASE_DIR: str = 'knowledge_base'
    LOG_FILE: str = 'agent_v107.log'


class Config:
    """Main configuration class aggregating all sub-configurations."""
    
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
