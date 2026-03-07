#!/usr/bin/env python3
"""Test script for Ollama LLM integration"""

import sys
import json
import requests

OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "qwen:1.8b"


def test_ollama_connection():
    """Test if Ollama is running"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        if response.status_code == 200:
            print("✓ Ollama connection successful")
            models = response.json().get("models", [])
            print(f"  Available models: {[m['name'] for m in models]}")
            return True
    except Exception as e:
        print(f"✗ Ollama connection failed: {e}")
        return False


def test_llm_basic():
    """Test basic LLM generation"""
    prompt = "What is Linux kernel panic? Answer in 2 sentences."
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 100
        }
    }
    
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Basic LLM generation successful")
            print(f"  Response: {result.get('response', '')[:100]}...")
            print(f"  Duration: {result.get('total_duration', 0) / 1e9:.2f}s")
            return True
        else:
            print(f"✗ LLM generation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ LLM generation error: {e}")
        return False


def test_kernel_case_extraction():
    """Test LLM with kernel case extraction"""
    prompt = """Extract structured information from this kernel issue:

Title: Linux kernel panic - null pointer dereference in driver code
The system crashed with "BUG: unable to handle kernel NULL pointer dereference" 
at address 0000000000000008. This happened after loading a custom network driver.
The driver was recently modified to add new functionality.

Key logs from dmesg:
[12345.678901] BUG: unable to handle kernel NULL pointer dereference
[12345.678902] IP: [<ffffffff81234567>] driver_init+0x12/0x30

Extract in JSON format:
{
    "phenomenon": "what happened",
    "root_cause": "why it happened", 
    "solution": "how to fix it"
}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 500
        }
    }
    
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Kernel case extraction successful")
            print(f"  Response: {result.get('response', '')[:200]}...")
            return True
        else:
            print(f"✗ Kernel case extraction failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Kernel case extraction error: {e}")
        return False


def test_with_project_llm():
    """Test using project's LLM integration"""
    try:
        # Import the project's LLM integration
        sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')
        
        # Test OllamaLLM directly
        from cases.acquisition.llm_integration import OllamaLLM
        
        llm = OllamaLLM(model=MODEL_NAME)
        
        response = llm.generate("What is kernel OOM? Answer in one sentence.")
        print("✓ Project LLM integration works")
        print(f"  Response: {response[:100]}...")
        return True
    except Exception as e:
        print(f"✗ Project LLM integration failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Ollama LLM Integration")
    print("=" * 60)
    
    results = []
    
    print("\n1. Testing Ollama connection...")
    results.append(test_ollama_connection())
    
    print("\n2. Testing basic LLM generation...")
    results.append(test_llm_basic())
    
    print("\n3. Testing kernel case extraction...")
    results.append(test_kernel_case_extraction())
    
    print("\n4. Testing project LLM integration...")
    results.append(test_with_project_llm())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)
