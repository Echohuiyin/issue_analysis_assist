#!/usr/bin/env python3
"""
深入分析失败案例的原始内容
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
import django
django.setup()

from cases.models import RawCase

def analyze_failed_cases_content():
    print("=" * 70)
    print("失败案例原始内容分析")
    print("=" * 70)
    print()
    
    failed_cases = RawCase.objects.filter(status='failed')[:10]
    
    for i, case in enumerate(failed_cases, 1):
        print(f"\n案例 {i}: ID={case.raw_id}")
        print(f"来源: {case.source}")
        print(f"标题: {case.raw_title[:80]}")
        print(f"URL: {case.url}")
        print(f"错误: {case.process_error}")
        print(f"\n原始内容长度: {len(case.raw_content)} 字符")
        print(f"原始内容预览 (前500字符):")
        print("-" * 70)
        print(case.raw_content[:500])
        print("-" * 70)
        print()

if __name__ == "__main__":
    analyze_failed_cases_content()