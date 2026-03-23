#!/usr/bin/env python3
"""
分析失败案例
找出导致处理失败的具体原因
"""
import os
import sys
from collections import Counter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
import django
django.setup()

from cases.models import RawCase

def analyze_failed_cases():
    print("=" * 70)
    print("失败案例分析")
    print("=" * 70)
    print()
    
    failed_cases = RawCase.objects.filter(status='failed')
    total = failed_cases.count()
    print(f"失败案例总数: {total}")
    print()
    
    if total == 0:
        print("没有失败案例")
        return
    
    # 分析错误类型
    error_types = Counter()
    error_examples = {}
    
    for case in failed_cases:
        error_msg = case.process_error or "Unknown error"
        
        # 分类错误类型
        if 'JSON' in error_msg or 'json' in error_msg:
            error_type = 'JSON解析错误'
        elif 'timeout' in error_msg.lower():
            error_type = '超时错误'
        elif 'connection' in error_msg.lower():
            error_type = '连接错误'
        elif 'empty' in error_msg.lower() or 'None' in error_msg:
            error_type = '空结果错误'
        elif 'validation' in error_msg.lower():
            error_type = '验证错误'
        else:
            error_type = '其他错误'
        
        error_types[error_type] += 1
        
        # 保存示例
        if error_type not in error_examples:
            error_examples[error_type] = {
                'case_id': case.raw_id,
                'title': case.raw_title[:80],
                'error': error_msg[:200]
            }
    
    # 打印错误类型统计
    print("错误类型分布:")
    print("-" * 70)
    for error_type, count in error_types.most_common():
        percentage = (count / total * 100)
        bar = '█' * int(percentage / 2)
        print(f"{error_type:15s}: {count:3d} ({percentage:5.1f}%) {bar}")
    print()
    
    # 打印错误示例
    print("=" * 70)
    print("错误示例:")
    print("=" * 70)
    for error_type, example in error_examples.items():
        print(f"\n【{error_type}】")
        print(f"案例ID: {example['case_id']}")
        print(f"标题: {example['title']}")
        print(f"错误信息: {example['error']}")
        print("-" * 70)

if __name__ == "__main__":
    analyze_failed_cases()