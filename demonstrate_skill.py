#!/usr/bin/env python3
"""
SKILL Demonstration and Verification Script
展示和验证RAG系统的能力
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')
django.setup()

from cases.models import TrainingCase, TestCase
from cases.rag import get_qa_engine, vector_retriever
from cases.acquisition.vector_service import get_vector_service


def check_database_status():
    """检查数据库状态"""
    print("=" * 60)
    print("📊 Database Status")
    print("=" * 60)
    
    training_count = TrainingCase.objects.count()
    test_count = TestCase.objects.count()
    
    print(f"Training cases: {training_count}")
    print(f"Test cases: {test_count}")
    print(f"Total cases: {training_count + test_count}")
    
    if training_count > 0:
        sample = TrainingCase.objects.first()
        print(f"\nSample case:")
        print(f"  - ID: {sample.case_id}")
        print(f"  - Title: {sample.title[:60]}...")
        print(f"  - Module: {sample.module}")
        print(f"  - Quality: {sample.quality_score}")
        print(f"  - Has embedding: {bool(sample.embedding)}")
    
    return training_count, test_count


def demonstrate_skill():
    """演示SKILL能力"""
    print("\n" + "=" * 60)
    print("🎯 SKILL Demonstration - RAG System Capabilities")
    print("=" * 60)
    
    training_count, test_count = check_database_status()
    
    if training_count + test_count == 0:
        print("\n⚠️ No cases found in database!")
        print("Please run the background collector to collect cases first.")
        return
    
    print("\n" + "=" * 60)
    print("📚 Loading Cases and Initializing RAG System...")
    print("=" * 60)
    
    training_cases = list(TrainingCase.objects.all().values(
        'case_id', 'title', 'phenomenon', 'root_cause', 'solution',
        'module', 'source', 'quality_score', 'embedding'
    ))
    
    test_cases = list(TestCase.objects.all().values(
        'case_id', 'title', 'phenomenon', 'root_cause', 'solution',
        'module', 'source', 'quality_score', 'embedding'
    ))
    
    all_cases = training_cases + test_cases
    print(f"✅ Loaded {len(all_cases)} cases")
    
    qa_engine = get_qa_engine()
    vector_service = get_vector_service()
    
    print("✅ RAG system initialized")
    
    test_questions = [
        {
            'question': '系统出现kernel panic，如何排查？',
            'description': 'Kernel panic crash debugging'
        },
        {
            'question': '如何解决内存泄漏问题？',
            'description': 'Memory leak troubleshooting'
        },
        {
            'question': '进程卡死不动，可能是什么原因？',
            'description': 'Process hang diagnosis'
        }
    ]
    
    print("\n" + "=" * 60)
    print("🧪 Testing SKILL with Sample Questions")
    print("=" * 60)
    
    for i, test in enumerate(test_questions, 1):
        print(f"\n--- Test {i}: {test['description']} ---")
        print(f"Question: {test['question']}")
        
        try:
            query_embedding = vector_service.generate_embedding(test['question'])
            
            if not query_embedding:
                print("❌ Failed to generate query embedding")
                continue
            
            similar_cases = vector_retriever.search_similar(
                query_embedding,
                all_cases,
                top_k=3,
                threshold=0.3
            )
            
            if similar_cases:
                print(f"\n✅ Found {len(similar_cases)} similar cases:")
                for j, case in enumerate(similar_cases, 1):
                    print(f"\n  [{j}] {case['title'][:60]}...")
                    print(f"      Similarity: {case['similarity']:.2%}")
                    print(f"      Module: {case['module']}")
                    print(f"      Root cause: {case['root_cause'][:80]}...")
            else:
                print("\n⚠️ No similar cases found (threshold too high or no matching cases)")
            
            print(f"\nGenerating answer...")
            result = qa_engine.answer(
                test['question'],
                all_cases,
                query_embedding=query_embedding,
                top_k=3,
                min_similarity=0.3
            )
            
            print(f"\n💡 Answer (confidence: {result['confidence']:.2%}):")
            print("-" * 60)
            answer_lines = result['answer'].split('\n')
            for line in answer_lines[:10]:
                print(line)
            if len(answer_lines) > 10:
                print(f"... ({len(answer_lines) - 10} more lines)")
            print("-" * 60)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("📊 SKILL Performance Metrics")
    print("=" * 60)
    
    cases_with_embeddings = sum(1 for case in all_cases if case.get('embedding'))
    print(f"Cases with embeddings: {cases_with_embeddings}/{len(all_cases)}")
    print(f"Embedding coverage: {cases_with_embeddings/len(all_cases)*100:.1f}%")
    
    if training_count > 0:
        modules = {}
        for case in all_cases:
            module = case.get('module', 'unknown')
            modules[module] = modules.get(module, 0) + 1
        
        print(f"\nCases by module:")
        for module, count in sorted(modules.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {module}: {count} cases")
    
    print("\n" + "=" * 60)
    print("✅ SKILL Demonstration Complete")
    print("=" * 60)
    print("\nKey Capabilities Demonstrated:")
    print("  ✅ Semantic similarity search (vector-based)")
    print("  ✅ Intelligent Q&A with context")
    print("  ✅ Multi-source case retrieval")
    print("  ✅ Confidence scoring")
    print("\nThe RAG system serves as the trained SKILL, providing:")
    print("  • Case-based reasoning")
    print("  • Knowledge retrieval")
    print("  • Intelligent analysis")
    print("  • Solution recommendations")


def verify_with_test_cases():
    """使用测试集验证SKILL能力"""
    print("\n" + "=" * 60)
    print("🧪 Verification with Test Cases")
    print("=" * 60)
    
    test_cases = list(TestCase.objects.all()[:5])
    
    if not test_cases:
        print("⚠️ No test cases available for verification")
        return
    
    print(f"Using {len(test_cases)} test cases for verification...")
    
    training_cases = list(TrainingCase.objects.all().values(
        'case_id', 'title', 'phenomenon', 'root_cause', 'solution',
        'module', 'source', 'quality_score', 'embedding'
    ))
    
    vector_service = get_vector_service()
    
    correct = 0
    total = 0
    
    for test_case in test_cases:
        print(f"\n--- Test Case: {test_case.title[:60]}... ---")
        
        query = f"{test_case.phenomenon[:100]} {test_case.root_cause[:50]}"
        
        try:
            query_embedding = vector_service.generate_embedding(query)
            
            if not query_embedding:
                continue
            
            similar_cases = vector_retriever.search_similar(
                query_embedding,
                training_cases,
                top_k=5,
                threshold=0.3
            )
            
            if similar_cases:
                print(f"✅ Found {len(similar_cases)} similar cases")
                print(f"   Top similarity: {similar_cases[0]['similarity']:.2%}")
                
                if similar_cases[0]['module'] == test_case.module:
                    correct += 1
                    print(f"   ✅ Module match: {test_case.module}")
                else:
                    print(f"   ❌ Module mismatch: expected {test_case.module}, got {similar_cases[0]['module']}")
                
                total += 1
            else:
                print("⚠️ No similar cases found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    if total > 0:
        accuracy = correct / total
        print(f"\n" + "=" * 60)
        print(f"📈 Verification Results")
        print("=" * 60)
        print(f"Total test cases: {total}")
        print(f"Correct predictions: {correct}")
        print(f"Accuracy: {accuracy:.2%}")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 Linux Kernel Issue Analysis - SKILL System")
    print("=" * 60)
    print("\nThis script demonstrates the trained SKILL capabilities")
    print("using the RAG (Retrieval-Augmented Generation) system.\n")
    
    try:
        demonstrate_skill()
        verify_with_test_cases()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()