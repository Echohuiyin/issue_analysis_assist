#!/usr/bin/env python3
"""
测试基于LLM的智能解析器

展示：
1. 使用LLM解析案例内容
2. 新的质量评估标准
3. 高质量案例vs低质量案例的对比
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kernel_cases.settings")
import django
django.setup()

from cases.acquisition.fetchers import StackOverflowFetcher, CSDNFetcher
from cases.acquisition.llm_parser import LLMParser
from cases.acquisition.validators import CaseValidator


def display_case(case_data, validation_result, source, parser_type):
    """展示案例详情"""
    print("\n" + "=" * 80)
    print(f"来源: {source}")
    print(f"解析器: {parser_type}")
    print("=" * 80)
    
    print(f"\n【标题】({len(case_data.get('title', ''))} 字符)")
    print(f"  {case_data.get('title', 'N/A')}")
    
    print(f"\n【现象】({len(case_data.get('phenomenon', ''))} 字符)")
    phenomenon = case_data.get('phenomenon', 'N/A')
    if len(phenomenon) > 300:
        print(f"  {phenomenon[:300]}...")
    else:
        print(f"  {phenomenon}")
    
    # 新增字段：关键日志
    if case_data.get('key_logs'):
        print(f"\n【关键日志】({len(case_data.get('key_logs', ''))} 字符)")
        key_logs = case_data.get('key_logs', '')
        if len(key_logs) > 200:
            print(f"  {key_logs[:200]}...")
        else:
            print(f"  {key_logs}")
    
    # 新增字段：分析过程
    if case_data.get('analysis_process'):
        print(f"\n【分析过程】({len(case_data.get('analysis_process', ''))} 字符)")
        analysis = case_data.get('analysis_process', '')
        if len(analysis) > 200:
            print(f"  {analysis[:200]}...")
        else:
            print(f"  {analysis}")
    
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
    print(f"  高质量案例: {'✓ 是' if validation_result.get('is_high_quality', False) else '✗ 否'}")
    print(f"  质量分数: {validation_result.get('quality_score', 0):.1f}/100")
    
    if 'quality_scores' in validation_result:
        print(f"  各字段分数:")
        for field, score in validation_result['quality_scores'].items():
            status = "✓" if score >= 60 else "✗"
            print(f"    {status} {field}: {score:.1f}")
    
    if validation_result.get('errors'):
        print(f"  错误 ({len(validation_result['errors'])} 个):")
        for error in validation_result['errors']:
            print(f"    ✗ {error}")
    
    if validation_result.get('warnings'):
        print(f"  警告 ({len(validation_result['warnings'])} 个):")
        for warning in validation_result['warnings']:
            print(f"    ⚠ {warning}")


def test_llm_parser():
    """测试LLM解析器"""
    print("\n" + "=" * 80)
    print("测试基于LLM的智能解析器")
    print("=" * 80)
    
    # 检查LLM是否可用
    llm_parser = LLMParser(llm_type="auto")
    
    if llm_parser.llm.is_available():
        print(f"\n✓ LLM已配置: {llm_parser.llm.__class__.__name__}")
    else:
        print("\n✗ LLM未配置，将使用Mock模式或传统规则方法")
        print("提示: 设置环境变量 OPENAI_API_KEY 或 DEEPSEEK_API_KEY 以启用LLM")
    
    # 测试案例
    test_cases = [
        {
            "name": "高质量案例示例",
            "content": """
Linux内核panic问题分析

