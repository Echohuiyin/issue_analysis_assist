"""
案例推荐引擎
基于问题描述推荐相关案例
"""
from typing import List, Dict, Optional
from .vector_retriever import VectorRetriever


class CaseRecommender:
    """案例推荐引擎"""
    
    def __init__(self, vector_service=None):
        """
        初始化案例推荐引擎
        
        Args:
            vector_service: 向量服务（用于生成查询向量）
        """
        self.vector_service = vector_service
        self.retriever = VectorRetriever()
    
    def recommend(
        self, 
        problem_description: str, 
        cases: List[Dict],
        query_embedding: Optional[List[float]] = None,
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> List[Dict]:
        """
        基于问题描述推荐相关案例
        
        Args:
            problem_description: 问题描述
            cases: 案例列表
            query_embedding: 查询向量（可选，如果不提供则自动生成）
            top_k: 返回前K个推荐
            min_similarity: 最小相似度阈值
            
        Returns:
            推荐案例列表（包含推荐理由）
        """
        # 如果没有提供查询向量，则生成
        if query_embedding is None and self.vector_service:
            query_embedding = self.vector_service.generate_embedding(problem_description)
        
        if not query_embedding:
            return []
        
        # 检索相似案例
        similar_cases = self.retriever.search_similar(
            query_embedding, 
            cases, 
            top_k=top_k * 2,  # 获取更多候选
            threshold=min_similarity
        )
        
        # 为每个案例添加推荐理由
        recommendations = []
        for case in similar_cases[:top_k]:
            recommendation = {
                **case,
                'recommendation_reason': self._generate_reason(case, problem_description),
                'confidence': self._calculate_confidence(case)
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    def recommend_by_module(
        self,
        problem_description: str,
        cases: List[Dict],
        module: str,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        按模块推荐案例
        
        Args:
            problem_description: 问题描述
            cases: 案例列表
            module: 内核模块
            query_embedding: 查询向量
            top_k: 返回前K个推荐
            
        Returns:
            推荐案例列表
        """
        # 如果没有提供查询向量，则生成
        if query_embedding is None and self.vector_service:
            query_embedding = self.vector_service.generate_embedding(problem_description)
        
        if not query_embedding:
            return []
        
        # 按模块检索
        similar_cases = self.retriever.search_by_module(
            query_embedding,
            cases,
            module,
            top_k=top_k
        )
        
        # 添加推荐理由
        recommendations = []
        for case in similar_cases:
            recommendation = {
                **case,
                'recommendation_reason': f"该案例属于{module}模块，与您的问题高度相关",
                'confidence': case.get('similarity', 0.0)
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_reason(self, case: Dict, problem_description: str) -> str:
        """
        生成推荐理由
        
        Args:
            case: 案例信息
            problem_description: 问题描述
            
        Returns:
            推荐理由
        """
        similarity = case.get('similarity', 0.0)
        module = case.get('module', 'other')
        source = case.get('source', 'unknown')
        
        reasons = []
        
        # 相似度理由
        if similarity >= 0.8:
            reasons.append("问题描述高度相似")
        elif similarity >= 0.7:
            reasons.append("问题描述较为相似")
        elif similarity >= 0.6:
            reasons.append("问题描述有一定相似性")
        
        # 模块理由
        if module != 'other':
            reasons.append(f"属于{module}模块")
        
        # 来源理由
        if source in ['stackoverflow', 'github']:
            reasons.append(f"来自高质量来源({source})")
        
        if reasons:
            return "，".join(reasons)
        else:
            return "基于向量相似度推荐"
    
    def _calculate_confidence(self, case: Dict) -> float:
        """
        计算推荐置信度
        
        Args:
            case: 案例信息
            
        Returns:
            置信度分数（0-1）
        """
        similarity = case.get('similarity', 0.0)
        quality_score = case.get('quality_score', 0.0)
        
        # 综合相似度和质量分数
        confidence = similarity * 0.7 + (quality_score / 100.0) * 0.3
        
        return min(confidence, 1.0)
    
    def explain_recommendation(self, case: Dict) -> Dict:
        """
        解释推荐理由
        
        Args:
            case: 案例信息
            
        Returns:
            推荐理由说明
        """
        explanation = {
            'case_id': case.get('case_id'),
            'title': case.get('title'),
            'similarity': case.get('similarity', 0.0),
            'quality_score': case.get('quality_score', 0.0),
            'confidence': case.get('confidence', 0.0),
            'reasons': []
        }
        
        # 相似度分析
        similarity = case.get('similarity', 0.0)
        if similarity >= 0.8:
            explanation['reasons'].append({
                'type': 'similarity',
                'level': 'high',
                'message': f"向量相似度很高({similarity:.2%})，问题描述非常接近"
            })
        elif similarity >= 0.7:
            explanation['reasons'].append({
                'type': 'similarity',
                'level': 'medium',
                'message': f"向量相似度较高({similarity:.2%})，问题描述较为相似"
            })
        else:
            explanation['reasons'].append({
                'type': 'similarity',
                'level': 'low',
                'message': f"向量相似度一般({similarity:.2%})，问题描述有一定相似性"
            })
        
        # 质量分析
        quality_score = case.get('quality_score', 0.0)
        if quality_score >= 70:
            explanation['reasons'].append({
                'type': 'quality',
                'level': 'high',
                'message': f"案例质量很高({quality_score:.1f}分)，内容详细完整"
            })
        elif quality_score >= 50:
            explanation['reasons'].append({
                'type': 'quality',
                'level': 'medium',
                'message': f"案例质量良好({quality_score:.1f}分)，内容基本完整"
            })
        
        # 模块分析
        module = case.get('module', 'other')
        if module != 'other':
            explanation['reasons'].append({
                'type': 'module',
                'level': 'info',
                'message': f"案例分类为{module}模块，可能涉及相关问题"
            })
        
        # 来源分析
        source = case.get('source', 'unknown')
        if source in ['stackoverflow', 'github']:
            explanation['reasons'].append({
                'type': 'source',
                'level': 'info',
                'message': f"案例来自{source}，通常是高质量的技术讨论"
            })
        
        return explanation


case_recommender = CaseRecommender()