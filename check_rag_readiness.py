#!/usr/bin/env python3
"""
检查RAG系统就绪状态
验证训练案例的完整性和向量嵌入
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
import django
django.setup()

from cases.models import TrainingCase

def check_rag_readiness():
    print("=" * 70)
    print("RAG系统就绪状态检查")
    print("=" * 70)
    print()
    
    # 检查训练案例数量
    total_cases = TrainingCase.objects.count()
    print(f"1. 训练案例数量: {total_cases}")
    
    if total_cases == 0:
        print("   ❌ 没有训练案例，RAG系统无法工作")
        return False
    
    print(f"   ✅ 有足够的训练案例")
    print()
    
    # 检查向量嵌入
    cases_with_embedding = 0
    cases_without_embedding = 0
    
    for case in TrainingCase.objects.all():
        if case.embedding and len(case.embedding) > 0:
            cases_with_embedding += 1
        else:
            cases_without_embedding += 1
    
    print(f"2. 向量嵌入状态:")
    print(f"   有嵌入: {cases_with_embedding}个")
    print(f"   无嵌入: {cases_without_embedding}个")
    
    if cases_without_embedding > 0:
        print(f"   ⚠️ 有{cases_without_embedding}个案例缺少向量嵌入")
    else:
        print(f"   ✅ 所有案例都有向量嵌入")
    print()
    
    # 检查案例完整性
    complete_cases = 0
    incomplete_cases = 0
    
    for case in TrainingCase.objects.all():
        if (case.title and case.phenomenon and case.root_cause and case.solution):
            complete_cases += 1
        else:
            incomplete_cases += 1
    
    print(f"3. 案例完整性:")
    print(f"   完整案例: {complete_cases}个")
    print(f"   不完整案例: {incomplete_cases}个")
    
    if incomplete_cases > 0:
        print(f"   ⚠️ 有{incomplete_cases}个案例字段不完整")
    else:
        print(f"   ✅ 所有案例字段完整")
    print()
    
    # 检查模块分布
    modules = {}
    for case in TrainingCase.objects.all():
        modules[case.module] = modules.get(case.module, 0) + 1
    
    print(f"4. 模块分布:")
    for module, count in sorted(modules.items(), key=lambda x: x[1], reverse=True):
        print(f"   {module}: {count}个")
    print()
    
    # 检查来源分布
    sources = {}
    for case in TrainingCase.objects.all():
        sources[case.source] = sources.get(case.source, 0) + 1
    
    print(f"5. 来源分布:")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        print(f"   {source}: {count}个")
    print()
    
    # 总结
    print("=" * 70)
    print("RAG系统就绪状态总结:")
    print("=" * 70)
    
    ready = True
    issues = []
    
    if total_cases < 50:
        ready = False
        issues.append(f"训练案例数量不足（{total_cases} < 50）")
    
    if cases_without_embedding > 0:
        ready = False
        issues.append(f"{cases_without_embedding}个案例缺少向量嵌入")
    
    if incomplete_cases > 0:
        issues.append(f"{incomplete_cases}个案例字段不完整")
    
    if ready:
        print("✅ RAG系统已就绪，可以开始开发")
        print()
        print("建议的RAG系统功能:")
        print("1. 相似案例检索")
        print("2. 智能问答")
        print("3. 案例推荐")
        print("4. 问题分析")
    else:
        print("❌ RAG系统尚未就绪，需要解决以下问题:")
        for issue in issues:
            print(f"   - {issue}")
    
    print()
    return ready

if __name__ == "__main__":
    check_rag_readiness()