#!/usr/bin/env python3
"""
案例质量过滤系统
只存储高质量案例（质量分数>=70），丢弃低质量案例
"""

import sys
import os
import django

# Setup Django
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
django.setup()

from cases.acquisition.fetchers import StackOverflowFetcher, CSDNFetcher
from cases.acquisition.llm_parser import LLMParser
from cases.models import KernelCase
from cases.acquisition.storage import CaseStorage


QUALITY_THRESHOLD = 70  # Only store cases with quality score >= 70


def fetch_and_evaluate_cases():
    """获取并评估案例质量"""
    
    print("=" * 80)
    print("案例质量过滤系统")
    print(f"质量阈值: {QUALITY_THRESHOLD}分")
    print("=" * 80)
    
    # 初始化组件
    so_fetcher = StackOverflowFetcher()
    csdn_fetcher = CSDNFetcher()
    llm_parser = LLMParser(llm_type="ollama")
    storage = CaseStorage()
    
    # 测试关键词
    keywords = [
        ("kernel panic", "stackoverflow"),
        ("kernel deadlock", "stackoverflow"),
        ("kernel OOM", "stackoverflow"),
        ("kernel null pointer", "stackoverflow"),
        ("kernel crash", "stackoverflow"),
        ("内核 panic", "csdn"),
        ("内核 死锁", "csdn"),
        ("内核 OOM", "csdn"),
    ]
    
    results = {
        "total_fetched": 0,
        "total_parsed": 0,
        "high_quality": [],
        "medium_quality": [],
        "low_quality": [],
        "stored": 0,
        "failed": 0
    }
    
    for keyword, source in keywords:
        print(f"\n\n{'='*60}")
        print(f"搜索: [{source}] {keyword}")
        print("=" * 60)
        
        # 获取URL列表
        if source == "stackoverflow":
            urls = so_fetcher.search(keyword, count=3)
            fetcher = so_fetcher
        else:
            urls = csdn_fetcher.search(keyword, count=3)
            fetcher = csdn_fetcher
        
        print(f"找到 {len(urls)} 个URL")
        results["total_fetched"] += len(urls)
        
        for i, url in enumerate(urls):
            print(f"\n--- 案例 {i+1}/{len(urls)} ---")
            print(f"URL: {url[:60]}...")
            
            # 获取内容
            content = fetcher.fetch(url)
            if not content:
                print("  ✗ 获取内容失败")
                results["failed"] += 1
                continue
            
            # 使用LLM解析
            print("  解析中...")
            case_data = llm_parser.parse(content, use_llm=True)
            
            if not case_data:
                print("  ✗ 解析失败")
                results["failed"] += 1
                continue
            
            results["total_parsed"] += 1
            
            # 质量评估
            quality = llm_parser.check_quality(case_data)
            score = quality.get("quality_score", 0)
            
            print(f"  质量分数: {score}/100")
            
            # 分类
            case_info = {
                "url": url,
                "source": source,
                "keyword": keyword,
                "case_data": case_data,
                "quality": quality
            }
            
            if score >= QUALITY_THRESHOLD:
                print(f"  ✓ 高质量 - 准备存储")
                results["high_quality"].append(case_info)
            elif score >= 50:
                print(f"  ○ 中等质量 - 丢弃")
                results["medium_quality"].append(case_info)
            else:
                print(f"  ✗ 低质量 - 丢弃")
                results["low_quality"].append(case_info)
    
    return results


def store_high_quality_cases(high_quality_cases):
    """存储高质量案例到数据库"""
    
    print("\n\n" + "=" * 80)
    print("存储高质量案例")
    print("=" * 80)
    
    storage = CaseStorage()
    stored = 0
    
    for case_info in high_quality_cases:
        case_data = case_info.get("case_data", {})
        url = case_info.get("url", "")
        source = case_info.get("source", "")
        
        # 构建存储数据
        storage_data = {
            "title": case_data.get("title", "Unknown"),
            "phenomenon": case_data.get("phenomenon", ""),
            "root_cause": case_data.get("root_cause", ""),
            "solution": case_data.get("solution", ""),
            "reference_url": url,
            "source": source,
            "module": "other",  # 可以后续用classifier分类
            "quality_score": case_info.get("quality", {}).get("quality_score", 0)
        }
        
        # 尝试存储
        result = storage.store(storage_data)
        
        if result.get("success"):
            print(f"  ✓ 存储成功: {storage_data['title'][:40]}...")
            stored += 1
        else:
            msg = result.get("message", "Unknown error")
            if "duplicate" in msg.lower():
                print(f"  - 已存在: {storage_data['title'][:40]}...")
            else:
                print(f"  ✗ 存储失败: {msg}")
    
    return stored


def show_statistics(results, stored_count):
    """显示统计信息"""
    
    print("\n\n" + "=" * 80)
    print("统计信息")
    print("=" * 80)
    
    total = results["total_fetched"]
    parsed = results["total_parsed"]
    high = len(results["high_quality"])
    medium = len(results["medium_quality"])
    low = len(results["low_quality"])
    failed = results["failed"]
    
    print(f"""
获取统计:
  总URL数: {total}
  成功解析: {parsed}
  解析失败: {failed}

质量分布:
  高质量 (>={QUALITY_THRESHOLD}): {high} ({high/parsed*100:.1f}%)
  中等质量 (50-{QUALITY_THRESHOLD-1}): {medium} ({medium/parsed*100:.1f}%)
  低质量 (<50): {low} ({low/parsed*100:.1f}%)

存储结果:
  实际存储: {stored_count}
  丢弃数量: {parsed - stored_count}
""")
    
    # 展示高质量案例
    if results["high_quality"]:
        print("\n" + "=" * 80)
        print(f"✓ 高质量案例 ({len(results['high_quality'])}个)")
        print("=" * 80)
        
        for i, case in enumerate(results["high_quality"], 1):
            data = case.get("case_data", {})
            quality = case.get("quality", {})
            print(f"""
{i}. {data.get('title', 'N/A')[:60]}
   来源: {case.get('source')} | 质量: {quality.get('quality_score')}分
   现象: {data.get('phenomenon', 'N/A')[:80]}...
   根因: {data.get('root_cause', 'N/A')[:80]}...
""")
    
    # 展示被丢弃的案例原因
    if results["low_quality"]:
        print("\n" + "=" * 80)
        print(f"✗ 被丢弃的低质量案例 ({len(results['low_quality'])}个)")
        print("=" * 80)
        
        for i, case in enumerate(results["low_quality"], 1):
            data = case.get("case_data", {})
            quality = case.get("quality", {})
            issues = quality.get("issues", [])
            print(f"""
{i}. {data.get('title', 'N/A')[:60]}
   来源: {case.get('source')} | 质量: {quality.get('quality_score')}分
   问题: {', '.join(issues) if issues else '信息不足'}
""")


if __name__ == "__main__":
    print("开始案例质量过滤...\n")
    
    # 1. 获取并评估
    results = fetch_and_evaluate_cases()
    
    # 2. 存储高质量案例
    if results["high_quality"]:
        stored = store_high_quality_cases(results["high_quality"])
    else:
        stored = 0
    
    # 3. 显示统计
    show_statistics(results, stored)
