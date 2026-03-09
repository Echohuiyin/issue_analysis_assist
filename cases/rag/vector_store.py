import json
import math
import os
from collections import Counter
from pathlib import Path
from typing import Dict, List


def _tokenize(text: str) -> List[str]:
    normalized = (text or "").lower()
    tokens = []
    current = []
    for ch in normalized:
        if ch.isalnum() or ch in ("_", "-"):
            current.append(ch)
        else:
            if current:
                tokens.append("".join(current))
                current = []
    if current:
        tokens.append("".join(current))
    return [t for t in tokens if len(t) >= 2]


def _vectorize(text: str) -> Dict[str, float]:
    tokens = _tokenize(text)
    if not tokens:
        return {}
    counts = Counter(tokens)
    norm = math.sqrt(sum(v * v for v in counts.values()))
    if norm == 0:
        return {}
    return {k: v / norm for k, v in counts.items()}


def _cosine_sim(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(k, 0.0) for k, v in a.items())


class LocalVectorStore:
    """Lightweight local vector store backed by JSON file."""

    def __init__(self, storage_path: str = ""):
        base = Path(storage_path) if storage_path else Path(__file__).resolve().parents[2] / "rag_store"
        base.mkdir(parents=True, exist_ok=True)
        self._file = base / "kernel_cases_vectors.json"
        self._records = self._load()

    def _load(self) -> List[Dict]:
        if not self._file.exists():
            return []
        try:
            return json.loads(self._file.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save(self) -> None:
        self._file.write_text(json.dumps(self._records, ensure_ascii=False, indent=2), encoding="utf-8")

    def _build_content(self, case_data: Dict) -> str:
        return "\n".join([
            case_data.get("title", ""),
            case_data.get("module", ""),
            case_data.get("phenomenon", ""),
            case_data.get("problem_analysis", "") or case_data.get("analysis_process", ""),
            case_data.get("related_code", ""),
            case_data.get("root_cause", ""),
            case_data.get("solution", ""),
        ])

    def upsert_case(self, case_id: str, case_data: Dict) -> Dict:
        content = self._build_content(case_data)
        vector = _vectorize(content)
        payload = {
            "case_id": case_id,
            "content": content[:12000],
            "vector": vector,
            "title": case_data.get("title", ""),
            "module": case_data.get("module", "other"),
            "source": case_data.get("source", ""),
            "url": case_data.get("reference_url", ""),
        }

        updated = False
        for idx, item in enumerate(self._records):
            if item.get("case_id") == case_id:
                self._records[idx] = payload
                updated = True
                break
        if not updated:
            self._records.append(payload)
        self._save()
        return {"success": True, "message": "Vector upserted", "case_id": case_id}

    def delete_case(self, case_id: str) -> Dict:
        before = len(self._records)
        self._records = [r for r in self._records if r.get("case_id") != case_id]
        self._save()
        return {"success": True, "deleted": before - len(self._records), "case_id": case_id}

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        qv = _vectorize(query)
        scored = []
        for item in self._records:
            score = _cosine_sim(qv, item.get("vector", {}))
            if score > 0:
                scored.append({
                    "case_id": item.get("case_id"),
                    "title": item.get("title"),
                    "module": item.get("module"),
                    "source": item.get("source"),
                    "url": item.get("url"),
                    "score": round(score, 4),
                })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:max(1, top_k)]


_VECTOR_STORE = None


def get_local_vector_store() -> LocalVectorStore:
    global _VECTOR_STORE
    if _VECTOR_STORE is None:
        storage_path = os.getenv("LOCAL_RAG_STORE_PATH", "")
        _VECTOR_STORE = LocalVectorStore(storage_path=storage_path)
    return _VECTOR_STORE
