@#!/usr/bin/env python3
"""Simple test for Ollama connectivity"""

import requests
import time

OLLAMA_URL = "http://localhost:11434/api/generate"

def test_simple_ollama():
    print("Testing basic Ollama connectivity...")
    
    payload = {
        "model": "qwen:1.8b",
        "prompt": "What is 1+1?",
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 20
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Ollama response received in {end_time - start_time:.2f} seconds")
            print(f"Response: {result.get('response', '')}")
            return True
        else:
            print(f"✗ Ollama returned status code: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("✗ Request timed out")
        print("The Ollama server might be overloaded or the model is taking too long to respond")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    test_simple_ollama()