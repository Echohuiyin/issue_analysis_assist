#!/usr/bin/env python3
"""
测试RAG API接口
验证所有API端点是否正常工作
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000/cases/api"


def test_api_health():
    """测试API健康检查"""
    print("=" * 70)
    print("测试 API 健康检查")
    print("=" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/health/")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"状态: {data.get('status')}")
            print(f"服务: {data.get('service')}")
            print(f"版本: {data.get('version')}")
            print(f"训练案例数: {data.get('training_cases')}")
            print("✅ 健康检查通过")
            return True
        else:
            print("❌ 健康检查失败")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False


def test_search_api():
    """测试案例检索API"""
    print("\n" + "=" * 70)
    print("测试案例检索 API")
    print("=" * 70)
    
    payload = {
        "query": "kernel panic 内存崩溃",
        "top_k": 3,
        "threshold": 0.5
    }
    
    print(f"请求: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        response = requests.post(f"{BASE_URL}/search/", json=payload)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功: {data.get('success')}")
            print(f"找到案例: {data.get('count')}个")
            
            cases = data.get('cases', [])
            for i, case in enumerate(cases[:2], 1):
                print(f"\n案例 {i}:")
                print(f"  标题: {case.get('title')[:60]}")
                print(f"  相似度: {case.get('similarity'):.2%}")
            
            print("\n✅ 案例检索API测试通过")
            return True
        else:
            print(f"❌ 案例检索API测试失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False


def test_recommend_api():
    """测试案例推荐API"""
    print("\n" + "=" * 70)
    print("测试案例推荐 API")
    print("=" * 70)
    
    payload = {
        "problem_description": "系统出现内存泄漏问题",
        "top_k": 3,
        "min_similarity": 0.5
    }
    
    print(f"请求: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        response = requests.post(f"{BASE_URL}/recommend/", json=payload)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功: {data.get('success')}")
            print(f"推荐案例: {data.get('count')}个")
            
            recommendations = data.get('recommendations', [])
            for i, rec in enumerate(recommendations[:2], 1):
                print(f"\n推荐 {i}:")
                print(f"  标题: {rec.get('title')[:60]}")
                print(f"  相似度: {rec.get('similarity'):.2%}")
                print(f"  置信度: {rec.get('confidence'):.2%}")
            
            print("\n✅ 案例推荐API测试通过")
            return True
        else:
            print(f"❌ 案例推荐API测试失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False


def test_qa_api():
    """测试智能问答API"""
    print("\n" + "=" * 70)
    print("测试智能问答 API")
    print("=" * 70)
    
    payload = {
        "question": "系统出现kernel panic怎么办？",
        "top_k": 3,
        "min_similarity": 0.5
    }
    
    print(f"请求: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        response = requests.post(f"{BASE_URL}/qa/", json=payload)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功: {data.get('success')}")
            print(f"置信度: {data.get('confidence'):.2%}")
            print(f"答案: {data.get('answer')[:200]}...")
            
            cases = data.get('cases', [])
            print(f"引用案例: {len(cases)}个")
            
            print("\n✅ 智能问答API测试通过")
            return True
        else:
            print(f"❌ 智能问答API测试失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False


def test_analyze_api():
    """测试问题分析API"""
    print("\n" + "=" * 70)
    print("测试问题分析 API")
    print("=" * 70)
    
    payload = {
        "issue_description": "系统运行一段时间后出现kernel panic",
        "logs": "kernel: BUG: unable to handle kernel NULL pointer dereference"
    }
    
    print(f"请求: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        response = requests.post(f"{BASE_URL}/analyze/", json=payload)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功: {data.get('success')}")
            
            analysis = data.get('analysis', {})
            print(f"置信度: {analysis.get('confidence_score'):.2%}")
            print(f"相似案例: {len(analysis.get('similar_cases', []))}个")
            
            print("\n✅ 问题分析API测试通过")
            return True
        else:
            print(f"❌ 问题分析API测试失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False


def main():
    print()
    print("=" * 70)
    print("RAG API 接口测试")
    print("=" * 70)
    print("\n注意: 请确保Django服务器正在运行")
    print("启动命令: python manage.py runserver")
    print()
    
    input("按回车键开始测试...")
    
    results = []
    
    results.append(("健康检查", test_api_health()))
    results.append(("案例检索", test_search_api()))
    results.append(("案例推荐", test_recommend_api()))
    results.append(("智能问答", test_qa_api()))
    results.append(("问题分析", test_analyze_api()))
    
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
        print("\n🎉 所有API测试通过！")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查服务器状态")
        return 1


if __name__ == "__main__":
    sys.exit(main())