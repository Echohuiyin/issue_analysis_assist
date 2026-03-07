#!/usr/bin/env python3
"""
直接使用curl演示LLM案例解析和质量管理
使用真实的LLM提取结果来评估质量
"""

import json
import re
import requests


QUALITY_THRESHOLD = 70

def call_llm(prompt):
    """调用Ollama"""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen:1.8b",
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 800, "temperature": 0.3}
        },
        timeout=180
    )
    return response.json().get("response", "")


def extract_case(content):
    """提取案例"""
    prompt = f"""从以下技术文章提取JSON格式案例信息:
{content}

要求:
1. title: 问题标题
2. phenomenon: 详细的问题现象描述
3. root_cause: 根本原因分析
4. solution: 具体解决方案

只返回JSON，不要其他文字。"""
    raw = call_llm(prompt)
    
    # 解析JSON
    try:
        # 尝试直接解析
        data = json.loads(raw)
        return data
    except:
        # 尝试提取JSON部分
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return None


def evaluate_quality(case_data):
    """评估提取的案例质量"""
    title = case_data.get("title", "") or ""
    phenomenon = case_data.get("phenomenon", "") or ""
    root_cause = case_data.get("root_cause", "") or ""
    solution = case_data.get("solution", "") or ""
    
    score = 0
    issues = []
    
    # 检查标题
    if len(title) > 10 and "unknown" not in title.lower():
        score += 20
    else:
        issues.append("标题不足")
    
    # 检查现象描述
    if len(phenomenon) > 30:
        score += 25
        if any(kw in phenomenon.lower() for kw in ["error", "panic", "crash", "fail", "bug"]):
            score += 5
    else:
        issues.append("现象描述不足")
    
    # 检查根因
    if len(root_cause) > 20 and "unknown" not in root_cause.lower():
        score += 25
    else:
        issues.append("根因分析不足")
    
    # 检查解决方案
    if len(solution) > 20 and "unknown" not in solution.lower():
        score += 30
    else:
        issues.append("解决方案不足")
    
    return score, issues


print("=" * 80)
print("案例质量过滤系统演示 - Qwen 1.8B (Ollama)")
print(f"质量阈值: {QUALITY_THRESHOLD}分 (>=70才会存入数据库)")
print("=" * 80)

# 测试案例 - 更详细的描述
test_cases = [
    ("高质量案例", """
Linux Kernel Panic - NULL Pointer Dereference

Problem Description:
My Linux 5.4 kernel crashed with "BUG: unable to handle kernel NULL pointer dereference" error.
The system became unresponsive and required hard reset.

Environment:
- Linux kernel 5.4.0-86-generic
- Ubuntu 20.04 LTS
- x86_64 architecture

Key Logs from dmesg:
[12345.678901] BUG: unable to handle kernel NULL pointer dereference at address 0000000000000008
[12345.678902] IP: [<ffffffff81234567>] my_driver_init+0x12/0x30

Root Cause Analysis:
After loading a custom network driver, the kernel crashed when accessing uninitialized pointer.
The driver probe function did not allocate private data structure before using dev->priv pointer.
The pointer was NULL causing the panic when dereferenced.

Troubleshooting Steps:
1. Analyzed dmesg output to locate crash point
2. Identified driver_init function in the call stack
3. Reviewed driver source code
4. Found missing kmalloc for private data allocation

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
    """),
    
    ("中等质量案例", """
Linux Kernel Issue

The Linux kernel has a problem with memory management.
When running heavy applications, the system gets slow.
I checked dmesg and found some errors.
Looking for help to fix this issue.
    """),
    
    ("低质量案例", """
Linux problem

My Linux doesn't work. Help!
    """),
]

results = {"high": [], "medium": [], "low": []}

for name, content in test_cases:
    print(f"\n\n{'='*60}")
    print(f"测试: {name}")
    print("=" * 60)
    
    print("提取中...")
    case_data = extract_case(content)
    
    if case_data:
        print(f"\n提取结果:")
        print(f"  标题: {case_data.get('title', 'N/A')}")
        print(f"  现象: {case_data.get('phenomenon', 'N/A')[:80]}...")
        print(f"  根因: {case_data.get('root_cause', 'N/A')[:80]}...")
        print(f"  解决方案: {case_data.get('solution', 'N/A')[:80]}...")
        
        # 评估质量
        score, issues = evaluate_quality(case_data)
        
        print(f"\n质量评估:")
        print(f"  质量分数: {score}/100")
        
        if score >= QUALITY_THRESHOLD:
            results["high"].append({"name": name, "score": score})
            print(f"  ✓ 高质量 - 会存储到数据库")
        elif score >= 50:
            results["medium"].append({"name": name, "score": score})
            print(f"  ○ 中等质量 - 会丢弃")
        else:
            results["low"].append({"name": name, "score": score})
            print(f"  ✗ 低质量 - 会丢弃")
            if issues:
                print(f"    原因: {', '.join(issues)}")
    else:
        print("提取失败")

print("\n\n" + "=" * 80)
print("统计结果")
print("=" * 80)
print(f"\n高质量 (>=70分): {len(results['high'])}")
print(f"中等质量 (50-69分): {len(results['medium'])}")
print(f"低质量 (<50分): {len(results['low'])}")

print("\n结论:")
if results["high"]:
    print(f"- 将存储 {len(results['high'])} 个高质量案例到数据库")
else:
    print("- 没有符合质量标准的案例")
    
if results["medium"] or results["low"]:
    print(f"- 将丢弃 {len(results['medium']) + len(results['low'])} 个低质量案例")
