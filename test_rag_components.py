#!/usr/bin/env python3
"""
测试RAG系统组件
验证向量检索和案例推荐功能
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
import django
django.setup()

from cases.models import TrainingCase
from cases.rag import VectorRetriever, CaseRecommender
from cases.acquisition.vector_service import get_vector_service


def test_vector_retriever():
    print("=" * 70)
    print("测试向量检索器")
    print("=" * 70)
    print()
    
    # 获取所有训练案例
    cases = list(TrainingCase.objects.all().values(
        'case_id', 'title', 'phenomenon', 'root_cause', 'solution',
        'module', 'source', 'quality_score', 'embedding'
    ))
    
    print(f"训练案例数量: {len(cases)}")
    print()
    
    # 初始化向量服务
    vector_service = get_vector_service(llm_type='ollama', model='qwen2.5:0.5b')
    
    # 测试查询
    test_queries = [
        "kernel panic 内存崩溃",
        "内存泄漏问题",
        "死锁 deadlock"
    ]
    
    retriever = VectorRetriever()
    
    for query in test_queries:
        print(f"查询: {query}")
        print("-" * 70)
        
        # 生成查询向量
        query_embedding = vector_service.generate_embedding(query)
        
        if not query_embedding:
            print("  无法生成查询向量")
            continue
        
        # 检索相似案例
        similar_cases = retriever.search_similar(
            query_embedding,
            cases,
            top_k=3,
            threshold=0.5
        )
        
        print(f"  找到 {len(similar_cases)} 个相似案例:")
        for i, case in enumerate(similar_cases, 1):
            print(f"  {i}. {case['title'][:50]}...")
            print(f"     相似度: {case['similarity']:.2%}")
            print(f"     模块: {case['module']}")
            print(f"     来源: {case['source']}")
            print()
    
    return True


def test_case_recommender():
    print("=" * 70)
    print("测试案例推荐引擎")
    print("=" * 70)
    print()
    
    # 获取所有训练案例
    cases = list(TrainingCase.objects.all().values(
        'case_id', 'title', 'phenomenon', 'root_cause', 'solution',
        'module', 'source', 'quality_score', 'embedding'
    ))
    
    # 初始化向量服务
    vector_service = get_vector_service(llm_type='ollama', model='qwen2.5:0.5b')
    
    # 测试问题
    test_problems = [
        "系统运行一段时间后出现kernel panic，日志显示内存分配失败",
        "内核模块加载后系统死锁，无法响应"
    ]
    
    recommender = CaseRecommender(vector_service)
    
    for problem in test_problems:
        print(f"问题: {problem}")
        print("-" * 70)
        
        # 推荐案例
        recommendations = recommender.recommend(
            problem,
            cases,
            top_k=3,
            min_similarity=0.5
        )
        
        print(f"  推荐 {len(recommendations)} 个相关案例:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec['title'][:50]}...")
            print(f"     相似度: {rec['similarity']:.2%}")
            print(f"     置信度: {rec['confidence']:.2%}")
            print(f"     推荐理由: {rec['recommendation_reason']}")
            print()
    
    return True


def test_hybrid_search():
    print("=" * 70)
    print("测试混合检索")
    print("=" * 70)
    print()
    
    # 获取所有训练案例
    cases = list(TrainingCase.objects.all().values(
        'case_id', 'title', 'phenomenon', 'root_cause', 'solution',
        'module', 'source', 'quality_score', 'embedding'
    ))
    
    # 初始化向量服务
    vector_service = get_vector_service(llm_type='ollama', model='qwen2.5:0.5b')
    
    # 测试查询
    query = "内核内存泄漏导致系统崩溃"
    keywords = ["内存", "泄漏", "崩溃"]
    
    print(f"查询: {query}")
    print(f"关键词: {', '.join(keywords)}")
    print("-" * 70)
    
    # 生成查询向量
    query_embedding = vector_service.generate_embedding(query)
    
    # 混合检索
    retriever = VectorRetriever()
    results = retriever.hybrid_search(
        query_embedding,
        keywords,
        cases,
        top_k=3,
        vector_weight=0.7,
        keyword_weight=0.3
    )
    
    print(f"  找到 {len(results)} 个相关案例:")
    for i, case in enumerate(results, 1):
        print(f"  {i}. {case['title'][:50]}...")
        print(f"     向量分数: {case['vector_score']:.2%}")
        print(f"     关键词分数: {case['keyword_score']:.2%}")
        print(f"     综合分数: {case['combined_score']:.2%}")
        print()
    
    return True


def main():
    print()
    print("=" * 70)
    print("RAG系统组件测试")
    print("=" * 70)
    print()
    
    try:
        # 测试向量检索器
        test_vector_retriever()
        print()
        
        # 测试案例推荐引擎
        test_case_recommender()
        print()
        
        # 测试混合检索
        test_hybrid_search()
        print()
        
        print("=" * 70)
        print("✅ 所有测试通过！")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)