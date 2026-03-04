from typing import Dict, List, Optional

class CaseValidator:
    def __init__(self):
        self.required_fields = [
            "title",
            "phenomenon",
            "environment",
            "root_cause",
            "troubleshooting_steps",
            "solution"
        ]
    
    def validate(self, case_data: Dict) -> Dict:
        """Validate case data and return validation result"""
        is_valid = True
        errors = []
        
        # Check if all required fields are present
        for field in self.required_fields:
            if field not in case_data or not case_data[field]:
                is_valid = False
                errors.append(f"Required field '{field}' is missing or empty")
        
        # Validate specific field constraints
        if "troubleshooting_steps" in case_data:
            if not isinstance(case_data["troubleshooting_steps"], list):
                is_valid = False
                errors.append("'troubleshooting_steps' must be a list")
        
        if "root_cause" in case_data and len(case_data["root_cause"]) < 10:
            is_valid = False
            errors.append("'root_cause' must be at least 10 characters long")
        
        if "solution" in case_data and len(case_data["solution"]) < 10:
            is_valid = False
            errors.append("'solution' must be at least 10 characters long")
        
        return {
            "is_valid": is_valid,
            "errors": errors
        }