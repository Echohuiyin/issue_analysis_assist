#!/usr/bin/env python3
"""
生成训练案例详细摘要
展示生成的案例内容和质量
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
import django
django.setup()

from cases.models import TrainingCase

def generate_summary():
    print("=" * 70)
    print("训练案例详细摘要")
    print("=" * 70)
    print()
    
    training_cases = TrainingCase.objects.all().order_by('-quality_score')
    total = training_cases.count()
    
    print(f"训练案例总数: {total}")
    print()
    
    # 展示前10个高质量案例
    print("=" * 70)
    print("高质量案例示例（前10个）:")
    print("=" * 70)
    
    for i, case in enumerate(training_cases[:10], 1):
        print(f"\n【案例 {i}】{case.case_id}")
        print(f"标题: {case.title}")
        print(f"来源: {case.source}")
        print(f"质量分数: {case.quality_score:.2f}")
        print(f"模块: {case.module}")
        print(f"严重程度: {case.severity}")
        print(f"\n问题现象:")
        print(f"  {case.phenomenon[:200]}...")
        print(f"\n关键日志:")
        print(f"  {case.key_logs[:150] if case.key_logs else '无'}...")
        print(f"\n根本原因:")
        print(f"  {case.root_cause[:150]}...")
        print(f"\n解决方案:")
        print(f"  {case.solution[:150]}...")
        print("-" * 70)
    
    # 统计信息
    print("\n" + "=" * 70)
    print("统计信息:")
    print("=" * 70)
    
    # 按模块统计
    modules = {}
    for case in training_cases:
        modules[case.module] = modules.get(case.module, 0) + 1
    
    print("\n按模块分布:")
    for module, count in sorted(modules.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total * 100)
        print(f"  {module:20s}: {count:3d} ({percentage:5.1f}%)")
    
    # 按严重程度统计
    severities = {}
    for case in training_cases:
        severities[case.severity] = severities.get(case.severity, 0) + 1
    
    print("\n按严重程度分布:")
    for severity, count in sorted(severities.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total * 100)
        print(f"  {severity:20s}: {count:3d} ({percentage:5.1f}%)")
    
    # 质量分数统计
    print("\n质量分数统计:")
    scores = [case.quality_score for case in training_cases]
    print(f"  最高分: {max(scores):.2f}")
    print(f"  最低分: {min(scores):.2f}")
    print(f"  平均分: {sum(scores)/len(scores):.2f}")
    
    # 内核版本统计
    versions = {}
    for case in training_cases:
        if case.kernel_version:
            versions[case.kernel_version] = versions.get(case.kernel_version, 0) + 1
    
    if versions:
        print("\n内核版本分布（前5个）:")
        for version, count in sorted(versions.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {version:20s}: {count:3d}")

if __name__ == "__main__":
    generate_summary()