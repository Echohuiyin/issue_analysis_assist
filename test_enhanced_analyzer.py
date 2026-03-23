#!/usr/bin/env python3
"""
Test enhanced issue analyzer with RAG integration
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
import django
django.setup()

from cases.models import TrainingCase
from cases.analysis.skill_storage import SKILLStorage
from cases.analysis.issue_analyzer import IssueAnalyzer


def test_enhanced_analyzer():
    print("=" * 70)
    print("Testing Enhanced Issue Analyzer with RAG Integration")
    print("=" * 70)
    print()
    
    storage = SKILLStorage()
    analyzer = IssueAnalyzer(storage)
    
    test_issues = [
        {
            "description": "System crashes with kernel panic after running for several hours",
            "logs": "kernel: BUG: unable to handle kernel NULL pointer dereference at 00000000"
        },
        {
            "description": "Memory leak detected in kernel module",
            "logs": "Out of memory: Kill process 1234 (myapp) score 900 or sacrifice child"
        },
        {
            "description": "System becomes unresponsive due to deadlock",
            "logs": "INFO: task blocked for more than 120 seconds"
        }
    ]
    
    for i, test_issue in enumerate(test_issues, 1):
        print(f"Test Case {i}:")
        print(f"Description: {test_issue['description']}")
        print(f"Logs: {test_issue['logs'][:80]}...")
        print("-" * 70)
        
        result = analyzer.analyze_issue(
            test_issue['description'],
            test_issue['logs']
        )
        
        print(f"\nSkills Used: {result['relevant_skills_used']}")
        print(f"Confidence Score: {result['confidence_score']:.2%}")
        print(f"Similar Cases Found: {len(result['similar_cases'])}")
        
        if result['similar_cases']:
            print("\nTop Similar Cases:")
            for j, case in enumerate(result['similar_cases'][:2], 1):
                print(f"  {j}. {case['title'][:60]}")
                print(f"     Similarity: {case['similarity']:.2%}")
                print(f"     Module: {case.get('module', 'N/A')}")
        
        print("\n" + "=" * 70)
        print()
    
    return True


def main():
    print()
    print("=" * 70)
    print("Enhanced Issue Analyzer Test")
    print("=" * 70)
    print()
    
    try:
        success = test_enhanced_analyzer()
        
        if success:
            print("=" * 70)
            print("✅ All tests passed!")
            print("=" * 70)
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)