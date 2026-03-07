#!/usr/bin/env python3
"""
简化版 - 案例质量过滤测试
"""

import sys
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')

from cases.acquisition.llm_parser import LLMParser


QUALITY_THRESHOLD = 70

print("=" * 80)
print("案例质量过滤演示")
print(f"质量阈值: {QUALITY_THRESHOLD}分")
print("=" * 80)

llm_parser = LLMParser(llm_type="ollama")

# 案例1 - 高质量
print("\n\n=== 案例1: 高质量 ===")
content1 = """
Linux Kernel Panic - NULL Pointer Dereference

Problem: BUG: unable to handle kernel NULL pointer dereference at address 0000000000000008

Root Cause: Driver probe function did not allocate private data before using dev->priv pointer

Solution: Add kmalloc in probe function:
struct driver_priv *priv = kmalloc(sizeof(*priv), GFP_KERNEL);
"""

print("解析中...")
r1 = llm_parser.parse(content1, use_llm=True)
if r1:
    q1 = llm_parser.check_quality(r1)
    print(f"质量分数: {q1.get('quality_score')}/100")
    print(f"标题: {r1.get('title')}")
    print(f"根因: {r1.get('root_cause')[:80]}...")
    if q1.get('quality_score') >= QUALITY_THRESHOLD:
        print("✓ 会被存储")
    else:
        print("✗ 会被丢弃")

# 案例2 - 低质量
print("\n\n=== 案例2: 低质量 ===")
content2 = """
Linux problem

My Linux doesn't work. Help!
"""

print("解析中...")
r2 = llm_parser.parse(content2, use_llm=True)
if r2:
    q2 = llm_parser.check_quality(r2)
    print(f"质量分数: {q2.get('quality_score')}/100")
    print(f"标题: {r2.get('title')}")
    print(f"根因: {r2.get('root_cause')}")
    if q2.get('quality_score') >= QUALITY_THRESHOLD:
        print("✓ 会被存储")
    else:
        print("✗ 会被丢弃")

print("\n\n完成!")
