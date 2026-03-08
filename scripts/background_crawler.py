#!/usr/bin/env python
"""
后台爬取工具 - 24小时持续运行，直到爬取到设定数量的案例
默认目标：2000个案例
支持：
- 后台运行（nohup或systemd）
- 定时调度（每6小时运行一次）
- 进度跟踪
- 错误重试
- 优雅退出
"""

import os
import sys
import time
import signal
import logging
import argparse
from datetime import datetime
from typing import Optional

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')

import django
django.setup()

from django.utils import timezone
from cases.models import RawCase
from cases.acquisition import (
    StackOverflowFetcher, CSDNFetcher, ZhihuFetcher,
    ContentCleaner
)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BackgroundCrawler:
    """后台爬取工具"""
    
    DEFAULT_TARGET = 2000
    DEFAULT_INTERVAL = 6 * 60 * 60  # 6小时
    DEFAULT_BATCH_SIZE = 50
    
    KERNEL_KEYWORDS_EN = [
        "linux kernel panic",
        "kernel oops",
        "kernel deadlock",
        "kernel null pointer dereference",
        "kernel OOM",
        "kernel page allocation failure",
        "kernel memory leak",
        "kernel crash",
        "kernel spinlock",
        "kernel interrupt",
    ]
    
    KERNEL_KEYWORDS_CN = [
        "内核 panic",
        "内核 oops",
        "内核死锁",
        "内核空指针",
        "内核 OOM",
        "内核页分配失败",
        "内核内存泄漏",
        "内核崩溃",
        "内核自旋锁",
        "内核中断",
    ]
    
    def __init__(
        self,
        target_count: int = DEFAULT_TARGET,
        interval: int = DEFAULT_INTERVAL,
        batch_size: int = DEFAULT_BATCH_SIZE,
        sources: list = None
    ):
        self.target_count = target_count
        self.interval = interval
        self.batch_size = batch_size
        self.sources = sources or ['stackoverflow', 'csdn', 'zhihu']
        
        self.so_fetcher = StackOverflowFetcher()
        self.csdn_fetcher = CSDNFetcher()
        self.zhihu_fetcher = ZhihuFetcher()
        self.cleaner = ContentCleaner()
        
        self._running = True
        self._shutdown_requested = False
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"初始化爬取工具 - 目标: {target_count}个案例, 间隔: {interval/3600:.1f}小时")
    
    def _signal_handler(self, signum, frame):
        """信号处理器 - 优雅退出"""
        logger.info(f"收到退出信号 {signum}, 准备优雅退出...")
        self._shutdown_requested = True
    
    def get_current_count(self) -> int:
        """获取当前原始案例数量"""
        return RawCase.objects.count()
    
    def get_remaining_count(self) -> int:
        """获取还需要爬取的数量"""
        return max(0, self.target_count - self.get_current_count())
    
    def save_raw_case(self, content: str, source: str, url: str, source_id: str = '') -> bool:
        """保存原始案例到数据库"""
        if not content or len(content.strip()) < 100:
            return False
        
        try:
            if RawCase.objects.filter(source_url=url).exists():
                logger.debug(f"URL已存在，跳过: {url}")
                return False
            
            RawCase.objects.create(
                raw_content=content,
                source=source,
                source_url=url,
                source_id=source_id
            )
            return True
        except Exception as e:
            logger.error(f"保存原始案例失败: {e}")
            return False
    
    def crawl_stackoverflow(self, keyword: str, count: int) -> int:
        """从StackOverflow爬取"""
        saved = 0
        try:
            urls = self.so_fetcher.search(keyword, count=count)
            logger.info(f"StackOverflow搜索 '{keyword}': 找到 {len(urls)} 个结果")
            
            for url in urls:
                if self._shutdown_requested:
                    break
                
                try:
                    content = self.so_fetcher.fetch(url)
                    if content:
                        source_id = url.split('/questions/')[1].split('/')[0] if '/questions/' in url else ''
                        if self.save_raw_case(content, 'stackoverflow', url, source_id):
                            saved += 1
                            logger.info(f"已保存 StackOverflow 案例: {url}")
                    
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"爬取StackOverflow失败 {url}: {e}")
                
                if saved >= count:
                    break
        except Exception as e:
            logger.error(f"StackOverflow爬取异常: {e}")
        
        return saved
    
    def crawl_csdn(self, keyword: str, count: int) -> int:
        """从CSDN爬取"""
        saved = 0
        try:
            urls = self.csdn_fetcher.search(keyword, count=count)
            logger.info(f"CSDN搜索 '{keyword}': 找到 {len(urls)} 个结果")
            
            for url in urls:
                if self._shutdown_requested:
                    break
                
                try:
                    content = self.csdn_fetcher.fetch(url)
                    if content:
                        source_id = url.split('/article/details/')[1].split('/')[0] if '/article/details/' in url else ''
                        if self.save_raw_case(content, 'csdn', url, source_id):
                            saved += 1
                            logger.info(f"已保存 CSDN 案例: {url}")
                    
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"爬取CSDN失败 {url}: {e}")
                
                if saved >= count:
                    break
        except Exception as e:
            logger.error(f"CSDN爬取异常: {e}")
        
        return saved
    
    def crawl_zhihu(self, keyword: str, count: int) -> int:
        """从知乎爬取"""
        saved = 0
        try:
            urls = self.zhihu_fetcher.search(keyword, count=count)
            logger.info(f"知乎搜索 '{keyword}': 找到 {len(urls)} 个结果")
            
            for url in urls:
                if self._shutdown_requested:
                    break
                
                try:
                    content = self.zhihu_fetcher.fetch(url)
                    if content:
                        source_id = ''
                        if '/question/' in url:
                            source_id = url.split('/question/')[1].split('/')[0]
                        elif '/p/' in url:
                            source_id = url.split('/p/')[1].split('/')[0]
                        
                        if self.save_raw_case(content, 'zhihu', url, source_id):
                            saved += 1
                            logger.info(f"已保存 知乎 案例: {url}")
                    
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"爬取知乎失败 {url}: {e}")
                
                if saved >= count:
                    break
        except Exception as e:
            logger.error(f"知乎爬取异常: {e}")
        
        return saved
    
    def run_once(self) -> dict:
        """执行一次爬取"""
        results = {
            'stackoverflow': 0,
            'csdn': 0,
            'zhihu': 0,
            'total': 0,
            'errors': []
        }
        
        remaining = self.get_remaining_count()
        if remaining <= 0:
            logger.info("已达到目标数量，无需继续爬取")
            return results
        
        per_source = min(self.batch_size, remaining // len(self.sources) + 1)
        
        for i, keyword_en in enumerate(self.KERNEL_KEYWORDS_EN):
            if self._shutdown_requested:
                break
            
            keyword_cn = self.KERNEL_KEYWORDS_CN[i] if i < len(self.KERNEL_KEYWORDS_CN) else keyword_en
            
            if 'stackoverflow' in self.sources:
                count = min(per_source // 3 + 1, 10)
                saved = self.crawl_stackoverflow(keyword_en, count)
                results['stackoverflow'] += saved
                results['total'] += saved
            
            if 'csdn' in self.sources and not self._shutdown_requested:
                count = min(per_source // 3 + 1, 10)
                saved = self.crawl_csdn(keyword_cn, count)
                results['csdn'] += saved
                results['total'] += saved
            
            if 'zhihu' in self.sources and not self._shutdown_requested:
                count = min(per_source // 3 + 1, 10)
                saved = self.crawl_zhihu(keyword_cn, count)
                results['zhihu'] += saved
                results['total'] += saved
            
            if results['total'] >= remaining:
                break
        
        return results
    
    def run(self):
        """持续运行爬取"""
        logger.info("=" * 60)
        logger.info("后台爬取工具启动")
        logger.info(f"目标数量: {self.target_count}")
        logger.info(f"当前数量: {self.get_current_count()}")
        logger.info(f"运行间隔: {self.interval / 3600:.1f} 小时")
        logger.info("=" * 60)
        
        iteration = 0
        while self._running and not self._shutdown_requested:
            iteration += 1
            current_count = self.get_current_count()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"第 {iteration} 轮爬取开始 - 当前: {current_count}/{self.target_count}")
            logger.info(f"{'='*60}")
            
            if current_count >= self.target_count:
                logger.info(f"✓ 已达到目标数量 {self.target_count}，爬取完成！")
                break
            
            start_time = time.time()
            results = self.run_once()
            elapsed = time.time() - start_time
            
            logger.info(f"\n本轮爬取完成:")
            logger.info(f"  - StackOverflow: {results['stackoverflow']} 个")
            logger.info(f"  - CSDN: {results['csdn']} 个")
            logger.info(f"  - 知乎: {results['zhihu']} 个")
            logger.info(f"  - 总计: {results['total']} 个")
            logger.info(f"  - 耗时: {elapsed:.1f} 秒")
            logger.info(f"  - 当前进度: {self.get_current_count()}/{self.target_count}")
            
            if self._shutdown_requested:
                logger.info("收到退出信号，停止爬取")
                break
            
            if self.get_current_count() < self.target_count:
                logger.info(f"\n等待 {self.interval / 3600:.1f} 小时后继续...")
                for _ in range(int(self.interval)):
                    if self._shutdown_requested:
                        break
                    time.sleep(1)
        
        logger.info("\n" + "=" * 60)
        logger.info("爬取工具已停止")
        logger.info(f"最终数量: {self.get_current_count()}/{self.target_count}")
        logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='后台爬取工具')
    parser.add_argument('--target', type=int, default=2000, help='目标案例数量 (默认: 2000)')
    parser.add_argument('--interval', type=int, default=21600, help='爬取间隔(秒) (默认: 21600=6小时)')
    parser.add_argument('--batch', type=int, default=50, help='每轮爬取批次大小 (默认: 50)')
    parser.add_argument('--sources', type=str, default='stackoverflow,csdn,zhihu', help='数据源 (默认: stackoverflow,csdn,zhihu)')
    parser.add_argument('--once', action='store_true', help='只运行一次')
    
    args = parser.parse_args()
    
    sources = [s.strip() for s in args.sources.split(',')]
    
    crawler = BackgroundCrawler(
        target_count=args.target,
        interval=args.interval,
        batch_size=args.batch,
        sources=sources
    )
    
    if args.once:
        results = crawler.run_once()
        print(f"\n爬取完成:")
        print(f"  - StackOverflow: {results['stackoverflow']} 个")
        print(f"  - CSDN: {results['csdn']} 个")
        print(f"  - 知乎: {results['zhihu']} 个")
        print(f"  - 总计: {results['total']} 个")
    else:
        crawler.run()


if __name__ == '__main__':
    main()