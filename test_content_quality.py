#!/usr/bin/env python3
"""
测试内容质量验证功能

演示如何验证解析的案例内容质量，包括：
1. 高质量案例验证
2. 低质量案例验证
3. Fallback内容检测
4. 质量评分系统
"""

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置 Django 环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kernel_cases.settings")
import django
django.setup()

from cases.acquisition.validators import CaseValidator


def test_high_quality_case():
    """测试高质量案例"""
    print("\n=== 测试高质量案例 ===")
    
    validator = CaseValidator()
    
    case_data = {
        'title': 'Linux kernel panic due to memory corruption in network driver',
        'phenomenon': 'System crashes with kernel panic error message showing memory fault in network driver module',
        'environment': 'Linux 5.10.0-10-amd64, x86_64',
        'root_cause': 'Analysis shows memory corruption caused by faulty network driver code that does not properly handle buffer allocation',
        'solution': 'Update the network driver to fix the memory corruption issue and apply the patch from vendor',
        'troubleshooting_steps': ['Check kernel logs', 'Analyze crash dump', 'Update driver']
    }
    
    result = validator.validate(case_data)
    
    print(f"验证结果: {'通过' if result['is_valid'] else '失败'}")
    print(f"质量分数: {result.get('quality_score', 0):.1f}")
    print(f"错误数量: {len(result.get('errors', []))}")
    print(f"警告数量: {len(result.get('warnings', []))}")
    
    if result.get('errors'):
        print("\n错误:")
        for error in result['errors']:
            print(f"  - {error}")
    
    if result.get('warnings'):
        print("\n警告:")
        for warning in result['warnings']:
            print(f"  - {warning}")
    
    return result['is_valid']


def test_low_quality_case():
    """测试低质量案例"""
    print("\n=== 测试低质量案例 ===")
    
    validator = CaseValidator()
    
    case_data = {
        'title': 'Short',
        'phenomenon': 'Some text',
        'environment': 'Linux',
        'root_cause': 'Some random text without proper analysis',
        'solution': 'Some random text without proper solution',
        'troubleshooting_steps': ['Step 1']
    }
    
    result = validator.validate(case_data)
    
    print(f"验证结果: {'通过' if result['is_valid'] else '失败'}")
    print(f"质量分数: {result.get('quality_score', 0):.1f}")
    print(f"错误数量: {len(result.get('errors', []))}")
    print(f"警告数量: {len(result.get('warnings', []))}")
    
    if result.get('errors'):
        print("\n错误:")
        for error in result['errors']:
            print(f"  - {error}")
    
    if result.get('warnings'):
        print("\n警告:")
        for warning in result['warnings']:
            print(f"  - {warning}")
    
    return not result['is_valid']  # 期望失败


def test_fallback_content():
    """测试Fallback内容检测"""
    print("\n=== 测试Fallback内容检测 ===")
    
    validator = CaseValidator()
    
    case_data = {
        'title': 'Linux kernel panic issue',
        'phenomenon': 'System crashes with kernel panic error',
        'environment': 'Linux 5.10.0',
        'root_cause': 'See article for details',
        'solution': 'See article for solution details',
        'troubleshooting_steps': ['Step 1']
    }
    
    result = validator.validate(case_data)
    
    print(f"验证结果: {'通过' if result['is_valid'] else '失败'}")
    print(f"质量分数: {result.get('quality_score', 0):.1f}")
    print(f"错误数量: {len(result.get('errors', []))}")
    print(f"警告数量: {len(result.get('warnings', []))}")
    
    if result.get('errors'):
        print("\n错误:")
        for error in result['errors']:
            print(f"  - {error}")
    
    # 检查是否检测到fallback内容
    has_fallback_error = any('fallback' in err.lower() for err in result.get('errors', []))
    print(f"\nFallback内容检测: {'成功' if has_fallback_error else '失败'}")
    
    return has_fallback_error


def test_quality_score_breakdown():
    """测试质量评分细分"""
    print("\n=== 测试质量评分细分 ===")
    
    validator = CaseValidator()
    
    case_data = {
        'title': 'Kernel memory leak in driver',
        'phenomenon': 'System shows memory leak symptoms',
        'environment': 'Linux 5.10.0',
        'root_cause': 'Driver code has memory leak bug',
        'solution': 'Fix the memory leak in driver code',
        'troubleshooting_steps': ['Step 1', 'Step 2']
    }
    
    result = validator.validate(case_data)
    
    print(f"验证结果: {'通过' if result['is_valid'] else '失败'}")
    print(f"总体质量分数: {result.get('quality_score', 0):.1f}")
    
    if 'quality_scores' in result:
        print("\n各字段质量分数:")
        for field, score in result['quality_scores'].items():
            print(f"  {field}: {score:.1f}")
    
    return result['is_valid']


def main():
    """主函数"""
    print("Linux内核问题自动分析系统 - 内容质量验证测试")
    print("=" * 60)
    
    tests = [
        ("高质量案例验证", test_high_quality_case),
        ("低质量案例验证", test_low_quality_case),
        ("Fallback内容检测", test_fallback_content),
        ("质量评分细分", test_quality_score_breakdown),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"测试失败: {e}")
            results.append((test_name, False))
    
    # 输出测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:20}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！内容质量验证功能正常工作！")
        return 0
    else:
        print("❌ 部分测试失败，请检查代码！")
        return 1


if __name__ == "__main__":
    sys.exit(main())