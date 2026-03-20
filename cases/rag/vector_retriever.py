"""
RAG向量检索器
基于向量嵌入实现相似案例检索
"""
import numpy as np
from typing import List, Dict, Optional
from django.db.models import Q


class VectorRetriever:
    """向量检索器"""
    
    def __init__(self, vector_service=None):
        """
        初始化向量检索器
        
        Args:
            vector_service: 向量服务（用于生成查询向量）
        """
        self.vector_service = vector_service
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            相似度分数（0-1）
        """
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def search_similar(
        self, 
        query_embedding: List[float], 
        cases: List[Dict], 
        top_k: int = 5, 
        threshold: float = 0.5
    ) -> List[Dict]:
        """
        检索相似案例
        
        Args:
            query_embedding: 查询向量
            cases: 案例列表（每个案例包含embedding字段）
            top_k: 返回前K个结果
            threshold: 相似度阈值
            
        Returns:
            相似案例列表（包含相似度分数）
        """
        results = []
        
        for case in cases:
            if not case.get('embedding') or len(case['embedding']) == 0:
                continue
            
            similarity = self._cosine_similarity(query_embedding, case['embedding'])
            
            if similarity >= threshold:
                result = {
                    'case_id': case.get('case_id'),
                    'title': case.get('title'),
                    'phenomenon': case.get('phenomenon'),
                    'root_cause': case.get('root_cause'),
                    'solution': case.get('solution'),
                    'module': case.get('module'),
                    'source': case.get('source'),
                    'quality_score': case.get('quality_score'),
                    'similarity': similarity
                }
                results.append(result)
        
        # 按相似度排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:top_k]
    
    def search_by_module(
        self, 
        query_embedding: List[float], 
        cases: List[Dict], 
        module: str, 
        top_k: int = 5
    ) -> List[Dict]:
        """
        按模块检索相似案例
        
        Args:
            query_embedding: 查询向量
            cases: 案例列表
            module: 内核模块
            top_k: 返回前K个结果
            
        Returns:
            相似案例列表
        """
        # 过滤指定模块的案例
        filtered_cases = [c for c in cases if c.get('module') == module]
        
        return self.search_similar(query_embedding, filtered_cases, top_k)
    
    def search_by_keywords(
        self, 
        keywords: List[str], 
        cases: List[Dict], 
        top_k: int = 5
    ) -> List[Dict]:
        """
        按关键词检索案例
        
        Args:
            keywords: 关键词列表
            cases: 案例列表
            top_k: 返回前K个结果
            
        Returns:
            匹配案例列表
        """
        results = []
        
        for case in cases:
            # 计算关键词匹配分数
            text = f"{case.get('title', '')} {case.get('phenomenon', '')} {case.get('root_cause', '')} {case.get('solution', '')}"
            text_lower = text.lower()
            
            match_count = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    match_count += 1
            
            if match_count > 0:
                match_score = match_count / len(keywords)
                result = {
                    'case_id': case.get('case_id'),
                    'title': case.get('title'),
                    'phenomenon': case.get('phenomenon'),
                    'root_cause': case.get('root_cause'),
                    'solution': case.get('solution'),
                    'module': case.get('module'),
                    'source': case.get('source'),
                    'quality_score': case.get('quality_score'),
                    'match_score': match_score,
                    'matched_keywords': match_count
                }
                results.append(result)
        
        # 按匹配分数排序
        results.sort(key=lambda x: (x['match_score'], x['quality_score']), reverse=True)
        
        return results[:top_k]
    
    def hybrid_search(
        self,
        query_embedding: List[float],
        keywords: List[str],
        cases: List[Dict],
        top_k: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict]:
        """
        混合检索（向量 + 关键词）
        
        Args:
            query_embedding: 查询向量
            keywords: 关键词列表
            cases: 案例列表
            top_k: 返回前K个结果
            vector_weight: 向量检索权重
            keyword_weight: 关键词检索权重
            
        Returns:
            混合检索结果
        """
        results = []
        
        for case in cases:
            # 计算向量相似度
            vector_score = 0.0
            if case.get('embedding') and len(case['embedding']) > 0:
                vector_score = self._cosine_similarity(query_embedding, case['embedding'])
            
            # 计算关键词匹配分数
            keyword_score = 0.0
            if keywords:
                text = f"{case.get('title', '')} {case.get('phenomenon', '')} {case.get('root_cause', '')} {case.get('solution', '')}"
                text_lower = text.lower()
                
                match_count = sum(1 for kw in keywords if kw.lower() in text_lower)
                keyword_score = match_count / len(keywords)
            
            # 计算综合分数
            combined_score = vector_weight * vector_score + keyword_weight * keyword_score
            
            if combined_score > 0:
                result = {
                    'case_id': case.get('case_id'),
                    'title': case.get('title'),
                    'phenomenon': case.get('phenomenon'),
                    'root_cause': case.get('root_cause'),
                    'solution': case.get('solution'),
                    'module': case.get('module'),
                    'source': case.get('source'),
                    'quality_score': case.get('quality_score'),
                    'vector_score': vector_score,
                    'keyword_score': keyword_score,
                    'combined_score': combined_score
                }
                results.append(result)
        
        # 按综合分数排序
        results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return results[:top_k]


vector_retriever = VectorRetriever()