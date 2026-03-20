"""
RAG系统Web视图
提供用户友好的Web界面
"""
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from cases.models import TrainingCase
from cases.rag import VectorRetriever, CaseRecommender, get_qa_engine
from cases.acquisition.vector_service import get_vector_service
from cases.analysis.skill_storage import SKILLStorage
from cases.analysis.issue_analyzer import IssueAnalyzer


@method_decorator(csrf_exempt, name='dispatch')
class RAGSearchView(View):
    """RAG案例检索页面"""
    
    def get(self, request):
        """显示检索页面"""
        return render(request, 'rag/search.html')
    
    def post(self, request):
        """处理检索请求"""
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
            top_k = int(data.get('top_k', 5))
            threshold = float(data.get('threshold', 0.5))
            
            if not query:
                return JsonResponse({
                    'success': False,
                    'error': '请输入查询内容'
                })
            
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
                'count': len(similar_cases)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class RAGQAView(View):
    """RAG智能问答页面"""
    
    def get(self, request):
        """显示问答页面"""
        return render(request, 'rag/qa.html')
    
    def post(self, request):
        """处理问答请求"""
        try:
            data = json.loads(request.body)
            question = data.get('question', '')
            top_k = int(data.get('top_k', 3))
            min_similarity = float(data.get('min_similarity', 0.5))
            
            if not question:
                return JsonResponse({
                    'success': False,
                    'error': '请输入问题'
                })
            
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
                'cases': result['cases']
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class RAGAnalyzeView(View):
    """RAG问题分析页面"""
    
    def get(self, request):
        """显示分析页面"""
        return render(request, 'rag/analyze.html')
    
    def post(self, request):
        """处理分析请求"""
        try:
            data = json.loads(request.body)
            issue_description = data.get('issue_description', '')
            logs = data.get('logs', '')
            
            if not issue_description:
                return JsonResponse({
                    'success': False,
                    'error': '请输入问题描述'
                })
            
            storage = SKILLStorage()
            analyzer = IssueAnalyzer(storage)
            
            result = analyzer.analyze_issue(
                issue_description,
                logs if logs else None
            )
            
            for case in result.get('similar_cases', []):
                if 'embedding' in case:
                    del case['embedding']
            
            return JsonResponse({
                'success': True,
                'analysis': {
                    'confidence_score': result['confidence_score'],
                    'similar_cases': result['similar_cases'],
                    'summary': result['summary']
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class RAGDashboardView(View):
    """RAG系统仪表板"""
    
    def get(self, request):
        """显示仪表板"""
        total_cases = TrainingCase.objects.count()
        cases_with_embeddings = TrainingCase.objects.exclude(
            embedding__isnull=True
        ).exclude(
            embedding__exact=[]
        ).count()
        
        module_stats = {}
        for case in TrainingCase.objects.all():
            module = case.module or 'other'
            module_stats[module] = module_stats.get(module, 0) + 1
        
        source_stats = {}
        for case in TrainingCase.objects.all():
            source = case.source or 'unknown'
            source_stats[source] = source_stats.get(source, 0) + 1
        
        context = {
            'total_cases': total_cases,
            'cases_with_embeddings': cases_with_embeddings,
            'module_stats': module_stats,
            'source_stats': source_stats,
        }
        
        return render(request, 'rag/dashboard.html', context)