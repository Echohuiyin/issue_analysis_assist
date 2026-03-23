#!/usr/bin/env python3
"""
测试RAG Web界面
验证所有页面是否正常渲染
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
django.setup()

from django.test import Client
from django.urls import reverse


def test_rag_dashboard():
    """测试RAG仪表板页面"""
    print("=" * 70)
    print("测试 RAG 仪表板页面")
    print("=" * 70)
    
    client = Client()
    url = reverse('rag_dashboard')
    response = client.get(url)
    
    print(f"URL: {url}")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ 仪表板页面加载成功")
        return True
    else:
        print("❌ 仪表板页面加载失败")
        return False


def test_rag_search():
    """测试RAG案例检索页面"""
    print("\n" + "=" * 70)
    print("测试 RAG 案例检索页面")
    print("=" * 70)
    
    client = Client()
    url = reverse('rag_search')
    response = client.get(url)
    
    print(f"URL: {url}")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ 案例检索页面加载成功")
        return True
    else:
        print("❌ 案例检索页面加载失败")
        return False


def test_rag_qa():
    """测试RAG智能问答页面"""
    print("\n" + "=" * 70)
    print("测试 RAG 智能问答页面")
    print("=" * 70)
    
    client = Client()
    url = reverse('rag_qa')
    response = client.get(url)
    
    print(f"URL: {url}")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ 智能问答页面加载成功")
        return True
    else:
        print("❌ 智能问答页面加载失败")
        return False


def test_rag_analyze():
    """测试RAG问题分析页面"""
    print("\n" + "=" * 70)
    print("测试 RAG 问题分析页面")
    print("=" * 70)
    
    client = Client()
    url = reverse('rag_analyze')
    response = client.get(url)
    
    print(f"URL: {url}")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ 问题分析页面加载成功")
        return True
    else:
        print("❌ 问题分析页面加载失败")
        return False


def test_navigation():
    """测试导航链接"""
    print("\n" + "=" * 70)
    print("测试导航链接")
    print("=" * 70)
    
    client = Client()
    
    pages = [
        ('index', '首页'),
        ('add_case', '添加案例'),
        ('stats', '统计'),
        ('rag_dashboard', 'RAG仪表板'),
        ('rag_search', '案例检索'),
        ('rag_qa', '智能问答'),
        ('rag_analyze', '问题分析'),
    ]
    
    results = []
    for url_name, name in pages:
        url = reverse(url_name)
        response = client.get(url)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} {name}: {url} - {response.status_code}")
        results.append(response.status_code == 200)
    
    return all(results)


def main():
    print()
    print("=" * 70)
    print("RAG Web 界面测试")
    print("=" * 70)
    print()
    
    results = []
    
    results.append(("仪表板", test_rag_dashboard()))
    results.append(("案例检索", test_rag_search()))
    results.append(("智能问答", test_rag_qa()))
    results.append(("问题分析", test_rag_analyze()))
    results.append(("导航链接", test_navigation()))
    
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有Web界面测试通过！")
        print("\n启动服务器:")
        print("  python manage.py runserver")
        print("\n访问地址:")
        print("  http://localhost:8000/cases/rag/")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())