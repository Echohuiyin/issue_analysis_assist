from .fetchers import HTTPFetcher, BaseFetcher
from .parsers import BlogParser, ForumParser, BaseParser
from .validators import CaseValidator
from .storage import CaseStorage
from typing import List, Dict, Optional

class CaseAcquisition:
    def __init__(self):
        self.fetcher = HTTPFetcher()
        self.validators = CaseValidator()
        self.storage = CaseStorage()
        
        # Register parsers for different content types
        self.parsers = {
            "blog": BlogParser(),
            "forum": ForumParser()
        }
    
    def acquire_case(self, url: str, content_type: str = "blog") -> Dict:
        """Acquire a single case from the given URL"""
        # Fetch content
        content = self.fetcher.fetch(url)
        if not content:
            return {
                "success": False,
                "message": f"Failed to fetch content from {url}"
            }
        
        # Parse content
        parser = self.parsers.get(content_type, BlogParser())
        parsed_data = parser.parse(content)
        if not parsed_data:
            return {
                "success": False,
                "message": f"Failed to parse content from {url}"
            }
        
        # Add reference URL to parsed data
        parsed_data["reference_url"] = url
        
        # Validate parsed data
        validation_result = self.validators.validate(parsed_data)
        if not validation_result["is_valid"]:
            return {
                "success": False,
                "message": "Validation failed",
                "errors": validation_result["errors"]
            }
        
        # Store case
        storage_result = self.storage.store(parsed_data)
        return storage_result
    
    def acquire_cases(self, sources: List[Dict]) -> List[Dict]:
        """Acquire multiple cases from different sources"""
        results = []
        
        for source in sources:
            url = source.get("url")
            content_type = source.get("content_type", "blog")
            
            if not url:
                results.append({
                    "success": False,
                    "message": "No URL provided for source"
                })
                continue
            
            result = self.acquire_case(url, content_type)
            result["source_url"] = url
            results.append(result)
        
        return results