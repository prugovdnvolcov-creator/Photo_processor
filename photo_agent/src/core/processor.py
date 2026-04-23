"""
Main image processor module.

Orchestrates the complete image processing pipeline including
context detection, background removal, geometric analysis,
and final composition.
"""

import gc
import logging
import math
import os
from typing import Dict, List, Optional, Tuple, Any

import cv2
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from rembg import remove, new_session

from photo_agent.src.core.config import Config
from photo_agent.src.core.geometry import GeometryExpert
from photo_agent.src.ai.brain import Brain


logger = logging.getLogger(__name__)


class Processor:
    """
    Main image processing engine.
    
    Combines AI-based context detection with geometric analysis
    to produce professionally composed product images.
    """
    
    def __init__(self, knowledge_base_dir: str = "knowledge_base"):
        """
        Initialize the processor.
        
        Args:
            knowledge_base_dir: Path to knowledge base directory
        """
        self.session = new_session("isnet-general-use")
        self.brain = Brain(knowledge_base_dir)
    
    def process(self, image_path: str) -> Tuple[Optional[Image.Image], Optional[str]]:
        """
        Process a single image through the complete pipeline.
        
        Args:
            image_path: Path to input image file
            
        Returns:
            Tuple of (processed_image, context_type) or (None, None) on error
        """
        filename = os.path.basename(image_path)
        logger.info(f"--- Analyzing: {filename} ---")
        
        try:
            # Load and prepare image
            orig = Image.open(image_path).convert("RGBA")
            orig = ImageOps.exif_transpose(orig)
            orig_rgb = orig.convert("RGB")
            W, H = orig.size
            
            # Analyze background from edge strips
            strip_width = int(W * Config.STRIP_WIDTH_RATIO)
            strip_left = orig_rgb.crop((0, 0, strip_width, H))
            strip_right = orig_rgb.crop((W - strip_width, 0, W, H))
            
            cv_left = cv2.cvtColor(np.array(strip_left), cv2.COLOR_RGB2GRAY)
            cv_right = cv2.cvtColor(np.array(strip_right), cv2.COLOR_RGB2GRAY)
            
            laplacian_variance = np.mean([
                cv2.Laplacian(cv_left, cv2.CV_64F).var(),
                cv2.Laplacian(cv_right, cv2.CV_64F).var()
            ])
            
            # Get AI prediction
            ai_label, ai_confidence, ai_source = self.brain.predict_full(orig_rgb)
            
            # Generate segmentation mask
            try:
                mask_img = remove(orig, session=self.session, only_mask=True)
            except Exception:
                mask_img = Image.new("L", (W, H), 0)
            
            # Make decision on context type
            model_type = self._decide_context_type(
                ai_label, ai_confidence, ai_source,
                laplacian_variance, orig_rgb, mask_img
            )
            
            # Get bounding boxes and geometric properties
            core_bbox, full_bbox, solidity, circularity = GeometryExpert.get_bboxes(
                orig_rgb, mask_img, model_type
            )
            
            # Classify object shape
            shape = self._classify_shape(core_bbox)
            
            logger.info(
                f"  > Decision: {model_type} | Shape: {shape} | "
                f"Laplacian: {laplacian_variance:.1f}"
            )
            
            # Scale and center the image
            canvas = self._compose_image(
                orig_rgb, core_bbox, full_bbox,
                model_type, shape, W, H
            )
            
            # Apply final enhancements
            canvas = ImageEnhance.Sharpness(canvas).enhance(Config.FINAL_SHARPNESS)
            canvas = ImageEnhance.Contrast(canvas).enhance(Config.FINAL_CONTRAST)
            
            # Cleanup
            del orig, orig_rgb, mask_img
            gc.collect()
            
            return canvas, model_type
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}", exc_info=True)
            return None, None
    
    def _decide_context_type(
        self,
        ai_label: str,
        ai_confidence: float,
        ai_source: str,
        laplacian_variance: float,
        orig_rgb: Image.Image,
        mask_img: Image.Image
    ) -> str:
        """
        Determine final context type based on multiple signals.
        
        Args:
            ai_label: Initial AI prediction label
            ai_confidence: AI confidence score
            ai_source: AI prediction source ("KB_MATCH" or "ZERO_SHOT")
            laplacian_variance: Background texture measure
            orig_rgb: Original RGB image
            mask_img: Segmentation mask
            
        Returns:
            Final context type ("PLATE", "PRODUCT", or "LIFESTYLE")
        """
        model_type = ai_label
        
        # Override logic for non-knowledge-base matches
        if ai_source != "KB_MATCH":
            # High background texture indicates lifestyle
            if laplacian_variance > Config.BG_LAPLACIAN_THRESHOLD:
                model_type = "LIFESTYLE"
            
            # Validate plate detection with geometry
            elif ai_label == "PLATE":
                _, _, solidity, circularity = GeometryExpert.get_bboxes(
                    orig_rgb, mask_img, 'PLATE'
                )
                if (solidity < Config.PLATE_SOLIDITY_MIN or 
                    circularity < Config.PLATE_CIRCULARITY_MIN):
                    model_type = "PRODUCT"
            
            # Low confidence defaults to product
            elif ai_confidence < Config.AI_CONFIDENCE_THRESHOLD:
                model_type = "PRODUCT"
        
        return model_type
    
    def _classify_shape(self, bbox: Tuple[int, int, int, int]) -> str:
        """
        Classify object shape based on aspect ratio.
        
        Args:
            bbox: Bounding box (x1, y1, x2, y2)
            
        Returns:
            Shape classification string
        """
        x1, y1, x2, y2 = bbox
        width = max(1, x2 - x1)
        height = max(1, y2 - y1)
        aspect_ratio = width / height
        
        if aspect_ratio < Config.NORMAL_ASPECT_THRESHOLD:
            return "THIN_VERT" if aspect_ratio < 0.5 else "THICK_VERT"
        elif aspect_ratio > Config.LONG_ASPECT_THRESHOLD:
            return "LONG_HORIZ"
        else:
            return "NORMAL_HORIZ"
    
    def _compose_image(
        self,
        orig_rgb: Image.Image,
        core_bbox: Tuple[int, int, int, int],
        full_bbox: Tuple[int, int, int, int],
        model_type: str,
        shape: str,
        orig_w: int,
        orig_h: int
    ) -> Image.Image:
        """
        Compose final image on canvas with proper scaling and centering.
        
        Args:
            orig_rgb: Original RGB image
            core_bbox: Core bounding box
            full_bbox: Full/reconstructed bounding box
            model_type: Context type
            shape: Object shape classification
            orig_w: Original image width
            orig_h: Original image height
            
        Returns:
            Composed PIL Image on canvas
        """
        canvas_w, canvas_h = Config.CANVAS_W, Config.CANVAS_H
        
        # Select appropriate bounding box and margins
        target_bbox = full_bbox if model_type == 'PLATE' else core_bbox
        
        if model_type == 'LIFESTYLE':
            margins = Config.MARGINS_LIFESTYLE
        elif model_type == 'PLATE':
            margins = Config.MARGINS_PLATE
        else:
            margins = Config.MARGINS_PRODUCT.get(
                shape,
                Config.MARGINS_PRODUCT["DEFAULT"]
            )
        
        # Calculate dimensions
        tx1, ty1, tx2, ty2 = target_bbox
        tw = max(1, tx2 - tx1)
        th = max(1, ty2 - ty1)
        
        # Calculate scale factor
        if model_type == 'LIFESTYLE':
            scale = max(canvas_w / orig_w, canvas_h / orig_h) * 1.3
        else:
            scale = min(
                (canvas_w - margins['side'] * 2) / tw,
                (canvas_h - (margins['top'] + margins['bottom'])) / th
            )
            if model_type == 'PLATE':
                scale *= 0.98
        
        # Resize image
        fw, fh = int(orig_w * scale), int(orig_h * scale)
        resized = orig_rgb.resize((fw, fh), Image.LANCZOS)
        
        # Precision centering
        pad_x = (canvas_w - (tw * scale)) / 2
        pad_y = (canvas_h - (th * scale)) / 2
        shift_x = int(pad_x - (tx1 * scale))
        shift_y = int(pad_y - (ty1 * scale))
        
        # Clamp shifts for lifestyle images
        if model_type == 'LIFESTYLE':
            shift_x = max(min(0, shift_x), canvas_w - fw)
            shift_y = max(min(0, shift_y), canvas_h - fh)
        
        # Create canvas
        if model_type == 'LIFESTYLE':
            # Blur original as background
            canvas = resized.resize((canvas_w, canvas_h), Image.BICUBIC)
            canvas = canvas.filter(ImageFilter.GaussianBlur(100))
        else:
            # Solid color background
            canvas = Image.new("RGB", (canvas_w, canvas_h), Config.PRODUCT_BG_COLOR)
        
        # Paste resized image
        canvas.paste(resized, (shift_x, shift_y))
        
        return canvas
