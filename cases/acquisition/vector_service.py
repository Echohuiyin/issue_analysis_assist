import numpy as np
from typing import List, Dict, Any, Optional
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self, model: str = "qwen2.5:0.5b", llm_type: str = "ollama"):
        self.model = model
        self.llm_type = llm_type.lower()
        self.embedding_dim = 4096

    def _is_ollama_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                return any(self.model.split(':')[0] in name for name in model_names)
        except Exception:
            return False
        return False

    def generate_embedding(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.embedding_dim
        try:
            if self.llm_type == "ollama" and self._is_ollama_available():
                # Use Ollama HTTP API for embedding generation
                response = requests.post(
                    "http://localhost:11434/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    embedding = response.json()["embedding"]
                    logger.info(f"Generated embedding using Ollama with dimension: {len(embedding)}")
                    return embedding
            return self._fallback_embedding(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return self._fallback_embedding(text)

    def _fallback_embedding(self, text: str) -> List[float]:
        char_set = "abcdefghijklmnopqrstuvwxyz0123456789"
        text = text.lower()
        freq = {c: 0 for c in char_set}
        for char in text:
            if char in freq:
                freq[char] += 1
        total = sum(freq.values())
        if total == 0:
            return [0.0] * self.embedding_dim
        embedding = [freq[c] / total for c in char_set]
        while len(embedding) < self.embedding_dim:
            embedding.append(0.0)
        return embedding[:self.embedding_dim]

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2:
            return 0.0
        try:
            min_len = min(len(vec1), len(vec2))
            vec1 = vec1[:min_len]
            vec2 = vec2[:min_len]
            a = np.array(vec1)
            b = np.array(vec2)
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return float(dot_product / (norm_a * norm_b))
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {str(e)}")
            return 0.0

    def find_similar(self, query_embedding: List[float], cases: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        if not query_embedding or not cases:
            return []
        similar_cases = []
        for case in cases:
            case_embedding = case.get("embedding", [])
            if case_embedding:
                similarity = self.cosine_similarity(query_embedding, case_embedding)
                similar_cases.append({
                    "case": case,
                    "similarity": similarity
                })
        similar_cases.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_cases[:top_k]

def get_vector_service(model: str = "qwen:1.8b", llm_type: str = "ollama") -> VectorService:
    return VectorService(model=model, llm_type=llm_type)