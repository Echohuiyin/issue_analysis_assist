# Core components that don't depend on Django
from .fetchers import BaseFetcher, HTTPFetcher, APIFetcher, RSSFetcher, StackOverflowFetcher, CSDNFetcher, ZhihuFetcher, JuejinFetcher
from .parsers import BaseParser, BlogParser, ForumParser
from .validators import CaseValidator, case_validator
from .cleaner import ContentCleaner, content_cleaner
from .classifier import ModuleClassifier, module_classifier
from .vector_service import VectorService, get_vector_service
from .llm_integration import (
    BaseLLM, 
    OllamaLLM, 
    VLLMLocalLLM,
    QwenLocalLLM, 
    ChatGLMLocalLLM,
    OpenAILLM, 
    DeepSeekLLM, 
    MockLLM, 
    LLMFactory, 
    get_llm
)
from .llm_parser import LLMParser, llm_parser

__all__ = [
    "BaseFetcher",
    "HTTPFetcher",
    "APIFetcher",
    "RSSFetcher",
    "StackOverflowFetcher",
    "CSDNFetcher",
    "ZhihuFetcher",
    "JuejinFetcher",
    "BaseParser",
    "BlogParser",
    "ForumParser",
    "CaseValidator",
    "case_validator",
    "ContentCleaner",
    "content_cleaner",
    "ModuleClassifier",
    "module_classifier",
    "VectorService",
    "get_vector_service",
    "BaseLLM",
    "OllamaLLM",
    "VLLMLocalLLM",
    "QwenLocalLLM",
    "ChatGLMLocalLLM",
    "OpenAILLM",
    "DeepSeekLLM",
    "MockLLM",
    "LLMFactory",
    "get_llm",
    "LLMParser",
    "llm_parser"
]

# Django-dependent components (import separately when needed)
# from .storage import CaseStorage
# from .main import CaseAcquisition