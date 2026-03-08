from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple

from .fetchers import HTTPFetcher, StackOverflowFetcher, CSDNFetcher, ZhihuFetcher
from .parsers import BlogParser, ForumParser, ZhihuParser
from .llm_parser import LLMParser
from .validators import CaseValidator
from .storage import CaseStorage
from .cleaner import content_cleaner
from .classifier import module_classifier


# Default search keywords used by batch acquisition.
KERNEL_KEYWORDS = [
    "kernel panic",
    "kernel oops",
    "kernel deadlock",
    "kernel null pointer dereference",
    "kernel OOM",
    "kernel page allocation failure",
]
# Global quality gate: cases below this score are discarded.
QUALITY_THRESHOLD = 80.0


def _to_cn_keyword(keyword: str) -> str:
    mapping = {
        "kernel panic": "内核 panic",
        "kernel oops": "内核 oops",
        "kernel deadlock": "内核死锁",
        "kernel null pointer dereference": "内核空指针",
        "kernel OOM": "内核 OOM",
        "kernel page allocation failure": "内核页分配失败",
    }
    return mapping.get(keyword, keyword)


class CaseAcquisition:
    """Acquisition orchestrator for phase-1/2 pipeline.

    The orchestrator keeps only flow-control logic:
    fetch -> parse -> clean -> classify -> validate -> store
    """

    def __init__(self):
        # Fetchers
        self.fetcher = HTTPFetcher()
        self.so_fetcher = StackOverflowFetcher()
        self.csdn_fetcher = CSDNFetcher()
        self.zhihu_fetcher = ZhihuFetcher()

        # Core collaborators
        self.validators = CaseValidator()
        self.storage = CaseStorage()
        self.llm_parser = LLMParser(llm_type="auto")

        # Source-specific parser fallback map.
        self.parsers = {
            "blog": BlogParser(),
            "forum": ForumParser(),
            "zhihu": ZhihuParser(),
        }

    def _resolve_source(self, url: str, content_type: str, source: str) -> Tuple[str, str, str]:
        """Resolve source/fetcher/content_type based on URL pattern."""
        if "stackexchange.com" in url or "stackoverflow.com" in url:
            content = self.so_fetcher.fetch(url)
            return content, "forum", source or "stackoverflow"
        if "csdn.net" in url:
            content = self.csdn_fetcher.fetch(url)
            return content, "blog", source or "csdn"
        if "zhihu.com" in url:
            content = self.zhihu_fetcher.fetch(url)
            return content, "zhihu", source or "zhihu"
        content = self.fetcher.fetch(url)
        return content, content_type, source or "unknown"

    def _parse_content(self, content: str, content_type: str):
        """Parse content via local LLM first, then source fallback parser."""
        parsed_data = None
        if content_type in ("blog", "zhihu"):
            parsed_data = self.llm_parser.parse(content, use_llm=True)
        if not parsed_data:
            parser = self.parsers.get(content_type, BlogParser())
            parsed_data = parser.parse(content)
        return parsed_data

    def _extract_source_id(self, url: str, source: str) -> str:
        """Extract platform-native source id from URL."""
        if source == "stackoverflow" and "/questions/" in url:
            return url.split("/questions/")[1].split("/")[0]
        if source == "csdn" and "/article/details/" in url:
            return url.split("/article/details/")[1].split("/")[0]
        if source == "zhihu":
            if "/question/" in url:
                return url.split("/question/")[1].split("/")[0]
            if "/p/" in url:
                return url.split("/p/")[1].split("/")[0]
        return ""

    def _classify_case_module(self, parsed_data: Dict, content: str) -> str:
        cleaned_text = content_cleaner.clean_html(content)
        classify_text = "\n".join([
            parsed_data.get("title", ""),
            parsed_data.get("phenomenon", ""),
            parsed_data.get("root_cause", ""),
            parsed_data.get("solution", ""),
            cleaned_text[:1000],
        ])
        return module_classifier.classify_module(classify_text)

    def acquire_case(self, url: str, content_type: str = "blog", source: str = "") -> Dict:
        """Acquire one case from URL and pass quality-gated storage."""
        content, content_type, source = self._resolve_source(url, content_type, source)
        if not content:
            return {
                "success": False,
                "message": f"Failed to fetch content from {url}"
            }

        parsed_data = self._parse_content(content, content_type)
        if not parsed_data:
            return {
                "success": False,
                "message": f"Failed to parse content from {url}"
            }

        # Normalize source metadata.
        if not parsed_data.get("reference_url"):
            parsed_data["reference_url"] = url
        parsed_data["source"] = source
        parsed_data["module"] = self._classify_case_module(parsed_data, content)
        source_id = self._extract_source_id(url, source)
        if source_id:
            parsed_data["source_id"] = source_id

        # Quality validation + gate.
        validation_result = self.validators.validate(parsed_data)
        if not validation_result["is_valid"]:
            return {
                "success": False,
                "message": "Validation failed - content quality check failed",
                "errors": validation_result["errors"],
                "warnings": validation_result.get("warnings", []),
                "quality_score": validation_result.get("quality_score", 0)
            }

        if float(validation_result.get("quality_score", 0) or 0) < QUALITY_THRESHOLD:
            return {
                "success": False,
                "message": f"Case discarded due to low quality score (<{QUALITY_THRESHOLD})",
                "warnings": validation_result.get("warnings", []),
                "quality_score": validation_result.get("quality_score", 0),
                "low_quality_flags": validation_result.get("low_quality_flags", []),
            }

        # Keep warnings visible for observability.
        quality_score = validation_result.get("quality_score", 0)
        warnings = validation_result.get("warnings", [])
        if quality_score < 60:
            print(f"Warning: Low quality score ({quality_score:.1f}) for case: {parsed_data.get('title', 'Unknown')}")
        if warnings:
            print(f"Quality warnings for case '{parsed_data.get('title', 'Unknown')}':")
            for warning in warnings:
                print(f"  - {warning}")

        return self.storage.store(parsed_data)

    def acquire_cases(
        self,
        sources: List[Dict],
        max_workers: int = 4,
        batch_size: int = 10,
        use_concurrency: bool = True,
    ) -> List[Dict]:
        """Acquire multiple cases with bounded concurrency and batching."""
        if not sources:
            return []

        def _acquire_one(index: int, source_item: Dict):
            url = source_item.get("url")
            content_type = source_item.get("content_type", "blog")
            source_name = source_item.get("source", "")

            if not url:
                return index, {
                    "success": False,
                    "message": "No URL provided for source",
                    "source_url": "",
                }

            result = self.acquire_case(url, content_type=content_type, source=source_name)
            result["source_url"] = url
            return index, result

        indexed_results = []
        if not use_concurrency or max_workers <= 1:
            for i, source_item in enumerate(sources):
                indexed_results.append(_acquire_one(i, source_item))
        else:
            workers = max(1, min(max_workers, 16))
            step = max(1, batch_size)
            for start in range(0, len(sources), step):
                batch = sources[start:start + step]
                with ThreadPoolExecutor(max_workers=workers) as pool:
                    futures = [pool.submit(_acquire_one, start + i, src) for i, src in enumerate(batch)]
                    for future in as_completed(futures):
                        indexed_results.append(future.result())

        indexed_results.sort(key=lambda item: item[0])
        return [item[1] for item in indexed_results]

    def acquire_from_stackoverflow(self, keyword: str = "kernel panic", count: int = 3) -> List[Dict]:
        """Search StackOverflow and ingest question cases."""
        print(f"Searching StackOverflow for: {keyword} (max {count} results)")
        urls = self.so_fetcher.search(keyword, count=count)

        if not urls:
            print(f"No results found for: {keyword}")
            return []

        sources = [{"url": url, "content_type": "forum", "source": "stackoverflow"} for url in urls]
        return self.acquire_cases(sources)

    def acquire_from_csdn(self, keyword: str = "内核 panic", count: int = 3) -> List[Dict]:
        """Search CSDN and ingest article cases."""
        print(f"Searching CSDN for: {keyword} (max {count} results)")
        urls = self.csdn_fetcher.search(keyword, count=count)

        if not urls:
            print(f"No results found for: {keyword}")
            return []

        sources = [{"url": url, "content_type": "blog", "source": "csdn"} for url in urls]
        return self.acquire_cases(sources)

    def acquire_from_zhihu(self, keyword: str = "内核 panic", count: int = 3) -> List[Dict]:
        """Search Zhihu and ingest content cases."""
        print(f"Searching Zhihu for: {keyword} (max {count} results)")
        urls = self.zhihu_fetcher.search(keyword, count=count)

        if not urls:
            print(f"No results found for: {keyword}")
            return []

        sources = [{"url": url, "content_type": "zhihu", "source": "zhihu"} for url in urls]
        return self.acquire_cases(sources)

    def run(self, keywords: List[str] = None, max_per_keyword: int = 2, sources: List[str] = None) -> List[Dict]:
        """Run acquisition from all specified sources.
        Searches StackOverflow/CSDN/Zhihu for each keyword and collects cases.
        
        Args:
            keywords: List of keywords to search for
            max_per_keyword: Maximum number of cases to acquire per keyword per source
            sources: List of sources to use ("stackoverflow", "csdn", "zhihu"), defaults to all
        """
        if keywords is None:
            keywords = KERNEL_KEYWORDS
        
        if sources is None:
            sources = ["stackoverflow", "csdn", "zhihu"]

        all_results = []
        for keyword in keywords:
            if "stackoverflow" in sources:
                so_results = self.acquire_from_stackoverflow(keyword, count=max_per_keyword)
                all_results.extend(so_results)
            
            if "csdn" in sources:
                csdn_keyword = _to_cn_keyword(keyword)
                csdn_results = self.acquire_from_csdn(csdn_keyword, count=max_per_keyword)
                all_results.extend(csdn_results)

            if "zhihu" in sources:
                zhihu_keyword = _to_cn_keyword(keyword)
                zhihu_results = self.acquire_from_zhihu(zhihu_keyword, count=max_per_keyword)
                all_results.extend(zhihu_results)

        success_count = sum(1 for r in all_results if r.get("success"))
        print(f"\nAcquisition complete: {success_count}/{len(all_results)} cases stored successfully")
        return all_results