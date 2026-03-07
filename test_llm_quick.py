#!/usr/bin/env python3
"""
Direct test of LLM parsing with short prompts
"""

import sys
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')

from cases.acquisition.llm_integration import OllamaLLM


def quick_test():
    """Quick test with short prompts"""
    
    print("=" * 80)
    print("LLM Parsing Quick Test - Qwen 1.8B")
    print("=" * 80)
    
    llm = OllamaLLM(model="qwen:1.8b")
    
    # Test 1 - High quality case
    print("\n\n=== Test 1: High Quality Case ===")
    prompt1 = """Extract kernel case info from this:

Title: Kernel panic - null pointer dereference in driver
Error: BUG: unable to handle kernel NULL pointer dereference
This happened after loading a custom driver. Root cause was missing kmalloc for private data.
Fix: Add kmalloc in probe function.

Extract as JSON with keys: title, phenomenon, root_cause, solution"""
    
    print("Prompt:", prompt1[:100], "...")
    try:
        response = llm.generate(prompt1, max_tokens=500)
        print("\n✓ Response:")
        print(response)
    except Exception as e:
        print(f"\n✗ Error: {e}")
    
    # Test 2 - Low quality case
    print("\n\n=== Test 2: Low Quality Case ===")
    prompt2 = """Extract kernel case info from:

My Linux has a problem. It crashed. Help me please.

Extract as JSON with keys: title, phenomenon, root_cause, solution"""
    
    print("Prompt:", prompt2[:100], "...")
    try:
        response = llm.generate(prompt2, max_tokens=500)
        print("\n✓ Response:")
        print(response)
    except Exception as e:
        print(f"\n✗ Error: {e}")
    
    # Test 3 - Medium quality
    print("\n\n=== Test 3: Medium Quality ===")
    prompt3 = """Extract kernel case info from:

Kernel driver loading failed. Checked logs, found error in init function.
Fixed by modifying the driver code.

Extract as JSON with keys: title, phenomenon, root_cause, solution"""
    
    print("Prompt:", prompt3[:100], "...")
    try:
        response = llm.generate(prompt3, max_tokens=500)
        print("\n✓ Response:")
        print(response)
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    quick_test()
