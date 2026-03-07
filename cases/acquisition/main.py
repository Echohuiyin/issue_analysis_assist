from .fetchers import HTTPFetcher, StackOverflowFetcher, CSDNFetcher, ZhihuFetcher, JuejinFetcher, BaseFetcher
from .parsers import BlogParser, ForumParser, BaseParser
from .validators import CaseValidator
from .storage import CaseStorage
from .cleaner import content_cleaner
from .classifier import module_classifier
from typing import List, Dict, Optional


# Pre-defined search keywords for kernel cases
KERNEL_KEYWORDS = [
    "kernel panic",
    "kernel oops",
    "kernel deadlock",
    "kernel null pointer dereference",
    "kernel OOM",
    "kernel page allocation failure",
]


class CaseAcquisition:
    def __init__(self):
        self.fetcher = HTTPFetcher()
        self.so_fetcher = StackOverflowFetcher()
        self.csdn_fetcher = CSDNFetcher()
        self.zhihu_fetcher = ZhihuFetcher()
        self.juejin_fetcher = JuejinFetcher()
        self.validators = CaseValidator()
        self.storage = CaseStorage()

        # Register parsers for different content types
        self.parsers = {
            "blog": BlogParser(),
            "forum": ForumParser(),
        }

    def acquire_case(self, url: str, content_type: str = "blog", source: str = "") -> Dict:
        """Acquire a single case from the given URL"""
        # Choose fetcher based on URL or content type
        if "stackexchange.com" in url or "stackoverflow.com" in url:
            content = self.so_fetcher.fetch(url)
            content_type = "forum"
            source = source or "stackoverflow"
        elif "csdn.net" in url:
            content = self.csdn_fetcher.fetch(url)
            content_type = "blog"
            source = source or "csdn"
        elif "zhihu.com" in url:
            content = self.zhihu_fetcher.fetch(url)
            content_type = "blog"
            source = source or "zhihu"
        elif "juejin.cn" in url:
            content = self.juejin_fetcher.fetch(url)
            content_type = "blog"
            source = source or "juejin"
        else:
            content = self.fetcher.fetch(url)
            source = source or "unknown"

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

        # Add reference URL to parsed data if not already set
        if not parsed_data.get("reference_url"):
            parsed_data["reference_url"] = url

        # Add source information
        parsed_data["source"] = source
        
        # Extract source_id from URL
        if source == "stackoverflow" and "/questions/" in url:
            # Extract question ID from URL like https://stackoverflow.com/questions/12345/...
            source_id = url.split("/questions/")[1].split("/")[0]
            parsed_data["source_id"] = source_id
        elif source == "csdn" and "/article/details/" in url:
            # Extract article ID from URL like https://blog.csdn.net/user/article/details/123456789
            source_id = url.split("/article/details/")[1].split("/")[0]
            parsed_data["source_id"] = source_id
        elif source == "zhihu" and "/question/" in url:
            # Extract question ID from URL like https://www.zhihu.com/question/123456789
            source_id = url.split("/question/")[1].split("/")[0]
            parsed_data["source_id"] = source_id
        elif source == "juejin" and "/post/" in url:
            # Extract article ID from URL like https://juejin.cn/post/1234567890123456789
            source_id = url.split("/post/")[1].split("/")[0]
            parsed_data["source_id"] = source_id

        # Validate parsed data
        validation_result = self.validators.validate(parsed_data)
        if not validation_result["is_valid"]:
            return {
                "success": False,
                "message": "Validation failed - content quality check failed",
                "errors": validation_result["errors"],
                "warnings": validation_result.get("warnings", []),
                "quality_score": validation_result.get("quality_score", 0)
            }
        
        # Log quality score and warnings even if validation passes
        quality_score = validation_result.get("quality_score", 0)
        warnings = validation_result.get("warnings", [])
        
        if quality_score < 60:
            print(f"Warning: Low quality score ({quality_score:.1f}) for case: {parsed_data.get('title', 'Unknown')}")
        
        if warnings:
            print(f"Quality warnings for case '{parsed_data.get('title', 'Unknown')}':")
            for warning in warnings:
                print(f"  - {warning}")

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

    def acquire_from_stackoverflow(self, keyword: str = "kernel panic", count: int = 3) -> List[Dict]:
        """Search StackOverflow for kernel-related questions and acquire them as cases"""
        print(f"Searching StackOverflow for: {keyword} (max {count} results)")
        urls = self.so_fetcher.search(keyword, count=count)

        if not urls:
            print(f"No results found for: {keyword}")
            return []

        sources = [{"url": url, "content_type": "forum", "source": "stackoverflow"} for url in urls]
        return self.acquire_cases(sources)

    def acquire_from_csdn(self, keyword: str = "内核 panic", count: int = 3) -> List[Dict]:
        """Search CSDN for kernel-related articles and acquire them as cases"""
        print(f"Searching CSDN for: {keyword} (max {count} results)")
        urls = self.csdn_fetcher.search(keyword, count=count)

        if not urls:
            print(f"No results found for: {keyword}")
            return []

        sources = [{"url": url, "content_type": "blog", "source": "csdn"} for url in urls]
        return self.acquire_cases(sources)

    def acquire_from_zhihu(self, keyword: str = "Linux内核", count: int = 3) -> List[Dict]:
        """Search Zhihu for kernel-related content and acquire them as cases"""
        print(f"Searching Zhihu for: {keyword} (max {count} results)")
        urls = self.zhihu_fetcher.search(keyword, count=count)

        if not urls:
            print(f"No results found for: {keyword}")
            return []

        sources = [{"url": url, "content_type": "blog", "source": "zhihu"} for url in urls]
        return self.acquire_cases(sources)

    def acquire_from_juejin(self, keyword: str = "内核", count: int = 3) -> List[Dict]:
        """Search Juejin for kernel-related articles and acquire them as cases"""
        print(f"Searching Juejin for: {keyword} (max {count} results)")
        urls = self.juejin_fetcher.search(keyword, count=count)

        if not urls:
            print(f"No results found for: {keyword}")
            return []

        sources = [{"url": url, "content_type": "blog", "source": "juejin"} for url in urls]
        return self.acquire_cases(sources)

    def run(self, keywords: List[str] = None, max_per_keyword: int = 2, sources: List[str] = None) -> List[Dict]:
        """Run acquisition from all specified sources.
        Searches StackOverflow, CSDN, Zhihu, and Juejin for each keyword and collects cases.
        
        Args:
            keywords: List of keywords to search for
            max_per_keyword: Maximum number of cases to acquire per keyword per source
            sources: List of sources to use ("stackoverflow", "csdn", "zhihu", "juejin"), defaults to all
        """
        if keywords is None:
            keywords = KERNEL_KEYWORDS
        
        if sources is None:
            sources = ["stackoverflow", "csdn", "zhihu", "juejin"]

        all_results = []
        for keyword in keywords:
            if "stackoverflow" in sources:
                so_results = self.acquire_from_stackoverflow(keyword, count=max_per_keyword)
                all_results.extend(so_results)
            
            if "csdn" in sources:
                # Translate English keywords to Chinese for better CSDN results
                csdn_keyword = keyword
                if keyword == "kernel panic":
                    csdn_keyword = "内核 panic"
                elif keyword == "kernel oops":
                    csdn_keyword = "内核 oops"
                elif keyword == "kernel deadlock":
                    csdn_keyword = "内核死锁"
                elif keyword == "kernel null pointer dereference":
                    csdn_keyword = "内核空指针"
                elif keyword == "kernel OOM":
                    csdn_keyword = "内核 OOM"
                elif keyword == "kernel page allocation failure":
                    csdn_keyword = "内核页分配失败"
                
                csdn_results = self.acquire_from_csdn(csdn_keyword, count=max_per_keyword)
                all_results.extend(csdn_results)

            if "zhihu" in sources:
                # Translate English keywords to Chinese for better Zhihu results
                zhihu_keyword = keyword
                if keyword == "kernel panic":
                    zhihu_keyword = "内核崩溃"
                elif keyword == "kernel oops":
                    zhihu_keyword = "内核错误"
                elif keyword == "kernel deadlock":
                    zhihu_keyword = "内核死锁"
                elif keyword == "kernel null pointer dereference":
                    zhihu_keyword = "内核空指针"
                elif keyword == "kernel OOM":
                    zhihu_keyword = "内存溢出"
                elif keyword == "kernel page allocation failure":
                    zhihu_keyword = "内核内存分配"
                
                zhihu_results = self.acquire_from_zhihu(zhihu_keyword, count=max_per_keyword)
                all_results.extend(zhihu_results)

            if "juejin" in sources:
                # Use Chinese keywords for Juejin
                juejin_keyword = keyword
                if keyword == "kernel panic":
                    juejin_keyword = "内核 panic"
                elif keyword == "kernel oops":
                    juejin_keyword = "内核 oops"
                elif keyword == "kernel deadlock":
                    juejin_keyword = "内核死锁"
                elif keyword == "kernel null pointer dereference":
                    juejin_keyword = "内核空指针"
                elif keyword == "kernel OOM":
                    juejin_keyword = "内核 OOM"
                elif keyword == "kernel page allocation failure":
                    juejin_keyword = "内核页分配"
                
                juejin_results = self.acquire_from_juejin(juejin_keyword, count=max_per_keyword)
                all_results.extend(juejin_results)

        success_count = sum(1 for r in all_results if r.get("success"))
        print(f"\nAcquisition complete: {success_count}/{len(all_results)} cases stored successfully")
        return all_results