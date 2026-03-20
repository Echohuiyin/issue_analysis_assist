"""
RAG系统API视图
提供REST API接口用于案例检索、推荐、问答和分析
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from typing import Dict, List

from cases.models import TrainingCase
from cases.rag import VectorRetriever, CaseRecommender, get_qa_engine
from cases.acquisition.vector_service import get_vector_service
from cases.analysis.skill_storage import SKILLStorage
from cases.analysis.issue_analyzer import IssueAnalyzer


@csrf_exempt
@require_http_methods(["POST"])
def search_similar_cases(request):
    """
    检索相似案例API
    
    请求体:
    {
        "query": "问题描述",
        "top_k": 5,
        "threshold": 0.5
    }
    
    返回:
    {
        "success": true,
        "cases": [...],
        "count": 3
    }
    """
    try:
        data = json.loads(request.body)
        query = data.get('query', '')
        top_k = data.get('top_k', 5)
        threshold = data.get('threshold', 0.5)
        
        if not query:
            return JsonResponse({
                'success': False,
                'error': '查询内容不能为空'
            }, status=400)
        
        vector_service = get_vector_service(model='qwen2.5:0.5b', llm_type='ollama')
        query_embedding = vector_service.generate_embedding(query)
        
        cases = list(TrainingCase.objects.exclude(
            embedding__isnull=True
        ).exclude(
            embedding__exact=[]
        ).values(
            'case_id', 'title', 'phenomenon', 'root_cause', 'solution',
            'module', 'source', 'quality_score', 'embedding'
        ))
        
        retriever = VectorRetriever()
        similar_cases = retriever.search_similar(
            query_embedding,
            cases,
            top_k=top_k,
            threshold=threshold
        )
        
        for case in similar_cases:
            if 'embedding' in case:
                del case['embedding']
        
        return JsonResponse({
            'success': True,
            'cases': similar_cases,
            'count': len(similar_cases),
            'query': query
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def recommend_cases(request):
    """
    案例推荐API
    
    请求体:
    {
        "problem_description": "问题描述",
        "top_k": 5,
        "min_similarity": 0.5
    }
    
    返回:
    {
        "success": true,
        "recommendations": [...],
        "count": 3
    }
    """
    try:
        data = json.loads(request.body)
        problem_description = data.get('problem_description', '')
        top_k = data.get('top_k', 5)
        min_similarity = data.get('min_similarity', 0.5)
        
        if not problem_description:
            return JsonResponse({
                'success': False,
                'error': '问题描述不能为空'
            }, status=400)
        
        vector_service = get_vector_service(model='qwen2.5:0.5b', llm_type='ollama')
        
        cases = list(TrainingCase.objects.exclude(
            embedding__isnull=True
        ).exclude(
            embedding__exact=[]
        ).values(
            'case_id', 'title', 'phenomenon', 'root_cause', 'solution',
            'module', 'source', 'quality_score', 'embedding'
        ))
        
        recommender = CaseRecommender(vector_service)
        recommendations = recommender.recommend(
            problem_description,
            cases,
            top_k=top_k,
            min_similarity=min_similarity
        )
        
        for rec in recommendations:
            if 'embedding' in rec:
                del rec['embedding']
        
        return JsonResponse({
            'success': True,
            'recommendations': recommendations,
            'count': len(recommendations),
            'problem_description': problem_description
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def qa_answer(request):
    """
    智能问答API
    
    请求体:
    {
        "question": "问题",
        "top_k": 3,
        "min_similarity": 0.5
    }
    
    返回:
    {
        "success": true,
        "answer": "答案",
        "confidence": 0.85,
        "cases": [...],
        "sources": [...]
    }
    """
    try:
        data = json.loads(request.body)
        question = data.get('question', '')
        top_k = data.get('top_k', 3)
        min_similarity = data.get('min_similarity', 0.5)
        
        if not question:
            return JsonResponse({
                'success': False,
                'error': '问题不能为空'
            }, status=400)
        
        cases = list(TrainingCase.objects.exclude(
            embedding__isnull=True
        ).exclude(
            embedding__exact=[]
        ).values(
            'case_id', 'title', 'phenomenon', 'root_cause', 'solution',
            'module', 'source', 'quality_score', 'embedding'
        ))
        
        qa_engine = get_qa_engine()
        result = qa_engine.answer(
            question,
            cases,
            top_k=top_k,
            min_similarity=min_similarity
        )
        
        for case in result.get('cases', []):
            if 'embedding' in case:
                del case['embedding']
        
        return JsonResponse({
            'success': True,
            'answer': result['answer'],
            'confidence': result['confidence'],
            'cases': result['cases'],
            'sources': result['sources'],
            'question': question
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def qa_chat(request):
    """
    多轮对话API
    
    请求体:
    {
        "conversation_history": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ],
        "new_question": "新问题",
        "top_k": 3
    }
    
    返回:
    {
        "success": true,
        "answer": "答案",
        "confidence": 0.85,
        "cases": [...]
    }
    """
    try:
        data = json.loads(request.body)
        conversation_history = data.get('conversation_history', [])
        new_question = data.get('new_question', '')
        top_k = data.get('top_k', 3)
        
        if not new_question:
            return JsonResponse({
                'success': False,
                'error': '新问题不能为空'
            }, status=400)
        
        cases = list(TrainingCase.objects.exclude(
            embedding__isnull=True
        ).exclude(
            embedding__exact=[]
        ).values(
            'case_id', 'title', 'phenomenon', 'root_cause', 'solution',
            'module', 'source', 'quality_score', 'embedding'
        ))
        
        qa_engine = get_qa_engine()
        result = qa_engine.chat(
            conversation_history,
            new_question,
            cases,
            top_k=top_k
        )
        
        for case in result.get('cases', []):
            if 'embedding' in case:
                del case['embedding']
        
        return JsonResponse({
            'success': True,
            'answer': result['answer'],
            'confidence': result['confidence'],
            'cases': result['cases'],
            'new_question': new_question
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def analyze_issue(request):
    """
    问题分析API
    
    请求体:
    {
        "issue_description": "问题描述",
        "logs": "日志内容（可选）"
    }
    
    返回:
    {
        "success": true,
        "analysis": {
            "relevant_skills_used": [...],
            "confidence_score": 0.75,
            "similar_cases": [...],
            "summary": "..."
        }
    }
    """
    try:
        data = json.loads(request.body)
        issue_description = data.get('issue_description', '')
        logs = data.get('logs', '')
        
        if not issue_description:
            return JsonResponse({
                'success': False,
                'error': '问题描述不能为空'
            }, status=400)
        
        storage = SKILLStorage()
        analyzer = IssueAnalyzer(storage)
        
        result = analyzer.analyze_issue(issue_description, logs if logs else None)
        
        for case in result.get('similar_cases', []):
            if 'embedding' in case:
                del case['embedding']
        
        return JsonResponse({
            'success': True,
            'analysis': {
                'issue_description': result['issue_description'],
                'relevant_skills_used': result['relevant_skills_used'],
                'confidence_score': result['confidence_score'],
                'similar_cases': result['similar_cases'],
                'summary': result['summary']
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_health(request):
    """
    API健康检查
    
    返回:
    {
        "status": "ok",
        "service": "RAG API",
        "version": "1.0"
    }
    """
    return JsonResponse({
        'status': 'ok',
        'service': 'RAG API',
        'version': '1.0',
        'training_cases': TrainingCase.objects.count()
    })