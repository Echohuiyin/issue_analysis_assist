#!/usr/bin/env python3
"""
重新处理低质量案例
使用降低后的质量阈值（50分）
"""
import os
import sys

# 设置环境变量
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')

# 导入必要的模块
import django
django.setup()

from cases.models import RawCase
from process_raw_cases import RawCaseProcessor

def main():
    print("=" * 70)
    print("重新处理低质量案例 - 使用新阈值（50分）")
    print("=" * 70)
    print()
    
    # 获取低质量案例数量
    low_quality_count = RawCase.objects.filter(status='low_quality').count()
    print(f"低质量案例数量: {low_quality_count}")
    print()
    
    if low_quality_count == 0:
        print("✓ 没有低质量案例需要重新处理")
        return
    
    # 将低质量案例状态改回pending
    print("将低质量案例状态改回pending...")
    updated = RawCase.objects.filter(status='low_quality').update(status='pending')
    print(f"✓ 已更新 {updated} 个案例状态")
    print()
    
    # 初始化处理器
    processor = RawCaseProcessor(llm_type='ollama', model='qwen2.5:0.5b')
    
    # 处理所有pending案例
    print("开始重新处理案例...")
    print()
    
    processor.process_all(batch_size=20, delay=1.0)

if __name__ == "__main__":
    main()