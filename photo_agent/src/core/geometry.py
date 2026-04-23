"""
Geometry analysis module for object detection and shape reconstruction.

Provides bounding box detection, ellipse reconstruction for plates,
and geometric property calculations.
"""

import math
from typing import Tuple, List

import cv2
import numpy as np
from PIL import Image

from photo_agent.src.core.config import Config


class GeometryExpert:
    """
    Expert class for geometric analysis of images.
    
    Handles bounding box detection, shape classification,
    and ellipse reconstruction for plate objects.
    """
    
    @staticmethod
    def get_bboxes(
        pil_orig: Image.Image,
        pil_mask: Image.Image,
        model_type: str
    ) -> Tuple[Tuple[int, int, int, int], Tuple[int, int, int, int], float, float]:
        """
        Get core and full bounding boxes with geometric properties.
        
        Args:
            pil_orig: Original PIL Image
            pil_mask: Segmentation mask as PIL Image
            model_type: Type of object ("PLATE", "PRODUCT", "LIFESTYLE")
            
        Returns:
            Tuple of (core_bbox, full_bbox, solidity, circularity) where:
                - core_bbox: Tight bounding box around detected object
                - full_bbox: Reconstructed bounding box (expanded for plates)
                - solidity: Ratio of object area to convex hull area
                - circularity: Measure of how circular the object is
        """
        W, H = pil_orig.size
        mask_arr = np.array(pil_mask.convert("L"))
        
        # Erosion to remove noisy pixels from mask
        kernel = np.ones((5, 5), np.uint8)
        mask_clean = cv2.erode(mask_arr, kernel, iterations=1)
        
        contours, _ = cv2.findContours(
            mask_clean,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        core_bbox = (0, 0, W, H)
        solidity = 0.0
        circularity = 0.0
        
        if contours:
            contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(contour)
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0
            
            perimeter = cv2.arcLength(contour, True)
            circularity = (4 * math.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0
            
            x, y, w, h = cv2.boundingRect(contour)
            core_bbox = (x, y, x + w, y + h)
        
        # For plates, perform geometric reconstruction
        if model_type == 'PLATE':
            full_bbox = GeometryExpert._reconstruct_ellipse(pil_orig, core_bbox)
        else:
            full_bbox = core_bbox
        
        return core_bbox, full_bbox, solidity, circularity
    
    @staticmethod
    def _reconstruct_ellipse(
        pil_orig: Image.Image,
        core_bbox: Tuple[int, int, int, int]
    ) -> Tuple[int, int, int, int]:
        """
        Reconstruct full ellipse for plate objects.
        
        Analyzes image edges to find plate rim arcs and fits
        a complete ellipse, handling cases where parts of the
        plate blend with the background.
        
        Args:
            pil_orig: Original PIL Image
            core_bbox: Core bounding box around food/plate center
            
        Returns:
            Reconstructed bounding box encompassing the full plate
        """
        W, H = pil_orig.size
        cv_img = cv2.cvtColor(np.array(pil_orig), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        
        # 1. Enhance local shadows (plate edges are always slightly darker)
        clahe = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8)
        )
        cl_gray = clahe.apply(gray)
        
        # 2. Edge detection using Canny
        sensitivity = Config.PLATE_RIM_SENSITIVITY
        edges = cv2.Canny(cl_gray, sensitivity, sensitivity * 3)
        
        # 3. Filter points: only keep those around the food area
        points = np.column_stack(np.where(edges > 0))
        if len(points) < 20:
            return GeometryExpert._fallback_expand(core_bbox, W, H)
        
        cx_food = (core_bbox[0] + core_bbox[2]) / 2
        cy_food = (core_bbox[1] + core_bbox[3]) / 2
        radius_est = max(
            core_bbox[2] - core_bbox[0],
            core_bbox[3] - core_bbox[1]
        ) / 2
        
        valid_points = []
        for p in points:
            dist = math.hypot(p[1] - cx_food, p[0] - cy_food)
            # Keep points at 0.8 to 1.8 times the estimated radius
            if radius_est * 0.8 < dist < radius_est * 1.8:
                valid_points.append((p[1], p[0]))  # OpenCV format (x, y)
        
        if len(valid_points) < 15:
            return GeometryExpert._fallback_expand(core_bbox, W, H)
        
        # 4. Fit ellipse mathematically from arc points
        try:
            ellipse = cv2.fitEllipse(
                np.array(valid_points, dtype=np.float32)
            )
            (ex, ey), (ew, eh), angle = ellipse
            
            # Validate ellipse reasonableness
            if ew > W or eh > H or ew < (core_bbox[2] - core_bbox[0]):
                raise ValueError("Ellipse dimensions out of bounds")
            
            nx1 = max(0, int(ex - ew / 2))
            ny1 = max(0, int(ey - eh / 2))
            nx2 = min(W, int(ex + ew / 2))
            ny2 = min(H, int(ey + eh / 2))
            
            return (nx1, ny1, nx2, ny2)
            
        except Exception:
            return GeometryExpert._fallback_expand(core_bbox, W, H)
    
    @staticmethod
    def _fallback_expand(
        core_bbox: Tuple[int, int, int, int],
        width: int,
        height: int
    ) -> Tuple[int, int, int, int]:
        """
        Fallback method: expand core bbox by 18% as safe zone.
        
        Args:
            core_bbox: Core bounding box
            width: Image width
            height: Image height
            
        Returns:
            Expanded bounding box
        """
        x1, y1, x2, y2 = core_bbox
        pw = (x2 - x1) * 0.18
        ph = (y2 - y1) * 0.18
        
        return (
            max(0, int(x1 - pw)),
            max(0, int(y1 - ph)),
            min(width, int(x2 + pw)),
            min(height, int(y2 + ph))
        )
