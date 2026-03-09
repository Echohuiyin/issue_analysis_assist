hu#!/usr/bin/env python3
"""
简单的LLM测试脚本
测试模型是否能正确返回JSON格式
"""
import json
from cases.acquisition.llm_integration import OllamaLLM

TEST_PROMPT = """请返回以下JSON格式：
{"test": "success", "value": 123}

只返回JSON，不要其他文字。"""

MODELS = ['qwen:0.5b', 'qwen:1.8b', 'qwen2.5:0.5b', 'qwen2.5:1.5b']

for model_name in MODELS:
    print(f"\n{'='*60}")
    print(f"测试模型: {model_name}")
    print(f"{'='*60}")
    
    try:
        llm = OllamaLLM(model=model_name)
        
        if not llm.is_available():
            print("✗ 模型不可用")
            continue
        
        print("发送提示词...")
        response = llm.generate(TEST_PROMPT, max_tokens=100)
        
        print(f"\n原始响应:")
        print(response)
        print(f"\n响应长度: {len(response)} 字符")
        
        try:
            parsed = json.loads(response)
            print(f"\n✓ JSON解析成功")
            print(f"解析结果: {parsed}")
        except json.JSONDecodeError as e:
            print(f"\n✗ JSON解析失败: {e}")
            print(f"错误位置: {e.pos}")
            
    except Exception as e:
        print(f"✗ 错误: {e}")

print(f"\n{'='*60}")
print("测试完成")
print(f"{'='*60}")