问题现象：
系统运行一段时间后出现kernel panic，错误信息如下：
[12345.678901] BUG: unable to handle kernel NULL pointer dereference at 0000000000000008
[12345.678902] IP: [<ffffffffa0123456>] driver_probe+0x56/0x100
[12345.678903] PGD 0 
[12345.678904] Oops: 0002 [#1] SMP 

环境信息：
Linux version 5.10.0-10-amd64 (debian-kernel@lists.debian.org)
x86_64 GNU/Linux

问题分析过程：
1. 首先检查内核日志，发现空指针解引用错误
2. 分析调用栈，定位到driver_probe函数
3. 使用gdb调试内核模块，发现指针未初始化
4. 检查驱动代码，发现probe函数中缺少NULL检查

根本原因：
驱动程序在probe函数中没有对device结构体指针进行NULL检查，直接访问了device->private_data成员，导致空指针解引用。

解决方案：
在driver_probe函数中添加NULL指针检查：
if (!device || !device->private_data) {
    dev_err(dev, "Invalid device pointer\n");
    return -EINVAL;
}

预防措施：
1. 所有指针使用前必须进行NULL检查
2. 使用静态分析工具检查代码
3. 添加单元测试覆盖异常路径
""",
            "expected_quality": "high"
        },
        {
            "name": "低质量案例示例",
            "content": """
Linux内核问题

问题描述：
系统有问题。

解决方案：
见文章详情。
""",
            "expected_quality": "low"
        }
    ]
    
    validator = CaseValidator()
    
    for test_case in test_cases:
        print(f"\n\n{'='*80}")
        print(f"测试案例: {test_case['name']}")
        print(f"预期质量: {test_case['expected_quality']}")
        print('='*80)
        
        # 使用LLM解析
        case_data = llm_parser.parse(test_case['content'], use_llm=True)
        
        if not case_data:
            print("解析失败")
            continue
        
        # 验证质量
        validation_result = validator.validate(case_data)
        
        # 展示结果
        display_case(case_data, validation_result, "测试案例", "LLM Parser")
        
        # 判断是否符合预期
        is_high_quality = validation_result.get('is_high_quality', False)
        expected_high = test_case['expected_quality'] == 'high'
        
        if is_high_quality == expected_high:
            print(f"\n✓ 质量评估符合预期")
        else:
            print(f"\n✗ 质量评估不符合预期")


def test_real_cases():
    """测试真实案例"""
    print("\n\n" + "=" * 80)
    print("从真实数据源获取案例并使用LLM解析")
    print("=" * 80)
    
    llm_parser = LLMParser(llm_type="auto")
    validator = CaseValidator()
    
    # 从StackOverflow获取一个案例
    try:
        print("\n从StackOverflow获取案例...")
        fetcher = StackOverflowFetcher()
        urls = fetcher.search("kernel panic", count=1)
        
        if urls:
            content = fetcher.fetch(urls[0])
            if content:
                # 使用LLM解析
                case_data = llm_parser.parse(content, use_llm=True)
                if case_data:
                    validation_result = validator.validate(case_data)
                    display_case(case_data, validation_result, "StackOverflow", "LLM Parser")
    except Exception as e:
        print(f"StackOverflow测试失败: {e}")
    
    # 从CSDN获取一个案例
    try:
        print("\n\n从CSDN获取案例...")
        fetcher = CSDNFetcher()
        urls = fetcher.search("内核 panic", count=1)
        
        if urls:
            content = fetcher.fetch(urls[0])
            if content:
                # 使用LLM解析
                case_data = llm_parser.parse(content, use_llm=True)
                if case_data:
                    validation_result = validator.validate(case_data)
                    display_case(case_data, validation_result, "CSDN", "LLM Parser")
    except Exception as e:
        print(f"CSDN测试失败: {e}")


def main():
    """主函数"""
    print("Linux内核问题自动分析系统 - LLM智能解析器测试")
    print("=" * 80)
    
    # 测试LLM解析器
    test_llm_parser()
    
    # 测试真实案例
    test_real_cases()
    
    print("\n\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
    
    print("\n使用说明:")
    print("1. 设置环境变量启用LLM:")
    print("   export OPENAI_API_KEY='your-key'")
    print("   或")
    print("   export DEEPSEEK_API_KEY='your-key'")
    print("\n2. 新的质量评估标准:")
    print("   - 问题现象描述清晰准确（包含具体症状、错误信息）")
    print("   - 有描述问题现象的关键日志提供")
    print("   - 提供了问题分析思路或较为详细的问题分析过程")
    print("\n3. LLM解析器优势:")
    print("   - 全文理解，而非简单规则匹配")
    print("   - 准确提取关键日志、分析过程等结构化信息")
    print("   - 自动评估内容质量，过滤低质量案例")


if __name__ == "__main__":
    main()