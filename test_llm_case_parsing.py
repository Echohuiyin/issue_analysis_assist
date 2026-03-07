#!/usr/bin/env python3
"""
LLM案例解析测试脚本
从数据源获取案例，使用LLM解析，并展示结果
"""

import sys
import os

# Add project to path
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')

from cases.acquisition.fetchers import StackOverflowFetcher, CSDNFetcher
from cases.acquisition.llm_parser import LLMParser


def test_llm_parser_with_sources():
    """测试LLM解析器，解析真实数据源的案例"""
    
    print("=" * 80)
    print("LLM案例解析测试 - 使用Ollama (Qwen 1.8B)")
    print("=" * 80)
    
    # 初始化组件
    so_fetcher = StackOverflowFetcher()
    csdn_fetcher = CSDNFetcher()
    llm_parser = LLMParser(llm_type="ollama")
    
    # 测试关键词
    test_keywords = [
        "kernel panic",
        "kernel deadlock", 
        "kernel OOM",
        "kernel null pointer"
    ]
    
    all_results = []
    
    for keyword in test_keywords:
        print(f"\n\n{'='*80}")
        print(f"关键词: {keyword}")
        print("=" * 80)
        
        # 从StackOverflow获取
        print(f"\n[StackOverflow] 搜索: {keyword}")
        so_urls = so_fetcher.search(keyword, count=2)
        print(f"  找到 {len(so_urls)} 个结果")
        
        for i, url in enumerate(so_urls[:2]):
            print(f"\n  --- StackOverflow案例 {i+1} ---")
            print(f"  URL: {url}")
            
            # 获取内容
            content = so_fetcher.fetch(url)
            if not content:
                print("  ✗ 获取内容失败")
                continue
            
            # 使用LLM解析
            print("  正在使用LLM解析...")
            case_data = llm_parser.parse(content, use_llm=True)
            
            if case_data:
                # 质量评估
                quality = llm_parser.check_quality(case_data)
                
                result = {
                    "source": "stackoverflow",
                    "keyword": keyword,
                    "url": url,
                    "case_data": case_data,
                    "quality": quality
                }
                all_results.append(result)
                
                print(f"\n  解析结果:")
                print(f"    标题: {case_data.get('title', 'N/A')[:80]}...")
                print(f"    现象: {case_data.get('phenomenon', 'N/A')[:100]}...")
                print(f"    根因: {case_data.get('root_cause', 'N/A')[:100]}...")
                print(f"    解决方案: {case_data.get('solution', 'N/A')[:100]}...")
                print(f"    置信度: {case_data.get('confidence', 'N/A')}")
                print(f"\n  质量评估:")
                print(f"    质量分数: {quality.get('quality_score', 'N/A')}")
                print(f"    高质量: {quality.get('is_high_quality', 'N/A')}")
                print(f"    有关键日志: {quality.get('has_key_logs', 'N/A')}")
                print(f"    有分析过程: {quality.get('has_analysis_process', 'N/A')}")
                if quality.get('issues'):
                    print(f"    问题: {', '.join(quality.get('issues', []))}")
            else:
                print("  ✗ 解析失败")
    
    # 从CSDN获取
    print(f"\n\n{'='*80}")
    print("CSDN 数据源测试")
    print("=" * 80)
    
    cn_keywords = ["内核 panic", "内核 死锁", "内核 OOM"]
    
    for keyword in cn_keywords:
        print(f"\n[CSDN] 搜索: {keyword}")
        csdn_urls = csdn_fetcher.search(keyword, count=2)
        print(f"  找到 {len(csdn_urls)} 个结果")
        
        for i, url in enumerate(csdn_urls[:2]):
            print(f"\n  --- CSDN案例 {i+1} ---")
            print(f"  URL: {url}")
            
            # 获取内容
            content = csdn_fetcher.fetch(url)
            if not content:
                print("  ✗ 获取内容失败")
                continue
            
            # 使用LLM解析
            print("  正在使用LLM解析...")
            case_data = llm_parser.parse(content, use_llm=True)
            
            if case_data:
                # 质量评估
                quality = llm_parser.check_quality(case_data)
                
                result = {
                    "source": "csdn",
                    "keyword": keyword,
                    "url": url,
                    "case_data": case_data,
                    "quality": quality
                }
                all_results.append(result)
                
                print(f"\n  解析结果:")
                print(f"    标题: {case_data.get('title', 'N/A')[:80]}...")
                print(f"    现象: {case_data.get('phenomenon', 'N/A')[:100]}...")
                print(f"    根因: {case_data.get('root_cause', 'N/A')[:100]}...")
                print(f"    解决方案: {case_data.get('solution', 'N/A')[:100]}...")
                print(f"    置信度: {case_data.get('confidence', 'N/A')}")
                print(f"\n  质量评估:")
                print(f"    质量分数: {quality.get('quality_score', 'N/A')}")
                print(f"    高质量: {quality.get('is_high_quality', 'N/A')}")
                print(f"    有关键日志: {quality.get('has_key_logs', 'N/A')}")
                print(f"    有分析过程: {quality.get('has_analysis_process', 'N/A')}")
                if quality.get('issues'):
                    print(f"    问题: {', '.join(quality.get('issues', []))}")
            else:
                print("  ✗ 解析失败")
    
    return all_results


