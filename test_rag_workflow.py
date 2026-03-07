#!/usr/bin/env python3
"""Test script for RAG workflow"""

import os
import sys
import uuid

# Add the project root to Python path
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kernel_cases.settings")
import django
django.setup()

from cases.models import KernelCase
from cases.acquisition.storage import CaseStorage
from cases.acquisition.vector_service import VectorService
from cases.analysis import SKILLStorage, IssueAnalyzer


def test_rag_workflow():
    """Test the complete RAG workflow"""
    print("=" * 80)
    print("Testing RAG Workflow")
    print("=" * 80)
    
    results = []
    
    # Step 1: Create a test case
    print("\n1. Creating test case...")
    test_case_data = {
        "title": "Linux kernel panic due to null pointer dereference",
        "phenomenon": "System crashes with kernel panic message showing null pointer dereference",
        "root_cause": "Null pointer dereference in driver code when accessing uninitialized device structure",
        "solution": "Add proper NULL pointer checks in the driver's probe function",
        "environment": "Linux 5.10.0-10-amd64 x86_64",
        "affected_components": "network driver",
        "severity": "High",
        "source": "test",
        "source_id": "test-001",
        "url": "http://example.com/test-case"
    }
    print("✓ Test case data prepared")
    results.append(True)
    
    # Step 2: Store the test case with embedding
    print("\n2. Storing test case with embedding...")
    storage = CaseStorage()
    try:
        result = storage.store(test_case_data)
        if result["success"]:
            print(f"✓ Test case stored successfully with ID: {result['case_id']}")
            test_case_id = result['case_id']
            results.append(True)
        else:
            print(f"✗ Failed to store test case: {result['message']}")
            results.append(False)
    except Exception as e:
        print(f"✗ Error storing test case: {e}")
        results.append(False)
    
    # Step 3: Verify embedding was generated and stored
    print("\n3. Verifying embedding...")
    try:
        case = KernelCase.objects.get(case_id=test_case_id)
        if case.embedding and len(case.embedding) > 0:
            print(f"✓ Embedding found with dimension: {len(case.embedding)}")
            results.append(True)
        else:
            print("✗ No embedding found for the test case")
            results.append(False)
    except Exception as e:
        print(f"✗ Error retrieving case: {e}")
        results.append(False)
    
    # Step 4: Test issue analysis with RAG
    print("\n4. Testing issue analysis with RAG...")
    try:
        skill_storage = SKILLStorage()
        analyzer = IssueAnalyzer(skill_storage)
        
        # Test with a similar issue
        issue_description = "Kernel panic with null pointer dereference in network driver"
        logs = "[12345.678901] BUG: unable to handle kernel NULL pointer dereference at 0000000000000008"
        
        result = analyzer.analyze_issue(issue_description, logs)
        
        print(f"✓ Issue analysis completed with confidence: {result['confidence_score']:.2f}")
        print(f"  Used {len(result['relevant_skills_used'])} skills")
        
        if result['similar_cases']:
            print(f"✓ Found {len(result['similar_cases'])} similar cases:")
            for i, similar_case in enumerate(result['similar_cases'], 1):
                case = similar_case['case']
                similarity = similar_case['similarity']
                print(f"    {i}. {case['title']} (Similarity: {similarity:.2f})")
            results.append(True)
        else:
            print("✗ No similar cases found (expected at least one)")
            results.append(False)
    except Exception as e:
        print(f"✗ Error during issue analysis: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    # Step 5: Clean up - delete the test case
    print("\n5. Cleaning up test data...")
    try:
        case = KernelCase.objects.get(case_id=test_case_id)
        case.delete()
        print("✓ Test case deleted successfully")
        results.append(True)
    except Exception as e:
        print(f"✗ Error cleaning up test data: {e}")
        results.append(False)
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All RAG workflow tests passed!")
        return True
    else:
        print("✗ Some RAG workflow tests failed")
        return False


if __name__ == "__main__":
    if test_rag_workflow():
        sys.exit(0)
    else:
        sys.exit(1)