"""
AI Brain module for image context detection and classification.

Uses CLIP model for zero-shot classification and knowledge base matching.
"""

import logging
import os
from typing import List, Tuple, Optional, Dict, Any

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Check AI availability
AI_AVAILABLE = False
try:
    import torch
    import torch.nn.functional as F
    from transformers import CLIPProcessor, CLIPModel, logging as hf_logging
    hf_logging.set_verbosity_error()
    AI_AVAILABLE = True
except ImportError:
    logger.warning("AI modules not found. AI features disabled.")


class Brain:
    """
    AI-powered image analysis engine.
    
    Provides context detection, classification, and similarity matching
    using CLIP model and a knowledge base of reference images.
    """
    
    def __init__(self, knowledge_base_dir: str = "knowledge_base"):
        """
        Initialize the AI Brain.
        
        Args:
            knowledge_base_dir: Path to directory containing reference images
        """
        self.model: Optional[Any] = None
        self.processor: Optional[Any] = None
        self.knowledge_base_dir = knowledge_base_dir
        self.knowledge_base: Dict[str, List] = {"PLATE": [], "PRODUCT": [], "LIFESTYLE": []}
        
        if AI_AVAILABLE:
            self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Load CLIP model and processor."""
        try:
            from photo_agent.src.core.config import Config
            self.model = CLIPModel.from_pretrained(Config.AI_MODEL_NAME)
            self.processor = CLIPProcessor.from_pretrained(Config.AI_MODEL_NAME)
            self._load_knowledge_base()
            logger.info("AI Brain initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI Brain: {e}")
            self.model = None
            self.processor = None
    
    def _safe_normalize(self, embed: Any) -> Optional[Any]:
        """
        Safely normalize embeddings to unit vectors.
        
        Args:
            embed: Input embedding (tensor, object with attributes, or array-like)
            
        Returns:
            Normalized embedding or None if normalization fails
        """
        if not isinstance(embed, torch.Tensor):
            if hasattr(embed, 'image_embeds'):
                embed = embed.image_embeds
            elif hasattr(embed, 'pooler_output'):
                embed = embed.pooler_output
            else:
                try:
                    embed = torch.tensor(embed)
                except (TypeError, ValueError):
                    return None
        
        return F.normalize(embed, p=2, dim=-1)
    
    def _load_knowledge_base(self) -> None:
        """Load reference images from knowledge base directory."""
        if not os.path.exists(self.knowledge_base_dir):
            for label in self.knowledge_base:
                os.makedirs(os.path.join(self.knowledge_base_dir, label), exist_ok=True)
            logger.info("Created empty knowledge base directories")
            return
        
        count = 0
        for label in self.knowledge_base:
            folder = os.path.join(self.knowledge_base_dir, label)
            if not os.path.exists(folder):
                continue
            
            for fname in os.listdir(folder):
                if fname.lower().endswith(('jpg', 'png', 'jpeg', 'webp')):
                    try:
                        img = Image.open(os.path.join(folder, fname)).convert("RGB")
                        inputs = self.processor(images=img, return_tensors="pt")
                        with torch.no_grad():
                            raw = self.model.get_image_features(**inputs)
                        embed = self._safe_normalize(raw)
                        if embed is not None:
                            self.knowledge_base[label].append(embed)
                            count += 1
                    except Exception as e:
                        logger.debug(f"Failed to load {fname}: {e}")
        
        logger.info(f"Knowledge Base loaded: {count} reference images ready")
    
    def predict_context_strip(self, strip_pil: Image.Image) -> float:
        """
        Predict whether an image strip contains solid background or textured surface.
        
        Args:
            strip_pil: PIL Image of a strip from image edge
            
        Returns:
            Probability of solid background (0.0 to 1.0)
        """
        if self.model is None:
            return 0.5
        
        labels = [
            "solid empty studio background",
            "textured interior lifestyle surface"
        ]
        
        inputs = self.processor(
            text=labels,
            images=strip_pil,
            return_tensors="pt",
            padding=True
        )
        
        with torch.no_grad():
            probs = self.model(**inputs).logits_per_image.softmax(dim=1).numpy()[0]
        
        return float(probs[0])
    
    def predict_full(self, image_pil: Image.Image) -> Tuple[str, float, str]:
        """
        Predict image context type using knowledge base and zero-shot classification.
        
        Args:
            image_pil: Full PIL Image to classify
            
        Returns:
            Tuple of (label, confidence, source) where:
                - label: One of "PLATE", "PRODUCT", "LIFESTYLE"
                - confidence: Confidence score (0.0 to 1.0)
                - source: "KB_MATCH" if matched knowledge base, "ZERO_SHOT" otherwise
        """
        if self.model is None:
            return "PRODUCT", 0.0, "NO_AI"
        
        # Get image embedding
        inputs = self.processor(images=image_pil, return_tensors="pt")
        with torch.no_grad():
            raw = self.model.get_image_features(**inputs)
        img_embed = self._safe_normalize(raw)
        
        # Try knowledge base matching first
        best_sim = -1.0
        best_label = None
        
        for label, embeds in self.knowledge_base.items():
            for ref_embed in embeds:
                sim = torch.mm(img_embed, ref_embed.T).item()
                if sim > best_sim:
                    best_sim = sim
                    best_label = label
        
        from photo_agent.src.core.config import Config
        if best_sim > Config.SIMILARITY_THRESHOLD:
            return best_label, float(best_sim), "KB_MATCH"
        
        # Fall back to zero-shot classification
        labels = ["PRODUCT", "PLATE", "LIFESTYLE"]
        prompts = [
            "a packaged commercial product",
            "a food plate top view",
            "lifestyle food interior decorations"
        ]
        
        inputs = self.processor(
            text=prompts,
            images=image_pil,
            return_tensors="pt",
            padding=True
        )
        
        with torch.no_grad():
            probs = self.model(**inputs).logits_per_image.softmax(dim=1).numpy()[0]
        
        idx = np.argmax(probs)
        return labels[idx], float(probs[idx]), "ZERO_SHOT"
    
    def reload_knowledge_base(self) -> None:
        """Reload knowledge base from disk (useful after adding new reference images)."""
        if self.model is not None:
            self.knowledge_base = {"PLATE": [], "PRODUCT": [], "LIFESTYLE": []}
            self._load_knowledge_base()
