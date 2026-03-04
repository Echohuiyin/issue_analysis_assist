from typing import Dict, Optional
import uuid

# Add Django imports only if Django is available
try:
    from django.utils import timezone
    from cases.models import KernelCase
    DJANGO_AVAILABLE = True
except ImportError:
    # Django not available, create mock objects for testing
    timezone = None
    KernelCase = None
    DJANGO_AVAILABLE = False

class CaseStorage:
    def store(self, case_data: Dict) -> Dict:
        """Store the case data to database and return result"""
        if not case_data:
            return {
                "success": False,
                "message": "No case data provided"
            }
        
        try:
            # Check if Django is available
            if not DJANGO_AVAILABLE:
                # Return mock success for testing purposes when Django is not available
                return {
                    "success": True,
                    "message": "Mock case storage successful (Django not available)",
                    "case_id": f"CASE-{uuid.uuid4().hex[:8].upper()}"
                }
            
            # Generate unique case ID if not provided
            case_id = case_data.get("case_id", f"CASE-{uuid.uuid4().hex[:8].upper()}")
            
            # Check if case already exists
            existing_case = KernelCase.objects.filter(case_id=case_id).first()
            if existing_case:
                return {
                    "success": False,
                    "message": f"Case with ID {case_id} already exists",
                    "case_id": case_id
                }
            
            # Map parsed fields to model fields
            # Extract kernel version from environment if available
            kernel_version = ""
            if "environment" in case_data:
                env_str = case_data["environment"]
                # Simple extraction - in real implementation, use regex
                if "Linux " in env_str:
                    kernel_part = env_str.split("Linux ")[1].split(",")[0]
                    kernel_version = kernel_part.strip()
            
            # Extract affected components (simplified)
            affected_components = case_data.get("affected_components", "Unknown")
            
            # Create new case
            case = KernelCase(
                case_id=case_id,
                title=case_data.get("title", "Untitled Case"),
                description=case_data.get("phenomenon", "") + "\n\nEnvironment: " + case_data.get("environment", ""),
                symptoms=case_data.get("phenomenon", ""),
                root_cause=case_data.get("root_cause", ""),
                solution=case_data.get("solution", ""),
                kernel_version=kernel_version,
                affected_components=affected_components,
                severity=case_data.get("severity", "Medium"),  # Default to Medium if not specified
                created_date=timezone.now()
            )
            
            case.save()
            
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