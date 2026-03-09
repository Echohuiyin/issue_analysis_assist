#!/usr/bin/env python3
"""
原始案例获取程序
从各数据源获取原始案例，存储到RawCase表
包含延迟机制以避免被网站拒绝访问
"""
import os
import sys
import time
import random
import hashlib
import django
from datetime import datetime

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
django.setup()

from cases.models import RawCase
from cases.acquisition.fetchers import (
    StackOverflowFetcher, 
    CSDNFetcher, 
    ZhihuFetcher, 
    JuejinFetcher
)
from cases.acquisition.cleaner import content_cleaner


class RawCaseFetcher:
    """原始案例获取器"""
    
    # 搜索关键词
    KEYWORDS = [
        "kernel panic",
        "kernel oops", 
        "kernel deadlock",
        "kernel null pointer",
        "kernel OOM",
        "kernel memory leak",
        "kernel crash",
        "kernel driver error",
        "内核 panic",
        "内核死锁",
        "内核崩溃",
        "内核内存泄漏",
        "内核驱动错误",
    ]
    
    # 延迟配置（秒）
    DELAY_CONFIG = {
        'min_delay': 2,      # 最小延迟
        'max_delay': 5,      # 最大延迟
        'batch_delay': 10,   # 批次间延迟
        'source_delay': 30,  # 切换数据源延迟
    }
    
    def __init__(self):
        self.so_fetcher = StackOverflowFetcher()
        self.csdn_fetcher = CSDNFetcher()
        self.zhihu_fetcher = ZhihuFetcher()
        self.juejin_fetcher = JuejinFetcher()
        
        self.stats = {
            'total_fetched': 0,
            'total_saved': 0,
            'total_duplicates': 0,
            'total_errors': 0,
        }
    
    def _compute_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _extract_from_html(self, html: str, source: str) -> dict:
        """从HTML中提取标题和内容"""
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 提取标题
            title = ''
            if source == 'csdn':
                title_tag = soup.find('h1', class_='title-article') or soup.find('title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
            elif source == 'zhihu':
                title_tag = soup.find('h1', class_='QuestionHeader-title') or soup.find('title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
            elif source == 'juejin':
                title_tag = soup.find('h1', class_='article-title') or soup.find('title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
            else:
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
            
            # 提取正文内容
            content_text = ''
            if source == 'csdn':
                content_tag = soup.find('article') or soup.find('div', id='content_views')
                if content_tag:
                    content_text = content_tag.get_text(separator='\n', strip=True)
            elif source == 'zhihu':
                content_tag = soup.find('div', class_='RichContent-inner') or soup.find('div', class_='QuestionRichText')
                if content_tag:
                    content_text = content_tag.get_text(separator='\n', strip=True)
            elif source == 'juejin':
                content_tag = soup.find('div', class_='article-content') or soup.find('article')
                if content_tag:
                    content_text = content_tag.get_text(separator='\n', strip=True)
            else:
                # 移除script和style标签
                for script in soup(["script", "style"]):
                    script.decompose()
                content_text = soup.get_text(separator='\n', strip=True)
            
            return {
                'title': title,
                'content': content_text,
                'html': html
            }
            
        except Exception as e:
            print(f"  [警告] HTML解析失败: {e}")
            return {
                'title': '',
                'content': html,
                'html': html
            }
    
    def _random_delay(self, delay_type: str = 'normal'):
        """随机延迟，避免被网站拒绝访问"""
        if delay_type == 'normal':
            delay = random.uniform(
                self.DELAY_CONFIG['min_delay'],
                self.DELAY_CONFIG['max_delay']
            )
        elif delay_type == 'batch':
            delay = self.DELAY_CONFIG['batch_delay']
        elif delay_type == 'source':
            delay = self.DELAY_CONFIG['source_delay']
        else:
            delay = 2
        
        time.sleep(delay)
    
    def _save_raw_case(self, source: str, source_id: str, url: str, 
                       title: str, content: str, html: str = '') -> bool:
        """保存原始案例到数据库"""
        try:
            # 计算内容哈希
            content_hash = self._compute_hash(f"{title}\n{content}")
            
            # 检查是否已存在
            if RawCase.objects.filter(content_hash=content_hash).exists():
                self.stats['total_duplicates'] += 1
                print(f"  [重复] {title[:50]}")
                return False
            
            # 创建原始案例
            RawCase.objects.create(
                source=source,
                source_id=source_id,
                url=url,
                raw_title=title[:500],
                raw_content=content,
                raw_html=html,
                content_hash=content_hash,
                status='pending',
            )
            
            self.stats['total_saved'] += 1
            print(f"  [保存] {title[:50]}")
            return True
            
        except Exception as e:
            self.stats['total_errors'] += 1
            print(f"  [错误] 保存失败: {e}")
            return False
    
    def fetch_from_stackoverflow(self, keyword: str, count: int = 10):
        """从StackOverflow获取案例"""
        print(f"\n{'='*60}")
        print(f"从StackOverflow搜索: {keyword} (最多{count}个)")
        print(f"{'='*60}")
        
        try:
            urls = self.so_fetcher.search(keyword, count=count)
            
            for i, url in enumerate(urls, 1):
                print(f"\n[{i}/{len(urls)}] 获取: {url}")
                
                try:
                    # 获取内容
                    content_str = self.so_fetcher.fetch(url)
                    
                    if content_str:
                        # 解析JSON
                        import json
                        content = json.loads(content_str)
                        
                        # 提取source_id
                        source_id = ''
                        if '/questions/' in url:
                            source_id = url.split('/questions/')[1].split('?')[0]
                        
                        # 提取问题和答案
                        question = content.get('question', {})
                        answer = content.get('answer', '')
                        
                        # 组合标题和内容
                        title = question.get('title', '')
                        body = question.get('body', '')
                        if answer:
                            body += f"\n\n--- Accepted Answer ---\n{answer}"
                        
                        # 保存
                        self._save_raw_case(
                            source='stackoverflow',
                            source_id=source_id,
                            url=question.get('link', url),
                            title=title,
                            content=body,
                            html=body,
                        )
                        
                        self.stats['total_fetched'] += 1
                        
                except Exception as e:
                    print(f"  [错误] 获取失败: {e}")
                    self.stats['total_errors'] += 1
                
                # 随机延迟
                if i < len(urls):
                    self._random_delay('normal')
            
            # 批次延迟
            self._random_delay('batch')
            
        except Exception as e:
            print(f"[错误] StackOverflow搜索失败: {e}")
    
    def fetch_from_csdn(self, keyword: str, count: int = 10):
        """从CSDN获取案例"""
        print(f"\n{'='*60}")
        print(f"从CSDN搜索: {keyword} (最多{count}个)")
        print(f"{'='*60}")
        
        try:
            urls = self.csdn_fetcher.search(keyword, count=count)
            
            for i, url in enumerate(urls, 1):
                print(f"\n[{i}/{len(urls)}] 获取: {url}")
                
                try:
                    # 获取内容
                    html_content = self.csdn_fetcher.fetch(url)
                    
                    if html_content:
                        # 提取source_id
                        source_id = ''
                        if '/article/details/' in url:
                            source_id = url.split('/article/details/')[1].split('?')[0]
                        
                        # 从HTML中提取标题和内容
                        extracted = self._extract_from_html(html_content, 'csdn')
                        
                        # 保存
                        self._save_raw_case(
                            source='csdn',
                            source_id=source_id,
                            url=url,
                            title=extracted['title'],
                            content=extracted['content'],
                            html=extracted['html'],
                        )
                        
                        self.stats['total_fetched'] += 1
                        
                except Exception as e:
                    print(f"  [错误] 获取失败: {e}")
                    self.stats['total_errors'] += 1
                
                # 随机延迟（CSDN需要更长延迟）
                if i < len(urls):
                    time.sleep(random.uniform(3, 6))
            
            # 批次延迟
            time.sleep(15)
            
        except Exception as e:
            print(f"[错误] CSDN搜索失败: {e}")
    
    def fetch_from_zhihu(self, keyword: str, count: int = 10):
        """从知乎获取案例"""
        print(f"\n{'='*60}")
        print(f"从知乎搜索: {keyword} (最多{count}个)")
        print(f"{'='*60}")
        
        try:
            urls = self.zhihu_fetcher.search(keyword, count=count)
            
            for i, url in enumerate(urls, 1):
                print(f"\n[{i}/{len(urls)}] 获取: {url}")
                
                try:
                    # 获取内容
                    html_content = self.zhihu_fetcher.fetch(url)
                    
                    if html_content:
                        # 提取source_id
                        source_id = ''
                        if '/question/' in url:
                            source_id = url.split('/question/')[1].split('/')[0]
                        
                        # 从HTML中提取标题和内容
                        extracted = self._extract_from_html(html_content, 'zhihu')
                        
                        # 保存
                        self._save_raw_case(
                            source='zhihu',
                            source_id=source_id,
                            url=url,
                            title=extracted['title'],
                            content=extracted['content'],
                            html=extracted['html'],
                        )
                        
                        self.stats['total_fetched'] += 1
                        
                except Exception as e:
                    print(f"  [错误] 获取失败: {e}")
                    self.stats['total_errors'] += 1
                
                # 随机延迟
                if i < len(urls):
                    self._random_delay('normal')
            
            # 批次延迟
            self._random_delay('batch')
            
        except Exception as e:
            print(f"[错误] 知乎搜索失败: {e}")
    
    def fetch_from_juejin(self, keyword: str, count: int = 10):
        """从掘金获取案例"""
        print(f"\n{'='*60}")
        print(f"从掘金搜索: {keyword} (最多{count}个)")
        print(f"{'='*60}")
        
        try:
            urls = self.juejin_fetcher.search(keyword, count=count)
            
            for i, url in enumerate(urls, 1):
                print(f"\n[{i}/{len(urls)}] 获取: {url}")
                
                try:
                    # 获取内容
                    html_content = self.juejin_fetcher.fetch(url)
                    
                    if html_content:
                        # 提取source_id
                        source_id = ''
                        if '/post/' in url:
                            source_id = url.split('/post/')[1].split('?')[0]
                        
                        # 从HTML中提取标题和内容
                        extracted = self._extract_from_html(html_content, 'juejin')
                        
                        # 保存
                        self._save_raw_case(
                            source='juejin',
                            source_id=source_id,
                            url=url,
                            title=extracted['title'],
                            content=extracted['content'],
                            html=extracted['html'],
                        )
                        
                        self.stats['total_fetched'] += 1
                        
                except Exception as e:
                    print(f"  [错误] 获取失败: {e}")
                    self.stats['total_errors'] += 1
                
                # 随机延迟
                if i < len(urls):
                    self._random_delay('normal')
            
            # 批次延迟
            self._random_delay('batch')
            
        except Exception as e:
            print(f"[错误] 掘金搜索失败: {e}")
    
    def run(self, keywords: list = None, count_per_keyword: int = 10, 
            sources: list = None, continuous: bool = False, 
            interval_minutes: int = 30):
        """
        运行案例获取
        
        Args:
            keywords: 搜索关键词列表
            count_per_keyword: 每个关键词获取的数量
            sources: 数据源列表 ['stackoverflow', 'csdn', 'zhihu', 'juejin']
            continuous: 是否持续运行
            interval_minutes: 持续运行时的间隔时间（分钟）
        """
        if keywords is None:
            keywords = self.KEYWORDS
        
        if sources is None:
            sources = ['stackoverflow', 'csdn', 'zhihu', 'juejin']
        
        round_num = 1
        
        while True:
            print(f"\n{'#'*60}")
            print(f"# 第 {round_num} 轮获取开始")
            print(f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'#'*60}")
            
            # 重置统计
            self.stats = {
                'total_fetched': 0,
                'total_saved': 0,
                'total_duplicates': 0,
                'total_errors': 0,
            }
            
            # 遍历关键词和数据源
            for keyword in keywords:
                if 'stackoverflow' in sources:
                    self.fetch_from_stackoverflow(keyword, count_per_keyword)
                    self._random_delay('source')
                
                if 'csdn' in sources:
                    self.fetch_from_csdn(keyword, count_per_keyword)
                    self._random_delay('source')
                
                if 'zhihu' in sources:
                    self.fetch_from_zhihu(keyword, count_per_keyword)
                    self._random_delay('source')
                
                if 'juejin' in sources:
                    self.fetch_from_juejin(keyword, count_per_keyword)
                    self._random_delay('source')
            
            # 打印统计
            print(f"\n{'='*60}")
            print(f"第 {round_num} 轮获取完成")
            print(f"统计:")
            print(f"  - 获取总数: {self.stats['total_fetched']}")
            print(f"  - 保存成功: {self.stats['total_saved']}")
            print(f"  - 重复案例: {self.stats['total_duplicates']}")
            print(f"  - 错误数量: {self.stats['total_errors']}")
            print(f"  - 数据库中待处理: {RawCase.objects.filter(status='pending').count()}")
            print(f"{'='*60}")
            
            # 如果不是持续运行，则退出
            if not continuous:
                break
            
            # 等待下一轮
            print(f"\n等待 {interval_minutes} 分钟后开始下一轮...")
            time.sleep(interval_minutes * 60)
            round_num += 1


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='原始案例获取程序')
    parser.add_argument('--keywords', nargs='+', help='搜索关键词')
    parser.add_argument('--count', type=int, default=10, help='每个关键词获取的数量')
    parser.add_argument('--sources', nargs='+', 
                        choices=['stackoverflow', 'csdn', 'zhihu', 'juejin'],
                        help='数据源')
    parser.add_argument('--continuous', action='store_true', help='持续运行')
    parser.add_argument('--interval', type=int, default=30, help='持续运行间隔（分钟）')
    
    args = parser.parse_args()
    
    fetcher = RawCaseFetcher()
    fetcher.run(
        keywords=args.keywords,
        count_per_keyword=args.count,
        sources=args.sources,
        continuous=args.continuous,
        interval_minutes=args.interval,
    )


if __name__ == '__main__':
    main()