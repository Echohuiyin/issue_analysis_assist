#!/usr/bin/env python3
"""
检查案例统计信息
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

print("=== 原始案例统计 ===")
print(f"总数: {RawCase.objects.count()}")
print(f"待处理: {RawCase.objects.filter(status='pending').count()}")
print(f"处理中: {RawCase.objects.filter(status='processing').count()}")
print(f"已处理: {RawCase.objects.filter(status='processed').count()}")
print(f"低质量: {RawCase.objects.filter(status='low_quality').count()}")
print(f"失败: {RawCase.objects.filter(status='failed').count()}")
print()