def show_good_bad_cases(results):
    """展示好案例和坏案例"""
    
    print("\n\n" + "=" * 80)
    print("案例质量汇总")
    print("=" * 80)
    
    # 按质量分数排序
    sorted_results = sorted(results, key=lambda x: x.get('quality', {}).get('quality_score', 0), reverse=True)
    
    # 质量好的案例 (>=70)
    good_cases = [r for r in sorted_results if r.get('quality', {}).get('quality_score', 0) >= 70]
    # 质量差的案例 (<50)
    bad_cases = [r for r in sorted_results if r.get('quality', {}).get('quality_score', 0) < 50]
    # 中等案例
    medium_cases = [r for r in sorted_results if 50 <= r.get('quality', {}).get('quality_score', 0) < 70]
    
    print(f"\n总计: {len(results)} 个案例")
    print(f"  高质量 (>=70分): {len(good_cases)} 个")
    print(f"  中等质量 (50-69分): {len(medium_cases)} 个")
    print(f"  低质量 (<50分): {len(bad_cases)} 个")
    
    # 展示高质量案例
    print("\n\n" + "=" * 80)
    print("✓ 高质量案例 (Top 5)")
    print("=" * 80)
    
    for i, result in enumerate(good_cases[:5], 1):
        case = result.get('case_data', {})
        quality = result.get('quality', {})
        
        print(f"\n--- 高质量案例 {i} ---")
        print(f"来源: {result.get('source', 'N/A')}")
        print(f"关键词: {result.get('keyword', 'N/A')}")
        print(f"质量分数: {quality.get('quality_score', 'N/A')}")
        print(f"置信度: {case.get('confidence', 'N/A')}")
        print(f"\n标题: {case.get('title', 'N/A')}")
        print(f"\n现象描述: {case.get('phenomenon', 'N/A')[:200]}...")
        print(f"\n根因分析: {case.get('root_cause', 'N/A')[:200]}...")
        print(f"\n解决方案: {case.get('solution', 'N/A')[:200]}...")
        if case.get('key_logs'):
            print(f"\n关键日志: {case.get('key_logs', 'N/A')[:150]}...")
    
    # 展示低质量案例
    print("\n\n" + "=" * 80)
    print("✗ 低质量案例")
    print("=" * 80)
    
    for i, result in enumerate(bad_cases, 1):
        case = result.get('case_data', {})
        quality = result.get('quality', {})
        
        print(f"\n--- 低质量案例 {i} ---")
        print(f"来源: {result.get('source', 'N/A')}")
        print(f"关键词: {result.get('keyword', 'N/A')}")
        print(f"质量分数: {quality.get('quality_score', 'N/A')}")
        print(f"问题: {', '.join(quality.get('issues', []))}")
        print(f"\n标题: {case.get('title', 'N/A')}")
        print(f"现象描述: {case.get('phenomenon', 'N/A')[:100] if case.get('phenomenon') else 'N/A'}")
        print(f"根因: {case.get('root_cause', 'N/A')[:100] if case.get('root_cause') else 'N/A'}")
        print(f"解决方案: {case.get('solution', 'N/A')[:100] if case.get('solution') else 'N/A'}")


if __name__ == "__main__":
    print("开始LLM案例解析测试...")
    print("这可能需要几分钟时间，请耐心等待...\n")
    
    results = test_llm_parser_with_sources()
    
    if results:
        show_good_bad_cases(results)
    else:
        print("\n没有解析到任何案例")
