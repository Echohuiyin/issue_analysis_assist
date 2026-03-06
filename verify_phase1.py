#!/usr/bin/env python3
"""
验证脚本：用于验证 Phase 1（案例获取模块）的所有功能

验证内容包括：
1. 运行单元测试
2. 测试内容清洗器功能
3. 测试内核模块分类器功能
4. 测试 StackOverflow 爬虫功能（真实数据）
5. 测试 CSDN 爬虫功能（真实数据）
6. 测试完整的案例获取流程
"""

import os
import sys
import subprocess
import json
from typing import Dict, List

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置 Django 环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kernel_cases.settings")
import django
django.setup()

# 导入需要验证的组件
from cases.acquisition.cleaner import content_cleaner
from cases.acquisition.classifier import module_classifier
from cases.acquisition.fetchers import StackOverflowFetcher, CSDNFetcher
from cases.acquisition.parsers import ForumParser, BlogParser
from cases.acquisition.storage import CaseStorage
from cases.acquisition.main import CaseAcquisition

def run_unit_tests():
    """运行单元测试"""
    print("\n=== 运行单元测试 ===")
    result = subprocess.run(
        [sys.executable, "manage.py", "test", "cases.tests.test_acquisition", "-v", "2"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print("错误信息:", result.stderr)
    print(f"测试结果: {'通过' if result.returncode == 0 else '失败'}")
    return result.returncode == 0

def test_content_cleaner():
    """测试内容清洗器功能"""
    print("\n=== 测试内容清洗器 ===")
    
    # 测试 HTML 清洗
    html_content = '''
    <html>
        <head><title>测试页面</title></head>
        <body>
            <h1>Linux内核内存泄漏</h1>
            <p>这是一个测试段落。</p>
            <pre><code>int main() {
    print("Hello World");
    return 0;
}</code></pre>
            <script>alert('测试')</script>
        </body>
    </html>
    '''
    
    cleaned_text = content_cleaner.clean_html(html_content)
    print("HTML清洗结果:")
    print(cleaned_text[:200] + "...")
    
    # 测试代码块提取
    code_blocks = content_cleaner.extract_code_blocks(html_content)
    print(f"\n提取的代码块数量: {len(code_blocks)}")
    if code_blocks:
        print("第一个代码块:")
        print(code_blocks[0])
    
    # 测试内容哈希计算
    text1 = "测试内容"
    text2 = "测试内容"
    text3 = "不同内容"
    
    hash1 = content_cleaner.compute_content_hash(text1)
    hash2 = content_cleaner.compute_content_hash(text2)
    hash3 = content_cleaner.compute_content_hash(text3)
    
    print(f"\n内容哈希测试:")
    print(f"text1的哈希: {hash1}")
    print(f"text2的哈希: {hash2}")
    print(f"text3的哈希: {hash3}")
    print(f"text1和text2哈希相同: {hash1 == hash2}")
    print(f"text1和text3哈希不同: {hash1 != hash3}")
    
    return True

def test_module_classifier():
    """测试内核模块分类器功能"""
    print("\n=== 测试内核模块分类器 ===")
    
    test_cases = [
        ("系统内存泄漏，OOM killer被触发", "memory"),
        ("TCP连接超时，网卡驱动异常", "network"),
        ("进程调度异常，CPU利用率过高", "scheduler"),
        ("spinlock死锁问题分析", "lock"),
        ("定时器超时导致的问题", "timer"),
        ("磁盘IO性能瓶颈分析", "storage"),
        ("中断处理程序异常", "irq"),
        ("USB驱动加载失败", "driver"),
        ("这是一个不相关的内容", "other"),
    ]
    
    correct_count = 0
    total_count = len(test_cases)
    
    for text, expected_module in test_cases:
        classified_module = module_classifier.classify_module(text)
        print(f"文本: '{text}'")
        print(f"分类结果: {classified_module} (期望: {expected_module})")
        print(f"{'✓' if classified_module == expected_module else '✗'}\n")
        
        if classified_module == expected_module:
            correct_count += 1
    
    accuracy = correct_count / total_count * 100
    print(f"分类准确率: {accuracy:.1f}% ({correct_count}/{total_count})")
    
    return accuracy >= 80

def test_stackoverflow_fetcher():
    """测试 StackOverflow 爬虫功能"""
    print("\n=== 测试 StackOverflow 爬虫 ===")
    
    fetcher = StackOverflowFetcher()
    parser = ForumParser()
    
    try:
        # 测试搜索功能
        print("搜索 Linux kernel panic 相关问题...")
        urls = fetcher.search("linux kernel panic", count=1)
        
        if not urls:
            print("未找到相关问题")
            return False
        
        print(f"找到 {len(urls)} 个问题")
        
        # 测试获取问题详情
        for url in urls[:1]:  # 只测试第一个
            print(f"\n获取问题详情: {url}")
            content = fetcher.fetch(url)
            
            if not content:
                print("获取内容失败")
                continue
            
            print(f"内容长度: {len(content)} 字符")
            
            # 测试解析功能
            print("解析问题内容...")
            parsed_data = parser.parse(content)
            
            if not parsed_data:
                print("解析失败")
                continue
            
            print(f"解析成功!")
            print(f"标题: {parsed_data.get('title', 'N/A')}")
            print(f"现象: {parsed_data.get('phenomenon', 'N/A')[:100]}...")
            print(f"根因: {parsed_data.get('root_cause', 'N/A')[:100]}...")
            print(f"解决方案: {parsed_data.get('solution', 'N/A')[:100]}...")
            
            return True
            
    except Exception as e:
        print(f"测试失败: {e}")
        return False
    
    return False

def test_csdn_fetcher():
    """测试 CSDN 爬虫功能"""
    print("\n=== 测试 CSDN 爬虫 ===")
    
    fetcher = CSDNFetcher()
    parser = BlogParser()
    
    try:
        # 测试搜索功能
        print("搜索 内核 panic 相关文章...")
        urls = fetcher.search("内核 panic", count=1)
        
        if not urls:
            print("未找到相关文章")
            return False
        
        print(f"找到 {len(urls)} 篇文章")
        
        # 测试获取文章详情
        for url in urls[:1]:  # 只测试第一个
            print(f"\n获取文章详情: {url}")
            content = fetcher.fetch(url)
            
            if not content:
                print("获取内容失败")
                continue
            
            print(f"内容长度: {len(content)} 字符")
            
            # 测试解析功能
            print("解析文章内容...")
            parsed_data = parser.parse(content)
            
            if not parsed_data:
                print("解析失败")
                continue
            
            print(f"解析成功!")
            print(f"标题: {parsed_data.get('title', 'N/A')}")
            print(f"现象: {parsed_data.get('phenomenon', 'N/A')[:100]}...")
            print(f"根因: {parsed_data.get('root_cause', 'N/A')[:100]}...")
            print(f"解决方案: {parsed_data.get('solution', 'N/A')[:100]}...")
            
            return True
            
    except Exception as e:
        print(f"测试失败: {e}")
        return False
    
    return False

def test_full_acquisition_flow():
    """测试完整的案例获取流程"""
    print("\n=== 测试完整的案例获取流程 ===")
    
    try:
        # 创建 CaseAcquisition 实例
        ca = CaseAcquisition()
        
        # 测试获取一个 StackOverflow 案例
        print("从 StackOverflow 获取案例...")
        results = ca.acquire_from_stackoverflow("linux kernel oops", count=1)
        
        if results:
            result = results[0]
            print(f"获取结果: {'成功' if result.get('success') else '失败'}")
            if result.get('success'):
                print(f"案例ID: {result.get('case_id')}")
        else:
            print("未获取到案例")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

def main():
    """主函数"""
    print("Linux内核问题自动分析系统 - 案例获取模块验证")
    print("=" * 60)
    
    # 运行所有测试
    tests = [
        ("单元测试", run_unit_tests),
        ("内容清洗器", test_content_cleaner),
        ("内核模块分类器", test_module_classifier),
        ("StackOverflow爬虫", test_stackoverflow_fetcher),
        ("CSDN爬虫", test_csdn_fetcher),
        ("完整获取流程", test_full_acquisition_flow),
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
        print("🎉 所有测试通过！Phase 1 验证成功！")
        return 0
    else:
        print("❌ 部分测试失败，请检查代码！")
        return 1

if __name__ == "__main__":
    sys.exit(main())