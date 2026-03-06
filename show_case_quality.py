#!/usr/bin/env python3
"""
展示高质量和低质量案例的具体内容

从StackOverflow和CSDN获取真实案例，展示质量验证结果
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kernel_cases.settings")
import django
django.setup()

from cases.acquisition.fetchers import StackOverflowFetcher, CSDNFetcher
from cases.acquisition.parsers import ForumParser, BlogParser
from cases.acquisition.validators import CaseValidator


def display_case(case_data, validation_result, source):
    """展示案例详情"""
    print("\n" + "=" * 80)
    print(f"来源: {source}")
    print("=" * 80)
    
    print(f"\n【标题】({len(case_data.get('title', ''))} 字符)")
    print(f"  {case_data.get('title', 'N/A')}")
    
    print(f"\n【现象】({len(case_data.get('phenomenon', ''))} 字符)")
    phenomenon = case_data.get('phenomenon', 'N/A')
    if len(phenomenon) > 200:
        print(f"  {phenomenon[:200]}...")
    else:
        print(f"  {phenomenon}")
    
    print(f"\n【根因】({len(case_data.get('root_cause', ''))} 字符)")
    root_cause = case_data.get('root_cause', 'N/A')
    if len(root_cause) > 200:
        print(f"  {root_cause[:200]}...")
    else:
        print(f"  {root_cause}")
    
    print(f"\n【解决方案】({len(case_data.get('solution', ''))} 字符)")
    solution = case_data.get('solution', 'N/A')
    if len(solution) > 200:
        print(f"  {solution[:200]}...")
    else:
        print(f"  {solution}")
    
    print(f"\n【质量验证结果】")
    print(f"  验证状态: {'✓ 通过' if validation_result['is_valid'] else '✗ 失败'}")
    print(f"  质量分数: {validation_result.get('quality_score', 0):.1f}/100")
    
    if 'quality_scores' in validation_result:
        print(f"  各字段分数:")
        for field, score in validation_result['quality_scores'].items():
            print(f"    - {field}: {score:.1f}")
    
    if validation_result.get('errors'):
        print(f"  错误 ({len(validation_result['errors'])} 个):")
        for error in validation_result['errors']:
            print(f"    ✗ {error}")
    
    if validation_result.get('warnings'):
        print(f"  警告 ({len(validation_result['warnings'])} 个):")
        for warning in validation_result['warnings']:
            print(f"    ⚠ {warning}")


def analyze_stackoverflow_cases():
    """分析StackOverflow案例"""
    print("\n" + "=" * 80)
    print("从 StackOverflow 获取案例并分析质量")
    print("=" * 80)
    
    fetcher = StackOverflowFetcher()
    parser = ForumParser()
    validator = CaseValidator()
    
    try:
        print("\n搜索关键词: kernel panic")
        urls = fetcher.search("kernel panic", count=2)
        
        if not urls:
            print("未找到相关案例")
            return []
        
        cases = []
        for i, url in enumerate(urls, 1):
            print(f"\n正在获取第 {i} 个案例...")
            content = fetcher.fetch(url)
            
            if not content:
                print("获取内容失败")
                continue
            
            case_data = parser.parse(content)
            if not case_data:
                print("解析内容失败")
                continue
            
            validation_result = validator.validate(case_data)
            cases.append((case_data, validation_result, f"StackOverflow #{i}"))
        
        return cases
    
    except Exception as e:
        print(f"错误: {e}")
        return []


def analyze_csdn_cases():
    """分析CSDN案例"""
    print("\n" + "=" * 80)
    print("从 CSDN 获取案例并分析质量")
    print("=" * 80)
    
    fetcher = CSDNFetcher()
    parser = BlogParser()
    validator = CaseValidator()
    
    try:
        print("\n搜索关键词: 内核 panic")
        urls = fetcher.search("内核 panic", count=2)
        
        if not urls:
            print("未找到相关案例")
            return []
        
        cases = []
        for i, url in enumerate(urls, 1):
            print(f"\n正在获取第 {i} 个案例...")
            content = fetcher.fetch(url)
            
            if not content:
                print("获取内容失败")
                continue
            
            case_data = parser.parse(content)
            if not case_data:
                print("解析内容失败")
                continue
            
            validation_result = validator.validate(case_data)
            cases.append((case_data, validation_result, f"CSDN #{i}"))
        
        return cases
    
    except Exception as e:
        print(f"错误: {e}")
        return []


def categorize_cases(all_cases):
    """将案例分类为高质量和低质量"""
    high_quality = []
    low_quality = []
    
    for case_data, validation_result, source in all_cases:
        quality_score = validation_result.get('quality_score', 0)
        
        if quality_score >= 70 and validation_result['is_valid']:
            high_quality.append((case_data, validation_result, source))
        else:
            low_quality.append((case_data, validation_result, source))
    
    return high_quality, low_quality


def main():
    """主函数"""
    print("Linux内核问题自动分析系统 - 案例质量展示")
    print("=" * 80)
    
    # 获取所有案例
    all_cases = []
    all_cases.extend(analyze_stackoverflow_cases())
    all_cases.extend(analyze_csdn_cases())
    
    if not all_cases:
        print("\n未获取到任何案例")
        return 1
    
    # 分类案例
    high_quality, low_quality = categorize_cases(all_cases)
    
    # 展示高质量案例
    if high_quality:
        print("\n\n" + "█" * 80)
        print("█" + " " * 30 + "高质量案例展示" + " " * 30 + "█")
        print("█" * 80)
        
        for case_data, validation_result, source in high_quality:
            display_case(case_data, validation_result, source)
    else:
        print("\n\n未找到高质量案例")
    
    # 展示低质量案例
    if low_quality:
        print("\n\n" + "█" * 80)
        print("█" + " " * 30 + "低质量案例展示" + " " * 30 + "█")
        print("█" * 80)
        
        for case_data, validation_result, source in low_quality:
            display_case(case_data, validation_result, source)
    else:
        print("\n\n未找到低质量案例")
    
    # 统计总结
    print("\n\n" + "=" * 80)
    print("统计总结")
    print("=" * 80)
    print(f"总案例数: {len(all_cases)}")
    print(f"高质量案例: {len(high_quality)} ({len(high_quality)/len(all_cases)*100:.1f}%)")
    print(f"低质量案例: {len(low_quality)} ({len(low_quality)/len(all_cases)*100:.1f}%)")
    
    if high_quality:
        avg_high_score = sum(v.get('quality_score', 0) for _, v, _ in high_quality) / len(high_quality)
        print(f"高质量案例平均分数: {avg_high_score:.1f}")
    
    if low_quality:
        avg_low_score = sum(v.get('quality_score', 0) for _, v, _ in low_quality) / len(low_quality)
        print(f"低质量案例平均分数: {avg_low_score:.1f}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())