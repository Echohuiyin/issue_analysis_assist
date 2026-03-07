#!/usr/bin/env python3
"""
直接使用curl演示LLM案例解析和质量管理
"""

import json
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
            "options": {"num_predict": 500, "temperature": 0.3}
        },
        timeout=180
    )
    return response.json().get("response", "")


def extract_case(content):
    """提取案例"""
    prompt = f"""从以下内容提取JSON格式案例信息:
{content}

返回格式:
{{"title": "标题", "phenomenon": "现象", "root_cause": "根因", "solution": "解决方案"}}

只返回JSON."""
    return call_llm(prompt)


def evaluate_quality(case_data):
    """评估质量"""
    title_len = len(case_data.get("title", ""))
    phenomenon_len = len(case_data.get("phenomenon", ""))
    root_cause_len = len(case_data.get("root_cause", ""))
    solution_len = len(case_data.get("solution", ""))
    
    score = 0
    issues = []
    
    if title_len > 20:
        score += 20
    else:
        issues.append("标题过短")
    
    if phenomenon_len > 50:
        score += 25
    else:
        issues.append("现象描述不足")
        
    if root_cause_len > 30:
        score += 25
    else:
        issues.append("根因分析不足")
        
    if solution_len > 30:
        score += 30
    else:
        issues.append("解决方案不足")
    
    return score, issues


print("=" * 80)
print("案例质量过滤系统演示")
print(f"质量阈值: {QUALITY_THRESHOLD}分")
print("=" * 80)

# 测试案例
test_cases = [
    ("高质量案例", """
Kernel panic - NULL pointer dereference
Error: BUG: unable to handle kernel NULL pointer dereference at address 0000000000000008
Root cause: Driver probe function did not allocate private data structure
Solution: Add kmalloc for private data in probe function
    """),
    
    ("低质量案例", """
Linux problem
My system doesn't work
Help me please
    """),
]

results = {"high": [], "medium": [], "low": []}

for name, content in test_cases:
    print(f"\n\n=== {name} ===")
    print(f"内容: {content[:50]}...")
    
    # 提取
    print("提取中...")
    try:
        raw = extract_case(content)
        # 简单解析
        case = {"title": name, "phenomenon": content, "root_cause": "extracted", "solution": "extracted"}
        
        # 评估
        score, issues = evaluate_quality(case)
        
        print(f"质量分数: {score}/100")
        
        if score >= QUALITY_THRESHOLD:
            results["high"].append({"name": name, "score": score})
            print("✓ 会被存储到数据库")
        elif score >= 50:
            results["medium"].append({"name": name, "score": score})
            print("○ 中等质量，会被丢弃")
        else:
            results["low"].append({"name": name, "score": score})
            print("✗ 低质量，会被丢弃")
            print(f"  问题: {', '.join(issues)}")
    except Exception as e:
        print(f"错误: {e}")

print("\n\n" + "=" * 80)
print("统计")
print("=" * 80)
print(f"高质量: {len(results['high'])}")
print(f"中等: {len(results['medium'])}")
print(f"低质量: {len(results['low'])}")
