"""
AI Brain module for image context detection and classification.

Uses CLIP model for zero-shot classification and knowledge base matching.
Implements singleton pattern for model caching to avoid redundant loading.
"""

import logging
import os
from typing import List, Tuple, Optional, Dict, Any
from threading import Lock

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


class ModelCache:
    """
    Singleton cache for AI models to prevent redundant loading.
    
    Thread-safe implementation that ensures only one instance
    of each model is loaded across all Brain instances.
    """
    _instance: Optional['ModelCache'] = None
    _lock = Lock()
    
    def __new__(cls) -> 'ModelCache':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._models: Dict[str, Tuple[Any, Any]] = {}
        self._initialized = True
    
    def get_model(self, model_name: str, cache_dir: Optional[str] = None) -> Tuple[Optional[Any], Optional[Any]]:
        """
        Get or load a CLIP model and processor.
        
        Args:
            model_name: HuggingFace model identifier
            cache_dir: Optional custom cache directory
            
        Returns:
            Tuple of (model, processor) or (None, None) if unavailable
        """
        if not AI_AVAILABLE:
            return None, None
        
        cache_key = f"{model_name}:{cache_dir}"
        
        if cache_key in self._models:
            logger.debug(f"Using cached model: {model_name}")
            return self._models[cache_key]
        
        try:
            logger.info(f"Loading AI model: {model_name}")
            model_kwargs = {}
            if cache_dir:
                model_kwargs['cache_dir'] = cache_dir
            
            model = CLIPModel.from_pretrained(model_name, **model_kwargs)
            processor = CLIPProcessor.from_pretrained(model_name, **model_kwargs)
            
            # Move to GPU if available and enabled
            from photo_agent.src.core.config import Config
            if Config.ENABLE_AI and Config.PERFORMANCE.ENABLE_GPU and torch.cuda.is_available():
                model = model.to('cuda')
                logger.info("Model loaded on GPU")
            elif Config.ENABLE_AI and torch.cuda.is_available():
                model = model.to('cuda')
                logger.info("Model loaded on GPU")
            else:
                logger.info("Model loaded on CPU")
            
            self._models[cache_key] = (model, processor)
            return model, processor
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return None, None
    
    def clear_cache(self) -> None:
        """Clear all cached models and free memory."""
        import gc
        with self._lock:
            self._models.clear()
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()


class Brain:
    """
    AI-powered image analysis engine.
    
    Provides context detection, classification, and similarity matching
    using CLIP model and a knowledge base of reference images.
    Uses ModelCache singleton for efficient model reuse.
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
        """Load CLIP model from cache or initialize new instance."""
        try:
            from photo_agent.src.core.config import Config
            
            if not Config.ENABLE_AI:
                logger.info("AI is disabled by configuration")
                return
            
            cache = ModelCache()
            self.model, self.processor = cache.get_model(
                Config.AI_MODEL_NAME, 
                Config.AI_CACHE_DIR
            )
            
            if self.model is not None:
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
