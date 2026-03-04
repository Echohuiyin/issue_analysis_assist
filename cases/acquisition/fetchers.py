import requests
from abc import ABC, abstractmethod

class BaseFetcher(ABC):
    @abstractmethod
    def fetch(self, url: str) -> str:
        """Fetch content from the given URL"""
        pass

class HTTPFetcher(BaseFetcher):
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    def fetch(self, url: str) -> str:
        """Fetch content from the given URL using HTTP GET"""
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

class APIFetcher(BaseFetcher):
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    def fetch(self, url: str, params: dict = None, headers: dict = None) -> dict:
        """Fetch content from the given API URL"""
        try:
            response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching API {url}: {e}")
            return None

class RSSFetcher(BaseFetcher):
    def fetch(self, url: str) -> str:
        """Fetch RSS feed content from the given URL"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching RSS {url}: {e}")
            return None
