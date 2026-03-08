import requests
import json
import re
import time
import random
from abc import ABC, abstractmethod
from urllib.parse import quote_plus


class BaseFetcher(ABC):
    @abstractmethod
    def fetch(self, url: str) -> str:
        """Fetch content from the given URL"""
        pass


class HTTPFetcher(BaseFetcher):
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                       '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    def __init__(
        self,
        timeout: int = 10,
        headers: dict = None,
        min_interval: float = 0.4,
        max_retries: int = 2,
        backoff_base: float = 0.8,
        cache_ttl: int = 300
    ):
        self.timeout = timeout
        self.headers = headers or self.DEFAULT_HEADERS.copy()
        self.min_interval = max(0.0, min_interval)
        self.max_retries = max(0, max_retries)
        self.backoff_base = max(0.1, backoff_base)
        self.cache_ttl = max(0, cache_ttl)
        self._last_request_at = 0.0
        self._cache = {}

    def _sleep_for_rate_limit(self):
        elapsed = time.monotonic() - self._last_request_at
        wait_time = self.min_interval - elapsed
        if wait_time > 0:
            time.sleep(wait_time)

    def _with_retry_get(self, url: str, **kwargs):
        for attempt in range(self.max_retries + 1):
            self._sleep_for_rate_limit()
            self._last_request_at = time.monotonic()
            try:
                response = requests.get(url, timeout=self.timeout, **kwargs)
                if response.status_code == 429 and attempt < self.max_retries:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        time.sleep(float(retry_after))
                    else:
                        delay = self.backoff_base * (2 ** attempt) + random.uniform(0, 0.2)
                        time.sleep(delay)
                    continue
                response.raise_for_status()
                return response
            except Exception:
                if attempt >= self.max_retries:
                    raise
                delay = self.backoff_base * (2 ** attempt) + random.uniform(0, 0.2)
                time.sleep(delay)
        return None

    def fetch(self, url: str) -> str:
        """Fetch content from the given URL using HTTP GET"""
        cached = self._cache.get(url)
        if cached and time.time() - cached["ts"] <= self.cache_ttl:
            return cached["value"]
        try:
            response = self._with_retry_get(url, headers=self.headers)
            response.encoding = response.apparent_encoding
            text = response.text
            if self.cache_ttl > 0:
                self._cache[url] = {"ts": time.time(), "value": text}
            return text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None


