import requests
import json
import re
from abc import ABC, abstractmethod


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

    def __init__(self, timeout: int = 10, headers: dict = None):
        self.timeout = timeout
        self.headers = headers or self.DEFAULT_HEADERS.copy()

    def fetch(self, url: str) -> str:
        """Fetch content from the given URL using HTTP GET"""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response.text
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
            response = requests.get(self.CSDN_SEARCH_API, params=params, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
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
        
        response = requests.get(CSDN_FALLBACK_URL, params=params, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()
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
    """Fetcher for Zhihu articles/questions - fetches content from Zhihu website"""

    ZHIHU_API_BASE = "https://www.zhihu.com/api/v4"

    def __init__(self, timeout: int = 10):
        super().__init__(timeout)
        self.headers['Accept'] = 'application/json, text/plain, */*'
        self.headers['Referer'] = 'https://www.zhihu.com/'

    def search(self, keyword: str, count: int = 5) -> list:
        """Search Zhihu for articles/questions matching keyword.
        Returns list of content URLs.
        """
        try:
            search_url = f"{self.ZHIHU_API_BASE}/search_v5"
            params = {
                "type": "content",
                "q": keyword,
                "limit": count,
                "offset": 0
            }
            response = requests.get(
                search_url, params=params, headers=self.headers, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            urls = []
            for item in data.get("data", []):
                if item.get("url"):
                    urls.append(item["url"])
                elif item.get("link"):
                    urls.append(item["link"])

            return urls[:count]
        except Exception as e:
            print(f"Error searching Zhihu: {e}")
            return []

    def fetch(self, url: str) -> str:
        """Fetch content from Zhihu.
        Returns HTML/content of the article or answer.
        """
        return super().fetch(url)

    def fetch_question_answers(self, question_id: str) -> str:
        """Fetch question and its answers from Zhihu API.
        Returns JSON string with question and answer data.
        """
        try:
            q_url = f"{self.ZHIHU_API_BASE}/questions/{question_id}"
            q_res = requests.get(q_url, headers=self.headers, timeout=self.timeout)
            q_res.raise_for_status()
            question = q_res.json()

            a_url = f"{self.ZHIHU_API_BASE}/questions/{question_id}/answers"
            params = {
                "limit": 10,
                "offset": 0,
                "sort_by": "votes"
            }
            a_res = requests.get(a_url, params=params, headers=self.headers, timeout=self.timeout)
            a_res.raise_for_status()
            answers = a_res.json()

            result = {
                "question": question,
                "answers": answers.get("data", [])
            }
            return json.dumps(result)
        except Exception as e:
            print(f"Error fetching from Zhihu: {e}")
            return None


class JuejinFetcher(HTTPFetcher):
    """Fetcher for Juejin articles - fetches articles from Juejin developer community"""

    JUEJIN_API_BASE = "https://api.juejin.cn"

    def __init__(self, timeout: int = 10):
        super().__init__(timeout)
        self.headers['Accept'] = 'application/json, text/plain, */*'

    def search(self, keyword: str, count: int = 5) -> list:
        """Search Juejin for articles matching keyword.
        Returns list of article URLs.
        """
        try:
            search_url = f"{self.JUEJIN_API_BASE}/content_api/v1/article/search"
            params = {
                "keyword": keyword,
                "type": 1,
                "limit": count
            }
            response = requests.post(
                search_url, json=params, headers=self.headers, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            urls = []
            if data.get("data"):
                for item in data["data"]:
                    if item.get("article_info") and item["article_info"].get("article_id"):
                        article_id = item["article_info"]["article_id"]
                        urls.append(f"https://juejin.cn/post/{article_id}")

            return urls[:count]
        except Exception as e:
            print(f"Error searching Juejin: {e}")
            return []

    def fetch(self, url: str) -> str:
        """Fetch article content from Juejin.
        Returns HTML content of the article.
        """
        return super().fetch(url)

    def fetch_article_detail(self, article_id: str) -> str:
        """Fetch article detail from Juejin API.
        Returns JSON string with article data.
        """
        try:
            detail_url = f"{self.JUEJIN_API_BASE}/content_api/v1/article/detail"
            params = {"article_id": article_id}
            response = requests.post(
                detail_url, json=params, headers=self.headers, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if data.get("data"):
                return json.dumps(data["data"])
            return None
        except Exception as e:
            print(f"Error fetching article detail from Juejin: {e}")
            return None