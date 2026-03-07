#!/usr/bin/env python3
"""
简化版案例质量过滤演示
直接使用预设内容测试，展示高质量过滤效果
"""

import sys
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')

from cases.acquisition.llm_parser import LLMParser


QUALITY_THRESHOLD = 70


def test_quality_filter():
    """测试质量过滤"""
    
    print("=" * 80)
    print("案例质量过滤演示")
    print(f"质量阈值: {QUALITY_THRESHOLD}分 (只有>=70分的案例才会被存储)")
    print("=" * 80)
    
    llm_parser = LLMParser(llm_type="ollama")
    
    # 准备多个测试案例
    test_cases = [
        # 高质量案例
        {
            "name": "高质量案例1 - Kernel Panic详细分析",
            "content": """
Linux Kernel Panic - NULL Pointer Dereference Analysis

Problem:
My Linux 5.4 kernel panicked with the following error:
BUG: unable to handle kernel NULL pointer dereference at address: 0000000000000008

Environment:
- Linux kernel 5.4.0-86-generic
- Ubuntu 20.04 LTS
- x86_64 architecture

Key Logs from dmesg:
[12345.678901] BUG: unable to handle kernel NULL pointer dereference
[12345.678902] IP: [<ffffffff81234567>] my_driver_init+0x12/0x30
[12345.678903] PGD 0 P4D 0 
[12345.678904] Oops: 0002 [#1] SMP

Root Cause Analysis:
After loading a custom network driver, the kernel crashed when accessing uninitialized pointer.
The driver probe function did not allocate private data structure before using it.
The dev->priv pointer was NULL when the driver tried to access it.

Troubleshooting Steps:
1. Analyzed dmesg output to locate crash point
2. Identified driver_init function in call stack
3. Reviewed driver source code
4. Found missing kmalloc for private data

Solution:
Added proper memory allocation in probe function:
struct driver_priv *priv = kmalloc(sizeof(*priv), GFP_KERNEL);
if (!priv)
    return -ENOMEM;
memset(priv, 0, sizeof(*priv));
dev_set_drvdata(dev, priv);

Prevention:
- Always initialize pointers before use
- Add NULL checks before dereferencing
- Use static code analysis tools
            """,
            "expected": "high"
        },
        {
            "name": "高质量案例2 - OOM问题排查",
            "content": """
Linux System Out of Memory (OOM) Issue

Problem:
System becomes unresponsive, dmesg shows:
[12345.678901] Out of memory: Killed process 1234 (java)
[12345.678902] oom_kill_allocating_task: out of memory

Environment:
- Linux 4.15.0-generic
- 8GB RAM, 4GB Swap
- Java application with memory leak

Analysis Process:
1. Checked vmstat output - si/so showing swap activity
2. Analyzed /proc/meminfo - available memory near zero
3. Used top command - found Java process consuming 6GB
4. Checked slabtop - slab cache growing abnormally
5. Identified memory leak in user-space application

Root Cause:
Java application has memory leak in caching layer.
The application keeps allocating new objects without releasing old ones.
Over time, this caused system to run out of memory.

Solution:
1. Restarted the Java application with heap size limit:
   java -Xmx2g -Xms1g -jar app.jar
2. Fixed the memory leak in application code
3. Added monitoring for memory usage

Prevention:
- Set appropriate memory limits for applications
- Monitor memory usage with tools like htop, vmstat
- Configure OOM killer behavior in /proc/sys/vm/overcommit_memory
            """,
            "expected": "high"
        },
        # 中等质量案例
        {
            "name": "中等质量案例 - 一般性描述",
            "content": """
Linux Kernel Issue

The Linux kernel has a problem with memory management.
When running heavy applications, the system gets slow.
I checked dmesg and found some errors.
Looking for help to fix this issue.
            """,
            "expected": "medium"
        },
        # 低质量案例
        {
            "name": "低质量案例1 - 信息不足",
            "content": """
Linux problem

My Linux doesn't work. Help!
            """,
            "expected": "low"
        },
        {
            "name": "低质量案例2 - 无解决方案",
            "content": """
Kernel Crash Issue

The system crashed today.
I don't know why.
It just stopped working.
Has anyone experienced this?
            """,
            "expected": "low"
        },
    ]
    
    results = {"high": [], "medium": [], "low": [], "failed": 0}
    
    for i, test in enumerate(test_cases):
        print(f"\n\n{'='*60}")
        print(f"测试 {i+1}: {test['name']}")
        print("=" * 60)
        
        # 解析
        print("解析中...")
        case_data = llm_parser.parse(test["content"], use_llm=True)
        
        if not case_data:
            print("  ✗ 解析失败")
            results["failed"] += 1
            continue
        
        # 质量评估
        quality = llm_parser.check_quality(case_data)
        score = quality.get("quality_score", 0)
        
        print(f"  质量分数: {score}/100")
        print(f"  预期: {test['expected']}")
        
        # 分类
        if score >= QUALITY_THRESHOLD:
            results["high"].append({"name": test["name"], "score": score, "data": case_data})
            print(f"  ✓ 高质量 - 会被存储")
        elif score >= 50:
            results["medium"].append({"name": test["name"], "score": score, "data": case_data})
            print(f"  ○ 中等质量 - 会被丢弃")
        else:
            results["low"].append({"name": test["name"], "score": score, "data": case_data})
            print(f"  ✗ 低质量 - 会被丢弃")
    
    # 统计
    print("\n\n" + "=" * 80)
    print("统计结果")
    print("=" * 80)
    
    total = len(test_cases)
    print(f"\n总测试数: {total}")
    print(f"  高质量 (>=70): {len(results['high'])} ({len(results['high'])/total*100:.0f}%)")
    print(f"  中等质量 (50-69): {len(results['medium'])} ({len(results['medium'])/total*100:.0f}%)")
    print(f"  低质量 (<50): {len(results['low'])} ({len(results['low'])/total*100:.0f}%)")
    print(f"  解析失败: {results['failed']}")
    
    # 展示高质量案例
    if results["high"]:
        print("\n\n" + "=" * 80)
        print(f"✓ 将被存储的高质量案例 ({len(results['high'])}个)")
        print("=" * 80)
        
        for i, r in enumerate(results["high"], 1):
            data = r["data"]
            print(f"""
{i}. {r['name']}
   质量分数: {r['score']}/100
   
   标题: {data.get('title', 'N/A')}
   现象: {data.get('phenomenon', 'N/A')[:80]}...
   根因: {data.get('root_cause', 'N/A')[:80]}...
   解决方案: {data.get('solution', 'N/A')[:80]}...
""")
    
    # 展示被丢弃的案例
    discarded = results["medium"] + results["low"]
    if discarded:
        print("\n\n" + "=" * 80)
        print(f"✗ 会被丢弃的案例 ({len(discarded)}个)")
        print("=" * 80)
        
        for i, r in enumerate(discarded, 1):
            quality = r["data"]
            issues = llm_parser.check_quality(r["data"]).get("issues", [])
            print(f"""
{i}. {r['name']}
   质量分数: {r['score']}/100
   问题: {', '.join(issues) if issues else '信息不足'}
""")
    
    return results


if __name__ == "__main__":
    test_quality_filter()
