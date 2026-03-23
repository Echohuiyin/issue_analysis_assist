#!/usr/bin/env python3
"""
改进的StackOverflow案例收集器
- 筛选高投票问题
- 支持多种过滤条件
- 增加错误处理和重试机制
"""
import os
import sys
import time
import json
import requests
from typing import List, Dict, Optional

# 设置环境变量
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')

# 导入必要的模块
import django
django.setup()

from cases.models import RawCase
from cases.acquisition.storage import CaseStorage


class ImprovedStackOverflowFetcher:
    """改进的StackOverflow案例收集器"""
    
    SO_API_BASE = "https://api.stackexchange.com/2.3"
    
    def __init__(self, timeout: int = 15, min_votes: int = 5, min_answers: int = 1):
        self.timeout = timeout
        self.min_votes = min_votes  # 最小投票数
        self.min_answers = min_answers  # 最小答案数
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def search_high_quality_questions(self, keyword: str, count: int = 30, 
                                      min_votes: int = None, 
                                      min_answers: int = None,
                                      has_accepted_answer: bool = True) -> List[Dict]:
        """
        搜索高质量问题
        
        Args:
            keyword: 搜索关键词
            count: 返回结果数量
            min_votes: 最小投票数
            min_answers: 最小答案数
            has_accepted_answer: 是否必须有接受答案
        """
        min_votes = min_votes or self.min_votes
        min_answers = min_answers or self.min_answers
        
        try:
            # 构建搜索URL
            search_url = (
                f"{self.SO_API_BASE}/search/advanced"
                f"?order=desc&sort=votes&q={keyword}"
                f"&site=stackoverflow&tagged=linux-kernel"
                f"&pagesize={min(count * 2, 100)}"  # 获取更多结果以便筛选
                f"&filter=!9_bDDxJY5"
            )
            
            print(f"搜索关键词: {keyword}")
            print(f"  最小投票数: {min_votes}")
            print(f"  最小答案数: {min_answers}")
            print(f"  必须有接受答案: {has_accepted_answer}")
            
            response = requests.get(search_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            # 筛选高质量问题
            high_quality_questions = []
            for item in data.get("items", []):
                # 检查投票数
                if item.get("score", 0) < min_votes:
                    continue
                
                # 检查答案数
                if item.get("answer_count", 0) < min_answers:
                    continue
                
                # 检查是否有接受答案
                if has_accepted_answer and not item.get("accepted_answer_id"):
                    continue
                
                high_quality_questions.append({
                    "question_id": item["question_id"],
                    "title": item.get("title", ""),
                    "score": item.get("score", 0),
                    "answer_count": item.get("answer_count", 0),
                    "view_count": item.get("view_count", 0),
                    "tags": item.get("tags", []),
                    "link": item.get("link", ""),
                    "accepted_answer_id": item.get("accepted_answer_id")
                })
                
                if len(high_quality_questions) >= count:
                    break
            
            print(f"  找到 {len(high_quality_questions)} 个高质量问题")
            return high_quality_questions
            
        except Exception as e:
            print(f"  ✗ 搜索失败: {e}")
            return []
    
    def fetch_question_with_answer(self, question_id: int) -> Optional[Dict]:
        """获取问题及其接受答案的完整内容"""
        try:
            # 获取问题详情
            q_url = (
                f"{self.SO_API_BASE}/questions/{question_id}"
                f"?site=stackoverflow&filter=!9_bDDxJY5"
            )
            q_res = requests.get(q_url, headers=self.headers, timeout=self.timeout)
            q_res.raise_for_status()
            q_data = q_res.json()
            
            if not q_data.get("items"):
                return None
            
            question = q_data["items"][0]
            
            # 获取接受答案
            answer_body = ""
            if question.get("accepted_answer_id"):
                a_url = (
                    f"{self.SO_API_BASE}/answers/{question['accepted_answer_id']}"
                    f"?site=stackoverflow&filter=!9_bDDxJY5"
                )
                a_res = requests.get(a_url, headers=self.headers, timeout=self.timeout)
                if a_res.status_code == 200:
                    a_data = a_res.json()
                    if a_data.get("items"):
                        answer_body = a_data["items"][0].get("body", "")
            
            return {
                "question": question,
                "answer": answer_body
            }
            
        except Exception as e:
            print(f"  ✗ 获取问题 {question_id} 失败: {e}")
            return None
    
    def collect_cases(self, keywords: List[str], count_per_keyword: int = 30) -> List[Dict]:
        """
        批量收集案例
        
        Args:
            keywords: 关键词列表
            count_per_keyword: 每个关键词收集的案例数
        """
        all_cases = []
        total_collected = 0
        
        print("\n" + "=" * 70)
        print("开始收集StackOverflow高质量案例")
        print("=" * 70)
        print()
        
        for keyword in keywords:
            print(f"\n处理关键词: {keyword}")
            print("-" * 70)
            
            # 搜索高质量问题
            questions = self.search_high_quality_questions(
                keyword=keyword,
                count=count_per_keyword,
                min_votes=5,
                min_answers=1,
                has_accepted_answer=True
            )
            
            # 获取每个问题的详细内容
            for i, q in enumerate(questions, 1):
                print(f"  [{i}/{len(questions)}] 获取问题 ID={q['question_id']}")
                print(f"    标题: {q['title'][:60]}...")
                print(f"    投票: {q['score']}, 答案: {q['answer_count']}, 浏览: {q['view_count']}")
                
                # 获取完整内容
                content = self.fetch_question_with_answer(q['question_id'])
                
                if content:
                    case = {
                        "source": "stackoverflow",
                        "source_id": str(q['question_id']),
                        "url": q['link'],
                        "title": q['title'],
                        "content": content,
                        "metadata": {
                            "score": q['score'],
                            "answer_count": q['answer_count'],
                            "view_count": q['view_count'],
                            "tags": q['tags']
                        }
                    }
                    all_cases.append(case)
                    total_collected += 1
                    print(f"    ✓ 成功收集")
                else:
                    print(f"    ✗ 获取失败")
                
                # 延迟避免API限制
                time.sleep(1)
            
            # 关键词之间增加延迟
            time.sleep(2)
        
        print("\n" + "=" * 70)
        print(f"收集完成！")
        print(f"总共收集: {total_collected} 个案例")
        print("=" * 70)
        
        return all_cases


def main():
    """主函数"""
    # 定义搜索关键词
    keywords = [
        "kernel panic",
        "kernel oops",
        "kernel deadlock",
        "kernel memory leak",
        "kernel module error",
        "device driver crash",
        "linux kernel development",
        "kernel null pointer",
        "kernel page fault",
        "kernel interrupt"
    ]
    
    # 创建收集器
    fetcher = ImprovedStackOverflowFetcher(
        min_votes=5,
        min_answers=1
    )
    
    # 收集案例
    cases = fetcher.collect_cases(
        keywords=keywords,
        count_per_keyword=30
    )
    
    # 保存到数据库
    if cases:
        print("\n保存案例到数据库...")
        storage = CaseStorage()
        
        saved_count = 0
        for case in cases:
            try:
                # 构建存储数据
                case_data = {
                    "source": case["source"],
                    "source_id": case["source_id"],
                    "url": case["url"],
                    "title": case["title"],
                    "content": json.dumps(case["content"]),
                    "raw_content": case["content"]["question"].get("body", ""),
                    "metadata": case["metadata"]
                }
                
                # 存储
                result = storage.store(case_data)
                if result.get("success"):
                    saved_count += 1
                    
            except Exception as e:
                print(f"  ✗ 保存案例失败: {e}")
        
        print(f"\n✓ 成功保存 {saved_count}/{len(cases)} 个案例")


if __name__ == "__main__":
    main()