"""
RAG (Retrieval-Augmented Generation) 模块
基于检索增强生成的智能问答系统
"""
from .vector_store import LocalVectorStore, get_local_vector_store
from .vector_retriever import VectorRetriever, vector_retriever
from .case_recommender import CaseRecommender, case_recommender
from .qa_engine import QAEngine, get_qa_engine

__all__ = [
    'LocalVectorStore',
    'get_local_vector_store',
    'VectorRetriever',
    'vector_retriever',
    'CaseRecommender',
    'case_recommender',
    'QAEngine',
    'get_qa_engine',
]