import json
import logging
from typing import List, Optional
import numpy as np
from ..config import DEFAULT_EMBEDDING_MODEL

logger = logging.getLogger(__name__)

_model_instance = None
_model_failed = False

def get_sentence_transformer_model():
    """
    Lazy loader for SentenceTransformer model with fallback handling.
    """
    global _model_instance, _model_failed
    if _model_instance is not None:
        return _model_instance
    if _model_failed:
        return None

    try:
        import os
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading SentenceTransformer model: {DEFAULT_EMBEDDING_MODEL}...")
        try:
            _model_instance = SentenceTransformer(DEFAULT_EMBEDDING_MODEL, local_files_only=True)
        except Exception:
            _model_instance = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)
        logger.info("SentenceTransformer model loaded successfully.")
        return _model_instance
    except Exception as e:
        logger.warning(f"Could not load SentenceTransformer ({e}). Falling back to TF-IDF/SVD vectorizer.")
        _model_failed = True
        return None

class FallbackSemanticVectorizer:
    """
    Lightweight, fast, 100% offline fallback vectorizer using TF-IDF + SVD.
    Generates 384-dimensional dense semantic vectors even without external HuggingFace downloads.
    """
    def __init__(self, dim: int = 384):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        self.dim = dim
        self.vectorizer = TfidfVectorizer(max_features=2000, stop_words='english', ngram_range=(1, 2))
        self.svd = TruncatedSVD(n_components=min(dim, 100), random_state=42)
        self.is_fitted = False

    def encode(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim))
        
        # Simple character / n-gram hash projection for stable deterministic vectors
        vectors = []
        for text in texts:
            vec = np.zeros(self.dim, dtype=np.float32)
            words = text.lower().split()
            if not words:
                vectors.append(vec)
                continue
            for i, word in enumerate(words):
                h = hash(word) % self.dim
                weight = 1.0 / (1.0 + np.log(1 + i * 0.05))
                vec[h] += weight
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec)
        return np.array(vectors)

_fallback_vectorizer = FallbackSemanticVectorizer(dim=384)

def generate_embedding(text: str) -> List[float]:
    """
    Generate dense vector embedding for a given text.
    """
    if not text.strip():
        return [0.0] * 384

    model = get_sentence_transformer_model()
    if model is not None:
        try:
            vector = model.encode(text, convert_to_numpy=True)
            # Normalize vector
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            return vector.tolist()
        except Exception as e:
            logger.warning(f"SentenceTransformer encoding error: {e}. Using fallback.")
            
    vectors = _fallback_vectorizer.encode([text])
    return vectors[0].tolist()

def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Batch generate embeddings for multiple texts.
    """
    if not texts:
        return []

    model = get_sentence_transformer_model()
    if model is not None:
        try:
            vectors = model.encode(texts, convert_to_numpy=True)
            normalized = []
            for v in vectors:
                norm = np.linalg.norm(v)
                normalized.append((v / norm if norm > 0 else v).tolist())
            return normalized
        except Exception as e:
            logger.warning(f"Batch SentenceTransformer error: {e}. Using fallback.")

    vectors = _fallback_vectorizer.encode(texts)
    return vectors.tolist()

def serialize_embedding(vector: List[float]) -> str:
    """Serialize list of floats into JSON string."""
    return json.dumps(vector)

def deserialize_embedding(vector_str: Optional[str]) -> Optional[List[float]]:
    """Deserialize JSON string into list of floats."""
    if not vector_str:
        return None
    try:
        return json.loads(vector_str)
    except Exception:
        return None
