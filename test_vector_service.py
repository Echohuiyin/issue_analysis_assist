#!/usr/bin/env python3
"""Test script for VectorService"""

import sys
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')

from cases.acquisition.vector_service import VectorService, get_vector_service

def test_vector_service():
    print("Testing VectorService...")
    
    # Test with Ollama
    vector_service = get_vector_service(model="qwen:1.8b", llm_type="ollama")
    
    # Test embedding generation
    test_text = "Linux kernel panic due to null pointer dereference"
    print(f"Generating embedding for: {test_text}")
    
    try:
        embedding = vector_service.generate_embedding(test_text)
        print(f"✓ Embedding generated successfully")
        print(f"  Embedding dimension: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")
        return True
    except Exception as e:
        print(f"✗ Embedding generation failed: {e}")
        return False

if __name__ == "__main__":
    if test_vector_service():
        print("\n✓ All vector service tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Vector service tests failed")
        sys.exit(1)