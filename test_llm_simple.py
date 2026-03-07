#!/usr/bin/env python3
"""
LLM案例解析测试脚本 - 简化版
使用预设的案例内容测试LLM解析
"""

import sys
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')

from cases.acquisition.llm_parser import LLMParser


def test_with_sample_content():
    """使用预设样本内容测试"""
    
    print("=" * 80)
    print("LLM案例解析测试 - 使用Ollama (Qwen 1.8B)")
    print("=" * 80)
    
    # 初始化LLM解析器
    llm_parser = LLMParser(llm_type="ollama")
    
    # 高质量案例样本
    good_sample = """
Linux内核panic故障排查案例

一、问题现象
系统突然崩溃，提示"BUG: kernel panic - not syncing: Fatal exception"。通过dmesg查看日志，发现以下关键错误信息：
[12345.678901] Kernel panic - not syncing: Fatal exception
[12345.678902] CPU: 0 PID: 1234 Comm: swapper
[12345.678903] Call Trace:
[12345.678904]  [<ffffffff81234567>] driver_probe+0x123/0x456
[12345.678905]  [<ffffffff81234568>] driver_init+0x89/0xabc

二、环境信息
- 内核版本: Linux 5.4.0--generic
- 操作系统: Ubuntu 20.04
- 硬件平台: x86_64

三、根因分析
经过排查分析，发现是内核驱动程序在初始化时存在空指针引用。当driver_probe函数调用driver_init时，由于没有正确初始化私有数据指针，导致访问空地址引发panic。问题出在驱动代码的第123行，忘记了在probe函数中分配私有数据结构。

四、分析过程
1. 首先查看dmesg日志，确定panic位置
2. 根据Call Stack定位到driver_probe函数
3. 检查驱动初始化代码，发现私有数据未分配
4. 添加kmalloc分配内存后问题解决

五、解决方案
在driver_probe函数中添加私有数据分配：
struct driver_data *priv = kmalloc(sizeof(struct driver_data), GFP_KERNEL);
if (!priv)
    return -ENOMEM;
memset(priv, 0, sizeof(struct driver_data));
dev_set_drvdata(dev, priv);

六、预防措施
1. 驱动开发时注意空指针检查
2. 使用static analysis工具检测潜在问题
3. 添加内核配置选项检测未初始化变量
"""
    
    # 低质量案例样本
    bad_sample = """
Linux内核问题

今天遇到一个Linux内核的问题，具体的我也不是很清楚反正是系统崩溃了。
日志看不太懂，有知道的朋友吗？在线等。
这个问题应该怎么解决啊？
"""
    
    # 中等质量案例样本
    medium_sample = """
内核驱动加载失败问题

一、问题
驱动加载失败

二、环境
Linux系统

三、分析
查看日志发现驱动加载失败

四、解决
修改驱动代码

具体请参考相关文档。
"""
    
    test_cases = [
        ("高质量案例", good_sample, "expected_good"),
        ("低质量案例", bad_sample, "expected_bad"),
        ("中等质量案例", medium_sample, "expected_medium"),
    ]
    
    results = []
    
    for name, content, expected in test_cases:
        print(f"\n\n{'='*80}")
        print(f"测试: {name}")
        print("=" * 80)
        
        # 使用LLM解析
        print("正在解析...")
        case_data = llm_parser.parse(content, use_llm=True)
        
        if case_data:
            # 质量评估
            quality = llm_parser.check_quality(case_data)
            
            print(f"\n解析结果:")
            print(f"  标题: {case_data.get('title', 'N/A')}")
            print(f"  现象: {case_data.get('phenomenon', 'N/A')[:150]}...")
            print(f"  根因: {case_data.get('root_cause', 'N/A')[:150]}...")
            print(f"  解决方案: {case_data.get('solution', 'N/A')[:150]}...")
            print(f"  置信度: {case_data.get('confidence', 'N/A')}")
            
            print(f"\n质量评估:")
            print(f"  质量分数: {quality.get('quality_score', 'N/A')}")
            print(f"  高质量: {quality.get('is_high_quality', 'N/A')}")
            print(f"  有关键日志: {quality.get('has_key_logs', 'N/A')}")
            print(f"  有分析过程: {quality.get('has_analysis_process', 'N/A')}")
            if quality.get('issues'):
                print(f"  问题: {', '.join(quality.get('issues', []))}")
            
            results.append({
                "name": name,
                "expected": expected,
                "case_data": case_data,
                "quality": quality
            })
        else:
            print("  解析失败")
    
    # 汇总
    print("\n\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    print(f"\n{'案例名称':<20} {'预期':<15} {'实际分数':<10} {'是否匹配'}")
    print("-" * 60)
    
    for r in results:
        expected = r.get('expected')
        actual = r.get('quality', {}).get('quality_score', 0)
        
        if expected == "expected_good":
            match = "✓" if actual >= 70 else "✗"
        elif expected == "expected_bad":
            match = "✓" if actual < 50 else "✗"
        else:
            match = "✓" if 50 <= actual < 70 else "✗"
        
        print(f"{r['name']:<20} {expected:<15} {actual:<10} {match}")
    
    # 展示高质量案例详情
    print("\n\n" + "=" * 80)
    print("✓ 高质量案例详情")
    print("=" * 80)
    
    good = [r for r in results if r.get('quality', {}).get('quality_score', 0) >= 70]
    for i, r in enumerate(good, 1):
        case = r.get('case_data', {})
        print(f"\n--- 案例 {i} ---")
        print(f"标题: {case.get('title')}")
        print(f"\n现象描述:")
        print(f"  {case.get('phenomenon')}")
        print(f"\n根因分析:")
        print(f"  {case.get('root_cause')}")
        print(f"\n解决方案:")
        print(f"  {case.get('solution')}")
        if case.get('key_logs'):
            print(f"\n关键日志:")
            print(f"  {case.get('key_logs')}")
    
    # 展示低质量案例详情
    print("\n\n" + "=" * 80)
    print("✗ 低质量案例详情")
    print("=" * 80)
    
    bad = [r for r in results if r.get('quality', {}).get('quality_score', 0) < 50]
    for i, r in enumerate(bad, 1):
        case = r.get('case_data', {})
        quality = r.get('quality', {})
        print(f"\n--- 案例 {i} ---")
        print(f"标题: {case.get('title')}")
        print(f"质量分数: {quality.get('quality_score')}")
        print(f"问题: {', '.join(quality.get('issues', []))}")
        print(f"\n现象描述: {case.get('phenomenon')}")
        print(f"根因: {case.get('root_cause')}")
        print(f"解决方案: {case.get('solution')}")


if __name__ == "__main__":
    test_with_sample_content()
