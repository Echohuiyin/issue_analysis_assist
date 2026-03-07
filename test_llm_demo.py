#!/usr/bin/env python3
"""
LLM案例解析演示 - 直接展示解析效果
使用预设内容测试，展示好案例和坏案例的区别
"""

import sys
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')

from cases.acquisition.llm_parser import LLMParser


def demo_case_parsing():
    """演示案例解析效果"""
    
    print("=" * 80)
    print("LLM案例解析演示 - Qwen 1.8B (Ollama)")
    print("=" * 80)
    
    llm_parser = LLMParser(llm_type="ollama")
    
    # 测试案例1 - 高质量
    good_case = """Linux Kernel Panic Due to Null Pointer Dereference

I encountered a kernel panic on my Linux 5.4 system. The error message was:
BUG: unable to handle kernel NULL pointer dereference at address 0000000000000008
RIP: 0010:driver_init+0x12/0x30

This happened after loading a custom network driver. The driver was probing 
successfully but when trying to access dev->priv it crashed.

The root cause was that I forgot to allocate the private data structure in 
the probe function. Adding kmalloc fixed the issue:

struct driver_priv *priv = kmalloc(sizeof(*priv), GFP_KERNEL);
if (!priv)
    return -->ENOMEM;
devpriv = priv;
"""

    # 测试案例2 - 低质量
    bad_case = """Linux problem

My Linux system has a problem. It crashed. I don't know why.
Can someone help me?
"""

    print("\n\n" + "=" * 80)
    print("测试1: 高质量案例 (详细的问题描述)")
    print("=" * 80)
    print("\n原始内容:")
    print(good_case[:300] + "...")
    
    print("\n\n--- LLM解析结果 ---")
    result = llm_parser.parse(good_case, use_llm=True)
    
    if result:
        quality = llm_parser.check_quality(result)
        print(f"\n✓ 解析成功")
        print(f"  质量分数: {quality.get('quality_score')}/100")
        print(f"  高质量: {'是' if quality.get('is_high_quality') else '否'}")
        print(f"  有关键日志: {'是' if quality.get('has_key_logs') else '否'}")
        print(f"  有分析过程: {'是' if quality.get('has_analysis_process') else '否'}")
        
        print(f"\n提取的标题: {result.get('title')}")
        print(f"\n提取的现象: {result.get('phenomenon')}")
        print(f"\n提取的根因: {result.get('root_cause')}")
        print(f"\n提取的解决方案: {result.get('solution')}")
    else:
        print("✗ 解析失败")
    
    print("\n\n" + "=" * 80)
    print("测试2: 低质量案例 (信息不足)")
    print("=" * 80)
    print("\n原始内容:")
    print(bad_case)
    
    print("\n\n--- LLM解析结果 ---")
    result2 = llm_parser.parse(bad_case, use_llm=True)
    
    if result2:
        quality2 = llm_parser.check_quality(result2)
        print(f"\n✓ 解析成功")
        print(f"  质量分数: {quality2.get('quality_score')}/100")
        print(f"  高质量: {'是' if quality2.get('is_high_quality') else '否'}")
        print(f"  有关键日志: {'是' if quality2.get('has_key_logs') else '否'}")
        print(f"  有分析过程: {'是' if quality2.get('has_analysis_process') else '否'}")
        
        print(f"\n提取的标题: {result2.get('title')}")
        print(f"\n提取的现象: {result2.get('phenomenon')}")
        print(f"\n提取的根因: {result2.get('root_cause')}")
        print(f"\n提取的解决方案: {result2.get('solution')}")
        
        if quality2.get('issues'):
            print(f"\n质量问题: {', '.join(quality2.get('issues'))}")
    else:
        print("✗ 解析失败")


if __name__ == "__main__":
    demo_case_parsing()
