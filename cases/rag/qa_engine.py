"""
RAG智能问答引擎
基于检索增强生成实现智能问答功能
"""
from typing import List, Dict, Optional
from .vector_retriever import VectorRetriever
from .case_recommender import CaseRecommender


class QAEngine:
    """智能问答引擎"""
    
    # 问答提示词模板
    QA_PROMPT_TEMPLATE = """你是一名Linux内核专家，请基于以下相关案例回答用户的问题。

相关案例：
{cases}

用户问题：{question}

请提供详细的回答，包括：
1. 问题分析
2. 可能的原因
3. 排查步骤
4. 解决方案

如果参考了某个案例，请注明案例来源。

回答："""

    # 多轮对话提示词模板
    CHAT_PROMPT_TEMPLATE = """你是一名Linux内核专家，正在与用户进行多轮对话。

对话历史：
{conversation_history}

相关案例：
{cases}

用户最新问题：{question}

请基于对话历史和相关案例，提供连贯的回答。

回答："""
    
    def __init__(self, llm, vector_service=None):
        """
        初始化问答引擎
        
        Args:
            llm: 大语言模型
            vector_service: 向量服务
        """
        self.llm = llm
        self.vector_service = vector_service
        self.retriever = VectorRetriever()
        self.recommender = CaseRecommender(vector_service)
    
    def answer(
        self, 
        question: str, 
        cases: List[Dict],
        query_embedding: Optional[List[float]] = None,
        top_k: int = 3,
        min_similarity: float = 0.5
    ) -> Dict:
        """
        基于检索结果生成答案
        
        Args:
            question: 用户问题
            cases: 案例列表
            query_embedding: 查询向量（可选）
            top_k: 检索案例数量
            min_similarity: 最小相似度阈值
            
        Returns:
            答案和引用案例
        """
        # 如果没有提供查询向量，则生成
        if query_embedding is None and self.vector_service:
            query_embedding = self.vector_service.generate_embedding(question)
        
        if not query_embedding:
            return {
                'answer': '抱歉，无法处理您的问题。',
                'cases': [],
                'confidence': 0.0
            }
        
        # 检索相关案例
        relevant_cases = self.retriever.search_similar(
            query_embedding,
            cases,
            top_k=top_k,
            threshold=min_similarity
        )
        
        if not relevant_cases:
            return {
                'answer': '抱歉，没有找到相关的案例来回答您的问题。',
                'cases': [],
                'confidence': 0.0
            }
        
        # 构建案例上下文
        cases_context = self._build_cases_context(relevant_cases)
        
        # 生成提示词
        prompt = self.QA_PROMPT_TEMPLATE.format(
            cases=cases_context,
            question=question
        )
        
        # 调用LLM生成答案
        try:
            answer = self.llm.generate(prompt, max_tokens=1000)
        except Exception as e:
            answer = f"生成答案时出错: {str(e)}"
        
        # 计算置信度
        confidence = self._calculate_confidence(relevant_cases)
        
        # 提取来源信息
        sources = self._extract_sources(relevant_cases)
        
        return {
            'answer': answer,
            'cases': relevant_cases,
            'confidence': confidence,
            'sources': sources
        }
    
    def chat(
        self, 
        conversation_history: List[Dict], 
        new_question: str,
        cases: List[Dict],
        query_embedding: Optional[List[float]] = None,
        top_k: int = 3
    ) -> Dict:
        """
        多轮对话
        
        Args:
            conversation_history: 对话历史
            new_question: 新问题
            cases: 案例列表
            query_embedding: 查询向量
            top_k: 检索案例数量
            
        Returns:
            答案和引用案例
        """
        # 如果没有提供查询向量，则生成
        if query_embedding is None and self.vector_service:
            query_embedding = self.vector_service.generate_embedding(new_question)
        
        if not query_embedding:
            return {
                'answer': '抱歉，无法处理您的问题。',
                'cases': [],
                'confidence': 0.0
            }
        
        # 检索相关案例
        relevant_cases = self.retriever.search_similar(
            query_embedding,
            cases,
            top_k=top_k,
            threshold=0.5
        )
        
        # 构建对话历史
        history_text = self._build_conversation_history(conversation_history)
        
        # 构建案例上下文
        cases_context = self._build_cases_context(relevant_cases) if relevant_cases else "无相关案例"
        
        # 生成提示词
        prompt = self.CHAT_PROMPT_TEMPLATE.format(
            conversation_history=history_text,
            cases=cases_context,
            question=new_question
        )
        
        # 调用LLM生成答案
        try:
            answer = self.llm.generate(prompt, max_tokens=1000)
        except Exception as e:
            answer = f"生成答案时出错: {str(e)}"
        
        # 计算置信度
        confidence = self._calculate_confidence(relevant_cases) if relevant_cases else 0.0
        
        # 提取来源信息
        sources = self._extract_sources(relevant_cases) if relevant_cases else []
        
        return {
            'answer': answer,
            'cases': relevant_cases,
            'confidence': confidence,
            'sources': sources
        }
    
    def _build_cases_context(self, cases: List[Dict]) -> str:
        """
        构建案例上下文
        
        Args:
            cases: 案例列表
            
        Returns:
            格式化的案例文本
        """
        context_parts = []
        
        for i, case in enumerate(cases, 1):
            part = f"""
案例 {i}：
标题：{case.get('title', '无标题')}
问题现象：{case.get('phenomenon', '无描述')[:300]}
根本原因：{case.get('root_cause', '无原因')[:200]}
解决方案：{case.get('solution', '无方案')[:200]}
来源：{case.get('source', '未知')}
相似度：{case.get('similarity', 0.0):.2%}
"""
            context_parts.append(part)
        
        return "\n".join(context_parts)
    
    def _build_conversation_history(self, history: List[Dict]) -> str:
        """
        构建对话历史文本
        
        Args:
            history: 对话历史列表
            
        Returns:
            格式化的对话历史
        """
        if not history:
            return "无对话历史"
        
        history_parts = []
        for turn in history[-5:]:  # 只保留最近5轮对话
            role = turn.get('role', 'user')
            content = turn.get('content', '')
            history_parts.append(f"{role}: {content}")
        
        return "\n".join(history_parts)
    
    def _calculate_confidence(self, cases: List[Dict]) -> float:
        """
        计算答案置信度
        
        Args:
            cases: 相关案例列表
            
        Returns:
            置信度分数（0-1）
        """
        if not cases:
            return 0.0
        
        # 基于案例相似度和质量计算置信度
        total_score = 0.0
        for case in cases:
            similarity = case.get('similarity', 0.0)
            quality = case.get('quality_score', 0.0) / 100.0
            score = similarity * 0.7 + quality * 0.3
            total_score += score
        
        avg_score = total_score / len(cases)
        
        # 根据案例数量调整置信度
        case_count_factor = min(len(cases) / 3.0, 1.0)
        
        return min(avg_score * case_count_factor, 1.0)
    
    def _extract_sources(self, cases: List[Dict]) -> List[Dict]:
        """
        提取案例来源信息
        
        Args:
            cases: 案例列表
            
        Returns:
            来源信息列表
        """
        sources = []
        for case in cases:
            source = {
                'case_id': case.get('case_id'),
                'title': case.get('title'),
                'source': case.get('source'),
                'similarity': case.get('similarity'),
                'url': case.get('url', '')
            }
            sources.append(source)
        
        return sources


qa_engine = None


def get_qa_engine(llm=None, vector_service=None):
    """
    获取问答引擎实例
    
    Args:
        llm: 大语言模型
        vector_service: 向量服务
        
    Returns:
        QAEngine实例
    """
    global qa_engine
    if qa_engine is None:
        if llm is None:
            from cases.acquisition.llm_integration import get_llm
            llm = get_llm('ollama', model='qwen2.5:0.5b')
        if vector_service is None:
            from cases.acquisition.vector_service import get_vector_service
            vector_service = get_vector_service(llm_type='ollama', model='qwen2.5:0.5b')
        qa_engine = QAEngine(llm, vector_service)
    return qa_engine