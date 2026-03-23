#!/usr/bin/env python3
"""
生成详细的案例处理报告
"""
import os
import sys
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
import django
django.setup()

from cases.models import RawCase, TrainingCase, TestCase

def generate_report():
    report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("=" * 70)
    print(f"案例处理详细报告 - {report_time}")
    print("=" * 70)
    print()
    
    # RawCase统计
    print("1. RawCase原始案例统计")
    print("-" * 70)
    total_raw = RawCase.objects.count()
    print(f"   总数: {total_raw}")
    
    status_counts = {}
    for status in ['pending', 'processing', 'processed', 'low_quality', 'failed']:
        count = RawCase.objects.filter(status=status).count()
        status_counts[status] = count
        percentage = (count / total_raw * 100) if total_raw > 0 else 0
        print(f"   {status:15s}: {count:4d} ({percentage:5.1f}%)")
    
    print()
    
    # TrainingCase统计
    print("2. TrainingCase训练案例统计")
    print("-" * 70)
    total_training = TrainingCase.objects.count()
    print(f"   总数: {total_training}")
    
    if total_training > 0:
        # 按来源统计
        sources = {}
        for tc in TrainingCase.objects.all():
            sources[tc.source] = sources.get(tc.source, 0) + 1
        
        print("   按来源分布:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_training * 100)
            print(f"     {source:15s}: {count:4d} ({percentage:5.1f}%)")
        
        # 质量分数分布
        print("\n   质量分数分布:")
        high_quality = TrainingCase.objects.filter(quality_score__gte=70).count()
        medium_quality = TrainingCase.objects.filter(quality_score__gte=50, quality_score__lt=70).count()
        low_quality = TrainingCase.objects.filter(quality_score__lt=50).count()
        
        print(f"     高质量(≥70): {high_quality}")
        print(f"     中等质量(50-70): {medium_quality}")
        print(f"     低质量(<50): {low_quality}")
        
        # 平均质量分数
        avg_score = sum(tc.quality_score for tc in TrainingCase.objects.all()) / total_training
        print(f"\n   平均质量分数: {avg_score:.2f}")
    
    print()
    
    # TestCase统计
    print("3. TestCase测试案例统计")
    print("-" * 70)
    total_test = TestCase.objects.count()
    print(f"   总数: {total_test}")
    
    if total_test > 0:
        avg_score = sum(tc.quality_score for tc in TestCase.objects.all()) / total_test
        print(f"   平均质量分数: {avg_score:.2f}")
    
    print()
    
    # 处理效率分析
    print("4. 处理效率分析")
    print("-" * 70)
    
    processed_count = status_counts.get('processed', 0)
    low_quality_count = status_counts.get('low_quality', 0)
    failed_count = status_counts.get('failed', 0)
    
    total_processed = processed_count + low_quality_count + failed_count
    
    if total_processed > 0:
        success_rate = (processed_count / total_processed * 100)
        low_quality_rate = (low_quality_count / total_processed * 100)
        failure_rate = (failed_count / total_processed * 100)
        
        print(f"   已处理总数: {total_processed}")
        print(f"   成功率: {success_rate:.1f}% ({processed_count}/{total_processed})")
        print(f"   低质量率: {low_quality_rate:.1f}% ({low_quality_count}/{total_processed})")
        print(f"   失败率: {failure_rate:.1f}% ({failed_count}/{total_processed})")
        
        # 训练案例转化率
        if total_processed > 0:
            conversion_rate = (total_training / total_processed * 100)
            print(f"\n   训练案例转化率: {conversion_rate:.1f}% ({total_training}/{total_processed})")
    
    print()
    
    # 目标进度
    print("5. 目标进度")
    print("-" * 70)
    target_cases = 1000
    current_cases = total_training + total_test
    progress = (current_cases / target_cases * 100) if target_cases > 0 else 0
    
    print(f"   目标案例数: {target_cases}")
    print(f"   当前案例数: {current_cases}")
    print(f"   完成进度: {progress:.1f}%")
    print(f"   距离目标: {max(0, target_cases - current_cases)}")
    
    print()
    print("=" * 70)

if __name__ == "__main__":
    generate_report()