class APIFetcher(BaseFetcher):
    def __init__(self, timeout: int = 10, default_params: dict = None, default_headers: dict = None):
        self.timeout = timeout
        self.default_params = default_params or {}
        self.default_headers = default_headers or {}

    def fetch(self, url: str) -> str:
        """Fetch JSON content from the given API URL, returns raw JSON string"""
        try:
            response = requests.get(
                url, params=self.default_params, headers=self.default_headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching API {url}: {e}")
            return None

    def fetch_json(self, url: str, params: dict = None, headers: dict = None) -> dict:
        """Fetch and parse JSON from the given API URL"""
        try:
            merged_params = {**self.default_params, **(params or {})}
            merged_headers = {**self.default_headers, **(headers or {})}
            response = requests.get(
                url, params=merged_params, headers=merged_headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching API {url}: {e}")
            return None


class RSSFetcher(BaseFetcher):
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch(self, url: str) -> str:
        """Fetch RSS feed content from the given URL"""
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching RSS {url}: {e}")
            return None


class StackOverflowFetcher(BaseFetcher):
    """Fetcher for StackOverflow API - fetches question + accepted answer"""

    SO_API_BASE = "https://api.stackexchange.com/2.3"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch(self, url: str) -> str:
        """Fetch question and accepted answer from StackOverflow API.
        url should be a SO API questions endpoint with filter=withbody.
        Returns JSON string with question and answer data.
        """
        try:
            q_res = requests.get(url, timeout=self.timeout)
            q_res.raise_for_status()
            q_data = q_res.json()

            if not q_data.get("items"):
                return None

            question = q_data["items"][0]

            # Fetch accepted answer if exists
            answer_body = ""
            if question.get("accepted_answer_id"):
                a_url = (f"{self.SO_API_BASE}/answers/{question['accepted_answer_id']}"
                         f"?site=stackoverflow&filter=withbody")
                a_res = requests.get(a_url, timeout=self.timeout)
                if a_res.status_code == 200:
                    a_data = a_res.json()
                    if a_data.get("items"):
                        answer_body = a_data["items"][0].get("body", "")

            result = {
                "question": question,
                "answer": answer_body
            }
            return json.dumps(result)
        except Exception as e:
            print(f"Error fetching from StackOverflow: {e}")
            return None

    def search(self, keyword: str, count: int = 5) -> list:
        """Search StackOverflow for questions matching keyword.
        Returns list of API URLs for matching questions.
        """
        try:
            search_url = (f"{self.SO_API_BASE}/search/advanced"
                          f"?order=desc&sort=votes&q={keyword}"
                          f"&site=stackoverflow&tagged=linux-kernel"
                          f"&pagesize={count}&filter=withbody")
            response = requests.get(search_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            urls = []
            for item in data.get("items", []):
                qid = item["question_id"]
                q_url = (f"{self.SO_API_BASE}/questions/{qid}"
                         f"?site=stackoverflow&filter=withbody")
                urls.append(q_url)
            return urls
        except Exception as e:
            print(f"Error searching StackOverflow: {e}")
            return []


class CSDNFetcher(HTTPFetcher):
    """Fetcher for CSDN articles - fetches articles from CSDN website"""

    CSDN_SEARCH_API = "https://so.csdn.net/api/v2/search"
    CSDN_ARTICLE_URL = "https://blog.csdn.net"

    def __init__(self, timeout: int = 10):
        super().__init__(timeout)

    def search(self, keyword: str, count: int = 5) -> list:
        """Search CSDN for articles matching keyword.
        Returns list of article URLs.
        """
        try:
            params = {
                "q": keyword,
                "t": "blog",
                "p": 1,
                "s": 0,
                "tm": 0,
                "lv": -1,
                "ft": 0,
                "l": "C",
                "u": "",
                "platform": "pc",
                "channel": "search"
            }

            # 使用CSDN的API接口而不是HTML页面
            response = self._with_retry_get(self.CSDN_SEARCH_API, params=params, headers=self.headers)
            data = response.json()

            article_urls = []
            # 提取文章URL
            if data.get("result_vos"):
                for item in data["result_vos"]:
                    if item.get("url") and "article/details" in item["url"]:
                        article_urls.append(item["url"])

            # Limit to requested count and remove duplicates
            unique_urls = list(dict.fromkeys(article_urls))
            return unique_urls[:count]
        except Exception as e:
            print(f"Error searching CSDN: {e}")
            # 如果API失败，尝试使用另一种方式
            try:
                return self._search_fallback(keyword, count)
            except Exception as fallback_e:
                print(f"Fallback search also failed: {fallback_e}")
                return []
    
    def _search_fallback(self, keyword: str, count: int = 5) -> list:
        """Fallback search method if API fails"""
        CSDN_FALLBACK_URL = "https://so.csdn.net/so/search"
        params = {
            "q": keyword,
            "t": "blog",
            "p": 1,
        }
        
        response = self._with_retry_get(CSDN_FALLBACK_URL, params=params, headers=self.headers)
        html = response.text
        
        # 尝试从HTML中提取URL，作为备选方案
        # 查找所有可能的URL
        all_urls = re.findall(r'https://blog\.csdn\.net/[^/]+/article/details/\d+', html)
        
        # Limit to requested count and remove duplicates
        unique_urls = list(dict.fromkeys(all_urls))
        return unique_urls[:count]

    def fetch(self, url: str) -> str:
        """Fetch article content from CSDN.
        Returns HTML content of the article.
        """
        return super().fetch(url)


class ZhihuFetcher(HTTPFetcher):
    """Fetcher for Zhihu content with API + HTML fallback."""

    ZHIHU_SEARCH_API = "https://www.zhihu.com/api/v4/search_v3"
    ZHIHU_SEARCH_FALLBACK = "https://www.zhihu.com/search?type=content&q={query}"

    def __init__(self, timeout: int = 10):
        headers = HTTPFetcher.DEFAULT_HEADERS.copy()
        headers.update({
            "Referer": "https://www.zhihu.com/",
            "Accept": "application/json,text/plain,*/*",
        })
        super().__init__(timeout=timeout, headers=headers, min_interval=1.0, max_retries=3, backoff_base=1.0, cache_ttl=300)

    def search(self, keyword: str, count: int = 5) -> list:
        try:
            params = {
                "gk_version": "gz-gaokao",
                "t": "general",
                "q": keyword,
                "correction": 1,
                "offset": 0,
                "limit": min(max(count * 2, 10), 20),
            }
            response = self._with_retry_get(self.ZHIHU_SEARCH_API, params=params, headers=self.headers)
            data = response.json()
            urls = []
            for item in data.get("data", []):
                obj = item.get("object", {})
                candidate = obj.get("url") or obj.get("url_token")
                if not candidate:
                    continue
                if candidate.startswith("/"):
                    candidate = f"https://www.zhihu.com{candidate}"
                if "zhihu.com/question/" in candidate or "zhuanlan.zhihu.com/p/" in candidate:
                    urls.append(candidate)
            return list(dict.fromkeys(urls))[:count]
        except Exception as e:
            print(f"Error searching Zhihu API: {e}")
            try:
                return self._search_fallback(keyword, count)
            except Exception as fallback_e:
                print(f"Zhihu fallback search also failed: {fallback_e}")
                return []

    def _search_fallback(self, keyword: str, count: int = 5) -> list:
        url = self.ZHIHU_SEARCH_FALLBACK.format(query=quote_plus(keyword))
        html = self.fetch(url)
        if not html:
            return []

        question_urls = re.findall(r'https://www\.zhihu\.com/question/\d+(?:/\d+)?', html)
        article_urls = re.findall(r'https://zhuanlan\.zhihu\.com/p/\d+', html)
        combined = list(dict.fromkeys(question_urls + article_urls))
        return combined[:count]