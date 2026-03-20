#!/usr/bin/env python3
"""
RAG系统命令行工具
提供命令行接口用于案例检索、问答和分析
"""
import os
import sys
import json
import argparse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
import django
django.setup()

from cases.models import TrainingCase
from cases.rag import VectorRetriever, CaseRecommender, get_qa_engine
from cases.acquisition.vector_service import get_vector_service
from cases.analysis.skill_storage import SKILLStorage
from cases.analysis.issue_analyzer import IssueAnalyzer


def cmd_search(args):
    """检索相似案例"""
    print("=" * 70)
    print("案例检索")
    print("=" * 70)
    print(f"\n查询: {args.query}")
    print(f"Top-K: {args.top_k}")
    print(f"阈值: {args.threshold}")
    print("-" * 70)
    
    vector_service = get_vector_service(model='qwen2.5:0.5b', llm_type='ollama')
    query_embedding = vector_service.generate_embedding(args.query)
    
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
        top_k=args.top_k,
        threshold=args.threshold
    )
    
    if not similar_cases:
        print("\n未找到相似案例")
        return
    
    print(f"\n找到 {len(similar_cases)} 个相似案例:\n")
    
    for i, case in enumerate(similar_cases, 1):
        print(f"{i}. {case['title']}")
        print(f"   相似度: {case['similarity']:.2%}")
        print(f"   模块: {case.get('module', 'N/A')}")
        print(f"   来源: {case.get('source', 'N/A')}")
        if case.get('root_cause'):
            print(f"   根本原因: {case['root_cause'][:100]}...")
        print()
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            for case in similar_cases:
                if 'embedding' in case:
                    del case['embedding']
            json.dump(similar_cases, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {args.output}")


def cmd_recommend(args):
    """推荐案例"""
    print("=" * 70)
    print("案例推荐")
    print("=" * 70)
    print(f"\n问题描述: {args.problem}")
    print(f"Top-K: {args.top_k}")
    print(f"最小相似度: {args.min_similarity}")
    print("-" * 70)
    
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
        args.problem,
        cases,
        top_k=args.top_k,
        min_similarity=args.min_similarity
    )
    
    if not recommendations:
        print("\n未找到推荐案例")
        return
    
    print(f"\n推荐 {len(recommendations)} 个案例:\n")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['title']}")
        print(f"   相似度: {rec['similarity']:.2%}")
        print(f"   置信度: {rec['confidence']:.2%}")
        print(f"   推荐理由: {rec['recommendation_reason']}")
        print()


def cmd_qa(args):
    """智能问答"""
    print("=" * 70)
    print("智能问答")
    print("=" * 70)
    print(f"\n问题: {args.question}")
    print("-" * 70)
    
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
        args.question,
        cases,
        top_k=args.top_k,
        min_similarity=args.min_similarity
    )
    
    print(f"\n答案:\n{result['answer']}\n")
    print(f"置信度: {result['confidence']:.2%}")
    print(f"引用案例: {len(result['cases'])}个\n")
    
    for i, case in enumerate(result['cases'][:2], 1):
        print(f"  {i}. {case['title'][:60]}")
        print(f"     相似度: {case['similarity']:.2%}")
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            output_data = {
                'question': args.question,
                'answer': result['answer'],
                'confidence': result['confidence'],
                'cases': result['cases']
            }
            for case in output_data['cases']:
                if 'embedding' in case:
                    del case['embedding']
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {args.output}")


def cmd_analyze(args):
    """问题分析"""
    print("=" * 70)
    print("问题分析")
    print("=" * 70)
    print(f"\n问题描述: {args.description}")
    if args.logs:
        print(f"日志: {args.logs[:100]}...")
    print("-" * 70)
    
    storage = SKILLStorage()
    analyzer = IssueAnalyzer(storage)
    
    result = analyzer.analyze_issue(
        args.description,
        args.logs if args.logs else None
    )
    
    print(f"\n使用的技能: {result['relevant_skills_used']}")
    print(f"置信度: {result['confidence_score']:.2%}")
    print(f"相似案例: {len(result['similar_cases'])}个\n")
    
    if result['similar_cases']:
        print("相似案例:")
        for i, case in enumerate(result['similar_cases'][:3], 1):
            print(f"  {i}. {case['title'][:60]}")
            print(f"     相似度: {case['similarity']:.2%}")
    
    print(f"\n分析摘要:\n{result['summary']}")
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            output_data = {
                'issue_description': result['issue_description'],
                'confidence_score': result['confidence_score'],
                'similar_cases': result['similar_cases'],
                'summary': result['summary']
            }
            for case in output_data['similar_cases']:
                if 'embedding' in case:
                    del case['embedding']
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {args.output}")


def main():
    parser = argparse.ArgumentParser(
        description='RAG系统命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 检索相似案例
  python rag_cli.py search "kernel panic 内存崩溃" --top-k 5
  
  # 推荐案例
  python rag_cli.py recommend "系统出现内存泄漏问题"
  
  # 智能问答
  python rag_cli.py qa "如何排查内核死锁问题？"
  
  # 问题分析
  python rag_cli.py analyze --description "系统崩溃" --logs "kernel panic log"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    parser_search = subparsers.add_parser('search', help='检索相似案例')
    parser_search.add_argument('query', help='查询内容')
    parser_search.add_argument('--top-k', type=int, default=5, help='返回案例数量')
    parser_search.add_argument('--threshold', type=float, default=0.5, help='相似度阈值')
    parser_search.add_argument('--output', help='输出文件路径（JSON格式）')
    parser_search.set_defaults(func=cmd_search)
    
    parser_recommend = subparsers.add_parser('recommend', help='推荐案例')
    parser_recommend.add_argument('problem', help='问题描述')
    parser_recommend.add_argument('--top-k', type=int, default=5, help='返回案例数量')
    parser_recommend.add_argument('--min-similarity', type=float, default=0.5, help='最小相似度')
    parser_recommend.set_defaults(func=cmd_recommend)
    
    parser_qa = subparsers.add_parser('qa', help='智能问答')
    parser_qa.add_argument('question', help='问题')
    parser_qa.add_argument('--top-k', type=int, default=3, help='引用案例数量')
    parser_qa.add_argument('--min-similarity', type=float, default=0.5, help='最小相似度')
    parser_qa.add_argument('--output', help='输出文件路径（JSON格式）')
    parser_qa.set_defaults(func=cmd_qa)
    
    parser_analyze = subparsers.add_parser('analyze', help='问题分析')
    parser_analyze.add_argument('--description', required=True, help='问题描述')
    parser_analyze.add_argument('--logs', help='日志内容')
    parser_analyze.add_argument('--output', help='输出文件路径（JSON格式）')
    parser_analyze.set_defaults(func=cmd_analyze)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()