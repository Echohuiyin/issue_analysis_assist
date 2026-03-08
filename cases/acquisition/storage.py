import re
from typing import Dict, Optional
import uuid

# Import the module classifier
from .classifier import module_classifier
from .cleaner import content_cleaner
from cases.rag import get_local_vector_store

# Add Django imports only if Django is available
try:
    from django.utils import timezone
    from django.db.models import Q
    from cases.models import KernelCase
    DJANGO_AVAILABLE = True
except ImportError:
    timezone = None
    Q = None
    KernelCase = None
    DJANGO_AVAILABLE = False

# Regex for kernel version extraction from environment string
KERNEL_VER_RE = re.compile(r'(?:Linux|kernel)\s*(\d+\.\d+[\.\d]*(?:-[\w.]+)?)', re.IGNORECASE)


class CaseStorage:
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

            # Generate content hash for deduplication
            # Combine title, description, root_cause, solution for unique content hash
            content_parts = [
                case_data.get("title", ""),
                case_data.get("phenomenon", ""),
                case_data.get("root_cause", ""),
                case_data.get("solution", "")
            ]
            combined_content = " ".join(filter(None, content_parts))
            content_hash = content_cleaner.compute_content_hash(combined_content)
            
            # Deduplication: check by content_hash
            if content_hash:
                existing = KernelCase.objects.filter(content_hash=content_hash).first()
                if existing:
                    return {
                        "success": False,
                        "message": f"Duplicate case found (content hash match): {existing.case_id}",
                        "case_id": existing.case_id
                    }

            # Generate unique case ID if not provided
            case_id = case_data.get("case_id", f"CASE-{uuid.uuid4().hex[:8].upper()}")

            # Check if case_id already exists
            if KernelCase.objects.filter(case_id=case_id).exists():
                return {
                    "success": False,
                    "message": f"Case with ID {case_id} already exists",
                    "case_id": case_id
                }

            # Extract kernel version from environment
            kernel_version = ""
            env_str = case_data.get("environment", "")
            match = KERNEL_VER_RE.search(env_str)
            if match:
                kernel_version = match.group(1)

            affected_components = case_data.get("affected_components", "Unknown")

            # Build description with reference URL
            phenomenon = case_data.get("phenomenon", "")
            description = phenomenon
            if env_str:
                description += f"\n\nEnvironment: {env_str}"
            ref_url = case_data.get("reference_url", "")
            if ref_url:
                description += f"\n\nReference: {ref_url}"

            # Classify kernel module if not provided
            module = case_data.get("module", "")
            if not module:
                # Combine text from multiple fields for better classification
                classification_text = " ".join([
                    case_data.get("title", ""),
                    case_data.get("phenomenon", ""),
                    case_data.get("root_cause", ""),
                    case_data.get("solution", "")
                ])
                module = module_classifier.classify_module(classification_text)

            # Extract tags from affected_components if not provided
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

            # Update local RAG vector store after DB commit.
            # This path is best-effort and must not break DB write success.
            try:
                vector_store = get_local_vector_store()
                vector_store.upsert_case(case_id, {
                    "title": str(getattr(case, "title", case_data.get("title", ""))),
                    "module": str(getattr(case, "module", case_data.get("module", "other"))),
                    "phenomenon": case_data.get("phenomenon", ""),
                    "problem_analysis": case_data.get("problem_analysis", case_data.get("analysis_process", "")),
                    "related_code": case_data.get("related_code", ""),
                    "root_cause": str(getattr(case, "root_cause", case_data.get("root_cause", ""))),
                    "solution": str(getattr(case, "solution", case_data.get("solution", ""))),
                    "source": str(getattr(case, "source", case_data.get("source", ""))),
                    "reference_url": ref_url,
                })
            except Exception as rag_error:
                print(f"Warning: RAG vector upsert failed for {case_id}: {rag_error}")

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