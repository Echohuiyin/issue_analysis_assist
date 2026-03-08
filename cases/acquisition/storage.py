import re
from typing import Dict
import uuid

from .classifier import module_classifier
from .cleaner import content_cleaner
from cases.rag import get_local_vector_store

# Django is optional for script-only mode.
try:
    from django.utils import timezone
    from cases.models import KernelCase
    DJANGO_AVAILABLE = True
except ImportError:
    timezone = None
    KernelCase = None
    DJANGO_AVAILABLE = False

KERNEL_VER_RE = re.compile(r'(?:Linux|kernel)\s*(\d+\.\d+[\.\d]*(?:-[\w.]+)?)', re.IGNORECASE)


class CaseStorage:
    """Persistence gateway for phase-2 case storage + local RAG indexing."""

    def _generate_content_hash(self, case_data: Dict) -> str:
        content_parts = [
            case_data.get("title", ""),
            case_data.get("phenomenon", ""),
            case_data.get("root_cause", ""),
            case_data.get("solution", ""),
        ]
        combined_content = " ".join(filter(None, content_parts))
        return content_cleaner.compute_content_hash(combined_content)

    def _extract_kernel_version(self, environment: str) -> str:
        match = KERNEL_VER_RE.search(environment or "")
        return match.group(1) if match else ""

    def _classify_module(self, case_data: Dict) -> str:
        module = case_data.get("module", "")
        if module:
            return module
        classification_text = " ".join([
            case_data.get("title", ""),
            case_data.get("phenomenon", ""),
            case_data.get("root_cause", ""),
            case_data.get("solution", ""),
        ])
        return module_classifier.classify_module(classification_text)

    def _build_description(self, phenomenon: str, environment: str, reference_url: str) -> str:
        description = phenomenon or ""
        if environment:
            description += f"\n\nEnvironment: {environment}"
        if reference_url:
            description += f"\n\nReference: {reference_url}"
        return description

    def _upsert_local_rag(self, case_id: str, case_data: Dict, case_obj, reference_url: str) -> None:
        """Best-effort local RAG write; must never break main DB flow."""
        try:
            vector_store = get_local_vector_store()
            vector_store.upsert_case(case_id, {
                "title": str(getattr(case_obj, "title", case_data.get("title", ""))),
                "module": str(getattr(case_obj, "module", case_data.get("module", "other"))),
                "phenomenon": case_data.get("phenomenon", ""),
                "problem_analysis": case_data.get("problem_analysis", case_data.get("analysis_process", "")),
                "related_code": case_data.get("related_code", ""),
                "root_cause": str(getattr(case_obj, "root_cause", case_data.get("root_cause", ""))),
                "solution": str(getattr(case_obj, "solution", case_data.get("solution", ""))),
                "source": str(getattr(case_obj, "source", case_data.get("source", ""))),
                "reference_url": reference_url,
            })
        except Exception as rag_error:
            print(f"Warning: RAG vector upsert failed for {case_id}: {rag_error}")

    def store(self, case_data: Dict) -> Dict:
        """Store the case data to database and return result"""
        if not case_data:
            return {
                "success": False,
                "message": "No case data provided"
            }

        try:
            if not DJANGO_AVAILABLE:
                return {
                    "success": True,
                    "message": "Mock case storage successful (Django not available)",
                    "case_id": f"CASE-{uuid.uuid4().hex[:8].upper()}"
                }

            content_hash = self._generate_content_hash(case_data)
            if content_hash:
                existing = KernelCase.objects.filter(content_hash=content_hash).first()
                if existing:
                    return {
                        "success": False,
                        "message": f"Duplicate case found (content hash match): {existing.case_id}",
                        "case_id": existing.case_id
                    }

            case_id = case_data.get("case_id", f"CASE-{uuid.uuid4().hex[:8].upper()}")
            if KernelCase.objects.filter(case_id=case_id).exists():
                return {
                    "success": False,
                    "message": f"Case with ID {case_id} already exists",
                    "case_id": case_id
                }

            env_str = case_data.get("environment", "")
            kernel_version = self._extract_kernel_version(env_str)
            affected_components = case_data.get("affected_components", "Unknown")
            phenomenon = case_data.get("phenomenon", "")
            ref_url = case_data.get("reference_url", "")
            module = self._classify_module(case_data)
            description = self._build_description(phenomenon, env_str, ref_url)

            tags = case_data.get("tags", [])
            if not tags and affected_components:
                tags = [tag.strip() for tag in affected_components.split(",") if tag.strip()]

            case = KernelCase(
                case_id=case_id,
                title=case_data.get("title", "Untitled Case")[:200],
                description=description,
                symptoms=phenomenon,
                root_cause=case_data.get("root_cause", ""),
                solution=case_data.get("solution", ""),
                kernel_version=kernel_version[:50],
                affected_components=affected_components[:200],
                severity=case_data.get("severity", "Medium"),
                created_date=timezone.now(),
                
                # New fields
                source=case_data.get("source", ""),
                source_id=case_data.get("source_id", ""),
                url=ref_url,
                problem_analysis=case_data.get("problem_analysis", ""),
                conclusion=case_data.get("conclusion", ""),
                module=module,
                tags=tags,
                votes=case_data.get("votes", 0),
                answers_count=case_data.get("answers_count", 0),
                content_hash=content_hash
            )

            case.save()
            self._upsert_local_rag(case_id, case_data, case, ref_url)

            return {
                "success": True,
                "message": "Case stored successfully",
                "case_id": case_id,
                "case": case
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error storing case: {str(e)}"
            }