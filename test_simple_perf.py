#!/usr/bin/env python3
"""
简单的性能对比测试
"""
import os
import sys
import time
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')

import django
django.setup()

from cases.models import RawCase
from cases.acquisition.llm_integration import OllamaLLM

MODELS = ['qwen:0.005b', 'qwen:1.8b', 'qwen2.5:0.5b', 'qwen2.5:1.5b']

print("获取测试案例...")
test_cases = list(RawCase.objects.filter(status='pending')[:1])

if not test_cases:
    print("没有待处理案例")
    sys.exit(0)

test_case = test_cases[0]
print(f"测试案例: {test_case.raw_title[:50]}")
print(f"内容长度: {len(test_case.raw_content)} 字符")
print()

for model_name in MODELS:
    print(f"{'='*60}")
    print(f"测试模型: {model_name}")
    print(f"{'='*60}")
    
    try:
        llm = OllamaLLM(model=model_name)
        
        if not llm.is_available():
            print("✗ 模型不可用")
            continue
        
        prompt = f"总结以下文本：{test_case.raw_content[:300]}"
        
        start = time.time()
        response = llm.generate(prompt, max_tokens=100)
        end = time.time()
        
        elapsed = end - start
        print(f"✓ 成功")
        print(f"  耗时: {elapsed:.2f}秒")
        print(f"  响应长度: {len(response)} 字符")
        print(f"  响应: {response[:100]}...")
        
    except Exception as e:
        print(f"✗ 失败: {e}")
    
    print()

print("测试完成")