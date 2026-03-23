#!/usr/bin/env python3
"""
案例收集进度报告
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

print("\n" + "=" * 70)
print(" " * 20 + "案例收集进度报告")
print("=" * 70)
print()

# 统计数据
total_cases = RawCase.objects.count()
pending = RawCase.objects.filter(status='pending').count()
processed = RawCase.objects.filter(status='processed').count()
low_quality = RawCase.objects.filter(status='low_quality').count()
failed = RawCase.objects.filter(status='failed').count()

# 按来源统计
stackoverflow = RawCase.objects.filter(source='stackoverflow').count()
csdn = RawCase.objects.filter(source='csdn').count()
zhihu = RawCase.objects.filter(source='zhihu').count()
juejin = RawCase.objects.filter(source='juejin').count()
other = RawCase.objects.filter(source='other').count()

print("1. 总体统计")
print("-" * 70)
print(f"   总案例数: {total_cases}")
print(f"   待处理: {pending}")
print(f"   已处理: {processed}")
print(f"   低质量: {low_quality}")
print(f"   失败: {failed}")
print()

print("2. 按来源统计")
print("-" * 70)
print(f"   StackOverflow: {stackoverflow}")
print(f"   CSDN: {csdn}")
print(f"   知乎: {zhihu}")
print(f"   掘金: {juejin}")
print(f"   其他: {other}")
print()

print("3. 质量改进效果")
print("-" * 70)
if total_cases > 0:
    success_rate = (processed / total_cases * 100)
    quality_rate = ((processed + low_quality) / total_cases * 100)
    print(f"   成功处理率: {success_rate:.1f}%")
    print(f"   有效处理率: {quality_rate:.1f}%")
    print(f"   真实案例占比: {(stackoverflow + csdn + zhihu + juejin) / total_cases * 100:.1f}%")
print()

print("4. 目标进度")
print("-" * 70)
target = 1000
progress = (total_cases / target * 100) if target > 0 else 0
print(f"   目标: {target} 个案例")
print(f"   当前进度: {progress:.1f}%")
print(f"   距离目标: {max(0, target - total_cases)} 个案例")
print()

print("=" * 70)
print()