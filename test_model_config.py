#!/usr/bin/env python3
"""
测试模型配置是否正确更新
"""
import os
import sys

# 设置环境变量
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')

# 导入必要的模块
from cases.acquisition.llm_integration import OllamaLLM, get_llm, llm_instance

# 清除单例实例
llm_instance = None

# 测试1: 直接创建OllamaLLM实例
print("测试1: 直接创建OllamaLLM实例")
llm1 = OllamaLLM()
print(f"  模型名称: {llm1.model}")
print(f"  服务可用: {llm1.is_available()}")
print()

# 测试2: 通过get_llm获取实例
print("测试2: 通过get_llm获取实例（带model参数）")
llm2 = get_llm("ollama", model="qwen2.5:0.5b")
print(f"  模型名称: {llm2.model}")
print(f"  服务可用: {llm2.is_available()}")
print()

# 测试3: 通过get_llm获取默认实例
llm_instance = None  # 重置单例
print("测试3: 通过get_llm获取默认实例")
llm3 = get_llm("ollama")
print(f"  模型名称: {llm3.model}")
print(f"  服务可用: {llm3.is_available()}")
print()

# 测试4: 测试LLMParser
from cases.acquisition.llm_parser import LLMParser
print("测试4: 测试LLMParser")
parser = LLMParser(llm_type="ollama", model="qwen2.5:0.5b")
print(f"  LLM模型: {parser.llm.model}")
print()

# 测试5: 测试RawCaseProcessor
from process_raw_cases import RawCaseProcessor
print("测试5: 测试RawCaseProcessor")
processor = RawCaseProcessor(llm_type="ollama", model="qwen2.5:0.5b")
print(f"  LLM模型: {processor.llm_parser.llm.model}")
print()

print("测试完成！")