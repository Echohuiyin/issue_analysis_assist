#!/usr/bin/env python3
"""
测试RAG智能问答功能
验证问答引擎和对话功能
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
import django
django.setup()

from cases.models import TrainingCase
from cases.rag import QAEngine, get_qa_engine
from cases.acquisition.vector_service import get_vector_service


def test_qa_engine():
    print("=" * 70)
    print("测试智能问答引擎")
    print("=" * 70)
    print()
    
    # 获取所有训练案例
    cases = list(TrainingCase.objects.all().values(
        'case_id', 'title', 'phenomenon', 'root_cause', 'solution',
        'module', 'source', 'quality_score', 'embedding'
    ))
    
    print(f"训练案例数量: {len(cases)}")
    print()
    
    # 初始化问答引擎
    qa_engine = get_qa_engine()
    
    # 测试问题
    test_questions = [
        "系统出现kernel panic怎么办？",
        "如何排查内核内存泄漏问题？",
        "内核死锁如何定位和解决？"
    ]
    
    for question in test_questions:
        print(f"问题: {question}")
        print("-" * 70)
        
        # 生成答案
        result = qa_engine.answer(
            question,
            cases,
            top_k=3,
            min_similarity=0.5
        )
        
        print(f"答案:")
        print(result['answer'][:500] + "...")
        print()
        print(f"置信度: {result['confidence']:.2%}")
        print(f"引用案例: {len(result['cases'])}个")
        
        for i, case in enumerate(result['cases'][:2], 1):
            print(f"  {i}. {case['title'][:50]}...")
            print(f"     相似度: {case['similarity']:.2%}")
        
        print()
    
    return True


def test_chat():
    print("=" * 70)
    print("测试多轮对话功能")
    print("=" * 70)
    print()
    
    # 获取所有训练案例
    cases = list(TrainingCase.objects.all().values(
        'case_id', 'title', 'phenomenon', 'root_cause', 'solution',
        'module', 'source', 'quality_score', 'embedding'
    ))
    
    # 初始化问答引擎
    qa_engine = get_qa_engine()
    
    # 模拟对话历史
    conversation_history = [
        {
            'role': 'user',
            'content': '我的系统出现了kernel panic'
        },
        {
            'role': 'assistant',
            'content': 'kernel panic是Linux内核的严重错误。请问您有具体的错误日志吗？'
        }
    ]
    
    # 新问题
    new_question = "日志显示是内存分配失败导致的"
    
    print("对话历史:")
    for msg in conversation_history:
        print(f"  {msg['role']}: {msg['content']}")
    print()
    print(f"新问题: {new_question}")
    print("-" * 70)
    
    # 生成答案
    result = qa_engine.chat(
        conversation_history,
        new_question,
        cases,
        top_k=3
    )
    
    print(f"答案:")
    print(result['answer'][:500] + "...")
    print()
    print(f"置信度: {result['confidence']:.2%}")
    print()
    
    return True


def main():
    print()
    print("=" * 70)
    print("RAG智能问答测试")
    print("=" * 70)
    print()
    
    try:
        # 测试问答引擎
        test_qa_engine()
        print()
        
        # 测试多轮对话
        test_chat()
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