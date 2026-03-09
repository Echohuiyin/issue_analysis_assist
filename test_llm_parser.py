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
    print(f"  验证状态: {'[OK] 通过' if validation_result['is_valid'] else '[FAIL] 失败'}")
    print(f"  高质量案例: {'[OK] 是' if validation_result.get('is_high_quality', False) else '[FAIL] 否'}")
    print(f"  质量分数: {validation_result.get('quality_score', 0):.1f}/100")
    
    if 'quality_scores' in validation_result:
        print(f"  各字段分数:")
        for field, score in validation_result['quality_scores'].items():
            status = "[OK]" if score >= 60 else "[FAIL]"
            print(f"    {status} {field}: {score:.1f}")
    
    if validation_result.get('errors'):
        print(f"  错误 ({len(validation_result['errors'])} 个):")
        for error in validation_result['errors']:
            print(f"    [FAIL] {error}")
    
    if validation_result.get('warnings'):
        print(f"  警告 ({len(validation_result['warnings'])} 个):")
        for warning in validation_result['warnings']:
            print(f"    [WARN] {warning}")


def test_llm_parser():
    """测试LLM解析器"""
    print("\n" + "=" * 80)
    print("测试基于LLM的智能解析器")
    print("=" * 80)
    
    # 检查LLM是否可用
    llm_parser = LLMParser(llm_type="auto")
    
    if llm_parser.llm.is_available():
        print(f"\n[OK] LLM已配置: {llm_parser.llm.__class__.__name__}")
    else:
        print("\n[FAIL] LLM未配置，将使用Mock模式或传统规则方法")
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
            print(f"\n[OK] 质量评估符合预期")
        else:
            print(f"\n[FAIL] 质量评估不符合预期")


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


def evaluate_labeled_quality_gain():
    """使用小规模标注集验证优化前后质量差异（可复现）"""
    print("\n\n" + "=" * 80)
    print("标注集质量增益评估（Baseline vs Improved）")
    print("=" * 80)
    validator = CaseValidator()

    labeled_pairs = [
        {
            "name": "panic-calltrace",
            "baseline": {
                "title": "Linux kernel issue",
                "phenomenon": "系统异常，见文章",
                "environment": "Linux",
                "root_cause": "See article for details",
                "analysis_process": "",
                "key_logs": "",
                "solution": "See article",
                "troubleshooting_steps": ["N/A"],
            },
            "improved": {
                "title": "Linux kernel panic due to null pointer dereference",
                "phenomenon": "系统在高并发下触发kernel panic，出现NULL pointer dereference与Oops错误。",
                "environment": "Linux 5.10.0 x86_64",
                "root_cause": "驱动probe路径未检查空指针，直接访问private_data导致崩溃。",
                "analysis_process": "先对dmesg关键日志进行筛选，再根据Call Trace定位到driver_probe，最后代码审查确认缺少NULL检查。",
                "key_logs": "[12345.678901] BUG: unable to handle kernel NULL pointer dereference\nCall Trace: driver_probe+0x56/0x100",
                "solution": "在probe入口增加NULL检查并在错误路径释放资源，补充回归测试。",
                "troubleshooting_steps": ["收集dmesg日志", "分析Call Trace", "修复并回归验证"],
            },
        },
        {
            "name": "oom-leak",
            "baseline": {
                "title": "OOM problem",
                "phenomenon": "内存有问题",
                "environment": "Linux",
                "root_cause": "可能是bug",
                "analysis_process": "",
                "key_logs": "",
                "solution": "升级版本",
                "troubleshooting_steps": ["check"],
            },
            "improved": {
                "title": "Kernel OOM triggered by driver memory leak",
                "phenomenon": "业务高峰出现page allocation failure并触发OOM killer，节点周期性重启。",
                "environment": "Linux 5.15, container runtime",
                "root_cause": "驱动缓存对象引用计数错误导致内存长期泄漏。",
                "analysis_process": "通过memcg指标发现异常增长，随后kmemleak定位泄漏对象，最终追踪到释放路径缺失。",
                "key_logs": "[2203.12] Out of memory: Killed process 1024\nkernel: page allocation failure: order:0",
                "solution": "修复引用计数并在卸载路径补充kfree，加入压测验证脚本。",
                "troubleshooting_steps": ["查看OOM日志", "定位泄漏对象", "修复释放路径并压测"],
            },
        },
    ]

    baseline_scores = []
    improved_scores = []
    for pair in labeled_pairs:
        b = validator.validate(pair["baseline"])
        i = validator.validate(pair["improved"])
        baseline_scores.append(float(b.get("quality_score", 0)))
        improved_scores.append(float(i.get("quality_score", 0)))
        print(f"{pair['name']}: baseline={b.get('quality_score', 0):.1f}, improved={i.get('quality_score', 0):.1f}")

    avg_baseline = sum(baseline_scores) / len(baseline_scores)
    avg_improved = sum(improved_scores) / len(improved_scores)
    gain = avg_improved - avg_baseline
    print(f"\n平均分: baseline={avg_baseline:.1f}, improved={avg_improved:.1f}, gain={gain:.1f}")
    return gain >= 20


def main():
    """主函数"""
    print("Linux内核问题自动分析系统 - LLM智能解析器测试")
    print("=" * 80)
    
    # 测试LLM解析器
    test_llm_parser()
    
    # 测试真实案例
    test_real_cases()
    
    # 标注集质量增益验证
    gain_ok = evaluate_labeled_quality_gain()
    print(f"\n标注集质量增益验证: {'[OK] 通过' if gain_ok else '[FAIL] 未达标'}")
    
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