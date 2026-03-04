# Core components that don't depend on Django
from .fetchers import BaseFetcher, HTTPFetcher, APIFetcher, RSSFetcher
from .parsers import BaseParser, BlogParser, ForumParser
from .validators import CaseValidator

__all__ = [
    "BaseFetcher",
    "HTTPFetcher",
    "APIFetcher",
    "RSSFetcher",
    "BaseParser",
    "BlogParser",
    "ForumParser",
    "CaseValidator"
]

# Django-dependent components (import separately when needed)
# from .storage import CaseStorage
# from .main import CaseAcquisition