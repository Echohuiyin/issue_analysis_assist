#!/usr/bin/env python
"""
案例处理脚本 - 从原始案例表读取，调用LLM解析，打分过滤，存入训练集
支持：
- 批量处理
- 质量过滤（分数阈值）
- 训练集/测试集划分
- 进度跟踪
- 错误重试
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, Optional, List
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')

import django
django.setup()

from django.utils import timezone
from django.db import transaction
from cases.models import RawCase, TrainingCase, TestCase
from cases.acquisition import (
    LLMParser, CaseValidator, ModuleClassifier,
    get_llm
)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('case_processor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CaseProcessor:
    """案例处理器"""
    
    DEFAULT_QUALITY_THRESHOLD = 75.0
    DEFAULT_BATCH_SIZE = 10
    DEFAULT_TEST_RATIO = 0.1
    
    def __init__(
        self,
        quality_threshold: float = DEFAULT_QUALITY_THRESHOLD,
        batch_size: int = DEFAULT_BATCH_SIZE,
        test_ratio: float = DEFAULT_TEST_RATIO,
        llm_type: str = "auto"
    ):
        self.quality_threshold = quality_threshold
        self.batch_size = batch_size
        self.test_ratio = test_ratio
        
        self.llm_parser = LLMParser(llm_type=llm_type)
        self.validator = CaseValidator()
        self.classifier = ModuleClassifier()
        
        logger.info(f"初始化案例处理器")
        logger.info(f"  - 质量阈值: {quality_threshold}")
        logger.info(f"  - 批次大小: {batch_size}")
        logger.info(f"  - 测试集比例: {test_ratio*100:.1f}%")
    
    def get_unprocessed_count(self) -> int:
        """获取未处理的原始案例数量"""
        return RawCase.objects.filter(processed=False).count()
    
    def get_unprocessed_cases(self, limit: int = None) -> List[RawCase]:
        """获取未处理的原始案例"""
        queryset = RawCase.objects.filter(processed=False).order_by('id')
        if limit:
            queryset = queryset[:limit]
        return list(queryset)
    
    def parse_raw_case(self, raw_case: RawCase) -> Optional[Dict]:
        """解析原始案例"""
        try:
            parsed_data = self.llm_parser.parse(raw_case.raw_content, use_llm=True)
            
            if not parsed_data:
                logger.warning(f"解析失败: RawCase-{raw_case.id}")
                return None
            
            parsed_data['source'] = raw_case.source
            parsed_data['source_url'] = raw_case.source_url
            parsed_data['raw_case_id'] = raw_case.id
            
            if not parsed_data.get('module') or parsed_data.get('module') == 'other':
                classify_text = f"{parsed_data.get('title', '')}\n{parsed_data.get('phenomenon', '')}\n{parsed_data.get('root_cause', '')}"
                parsed_data['module'] = self.classifier.classify_module(classify_text)
            
            return parsed_data
        except Exception as e:
            logger.error(f"解析异常 RawCase-{raw_case.id}: {e}")
            return None
    
    def validate_case(self, parsed_data: Dict) -> Dict:
        """验证案例质量"""
        return self.validator.validate(parsed_data)
    
    def save_to_dataset(self, parsed_data: Dict, raw_case: RawCase, is_test: bool = False) -> bool:
        """保存到训练集或测试集"""
        try:
            model_class = TestCase if is_test else TrainingCase
            
            case = model_class(
                title=parsed_data.get('title', '')[:500],
                phenomenon=parsed_data.get('phenomenon', ''),
                key_logs=parsed_data.get('key_logs', ''),
                environment=parsed_data.get('environment', ''),
                root_cause=parsed_data.get('root_cause', ''),
                analysis_process=parsed_data.get('analysis_process', ''),
                solution=parsed_data.get('solution', ''),
                related_code=parsed_data.get('related_code', ''),
                fix_code=parsed_data.get('fix_code', ''),
                module=parsed_data.get('module', 'other'),
                tags=parsed_data.get('tags', []),
                source=parsed_data.get('source', ''),
                source_url=parsed_data.get('source_url', ''),
                raw_case=raw_case,
                quality_score=parsed_data.get('quality_score', 0.0),
                confidence=parsed_data.get('confidence', 0.0)
            )
            
            case.save()
            dataset_name = "测试集" if is_test else "训练集"
            logger.info(f"已保存到{dataset_name}: {case.title[:50]}")
            return True
        except Exception as e:
            logger.error(f"保存失败: {e}")
            return False
    
    def process_case(self, raw_case: RawCase) -> Dict:
        """处理单个案例"""
        result = {
            'raw_case_id': raw_case.id,
            'success': False,
            'saved_to': None,
            'quality_score': 0,
            'error': None
        }
        
        try:
            parsed_data = self.parse_raw_case(raw_case)
            if not parsed_data:
                result['error'] = "解析失败"
                return result
            
            validation_result = self.validate_case(parsed_data)
            quality_score = validation_result.get('quality_score', 0)
            result['quality_score'] = quality_score
            
            parsed_data['quality_score'] = quality_score
            parsed_data['confidence'] = parsed_data.get('confidence', 0.5)
            
            if quality_score < self.quality_threshold:
                logger.info(f"质量分数 {quality_score:.1f} < {self.quality_threshold}, 跳过: {parsed_data.get('title', '')[:50]}")
                result['error'] = f"质量分数过低: {quality_score:.1f}"
                return result
            
            is_test = random.random() < self.test_ratio
            
            if self.save_to_dataset(parsed_data, raw_case, is_test):
                result['success'] = True
                result['saved_to'] = 'test' if is_test else 'training'
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"处理异常 RawCase-{raw_case.id}: {e}")
        
        return result
    
    def mark_as_processed(self, raw_case: RawCase, success: bool = True):
        """标记为已处理"""
        raw_case.processed = True
        raw_case.processed_at = timezone.now()
        raw_case.save(update_fields=['processed', 'processed_at'])
    
    def process_batch(self, batch_size: int = None) -> Dict:
        """处理一批案例"""
        batch_size = batch_size or self.batch_size
        
        stats = {
            'total': 0,
            'success': 0,
            'training': 0,
            'test': 0,
            'low_quality': 0,
            'parse_failed': 0,
            'errors': []
        }
        
        raw_cases = self.get_unprocessed_cases(limit=batch_size)
        stats['total'] = len(raw_cases)
        
        if not raw_cases:
            logger.info("没有待处理的原始案例")
            return stats
        
        logger.info(f"开始处理 {len(raw_cases)} 个原始案例...")
        
        for i, raw_case in enumerate(raw_cases, 1):
            logger.info(f"\n[{i}/{len(raw_cases)}] 处理 RawCase-{raw_case.id} ({raw_case.source})")
            
            result = self.process_case(raw_case)
            
            if result['success']:
                stats['success'] += 1
                if result['saved_to'] == 'test':
                    stats['test'] += 1
                else:
                    stats['training'] += 1
            elif result['error']:
                if '质量分数过低' in result['error']:
                    stats['low_quality'] += 1
                elif '解析失败' in result['error']:
                    stats['parse_failed'] += 1
                else:
                    stats['errors'].append({
                        'raw_case_id': raw_case.id,
                        'error': result['error']
                    })
            
            self.mark_as_processed(raw_case)
            
            time.sleep(0.5)
        
        return stats
    
    def run(self, max_cases: int = None):
        """持续处理案例"""
        logger.info("=" * 60)
        logger.info("案例处理器启动")
        logger.info(f"质量阈值: {self.quality_threshold}")
        logger.info(f"测试集比例: {self.test_ratio*100:.1f}%")
        logger.info("=" * 60)
        
        total_stats = {
            'total': 0,
            'success': 0,
            'training': 0,
            'test': 0,
            'low_quality': 0,
            'parse_failed': 0
        }
        
        iteration = 0
        while True:
            iteration += 1
            unprocessed_count = self.get_unprocessed_count()
            
            if unprocessed_count == 0:
                logger.info("没有待处理的原始案例，处理完成")
                break
            
            if max_cases and total_stats['total'] >= max_cases:
                logger.info(f"已达到最大处理数量 {max_cases}，停止处理")
                break
            
            logger.info(f"\n{'='*60}")
            logger.info(f"第 {iteration} 轮处理 - 待处理: {unprocessed_count}")
            logger.info(f"{'='*60}")
            
            batch_stats = self.process_batch()
            
            for key in ['total', 'success', 'training', 'test', 'low_quality', 'parse_failed']:
                total_stats[key] += batch_stats[key]
            
            logger.info(f"\n本轮统计:")
            logger.info(f"  - 处理: {batch_stats['total']}")
            logger.info(f"  - 成功: {batch_stats['success']}")
            logger.info(f"  - 训练集: {batch_stats['training']}")
            logger.info(f"  - 测试集: {batch_stats['test']}")
            logger.info(f"  - 低质量: {batch_stats['low_quality']}")
            logger.info(f"  - 解析失败: {batch_stats['parse_failed']}")
            
            logger.info(f"\n累计统计:")
            logger.info(f"  - 总处理: {total_stats['total']}")
            logger.info(f"  - 总成功: {total_stats['success']}")
            logger.info(f"  - 训练集总数: {total_stats['training']}")
            logger.info(f"  - 测试集总数: {total_stats['test']}")
        
        logger.info("\n" + "=" * 60)
        logger.info("案例处理完成")
        logger.info(f"最终统计:")
        logger.info(f"  - 总处理: {total_stats['total']}")
        logger.info(f"  - 总成功: {total_stats['success']}")
        logger.info(f"  - 训练集: {total_stats['training']}")
        logger.info(f"  - 测试集: {total_stats['test']}")
        logger.info(f"  - 低质量: {total_stats['low_quality']}")
        logger.info("=" * 60)
        
        return total_stats


def main():
    parser = argparse.ArgumentParser(description='案例处理脚本')
    parser.add_argument('--quality', type=float, default=75.0, help='质量分数阈值 (默认: 75.0)')
    parser.add_argument('--batch', type=int, default=10, help='批次大小 (默认: 10)')
    parser.add_argument('--test-ratio', type=float, default=0.1, help='测试集比例 (默认: 0.1)')
    parser.add_argument('--max', type=int, default=None, help='最大处理数量 (默认: 无限制)')
    parser.add_argument('--llm', type=str, default='auto', help='LLM类型 (默认: auto)')
    parser.add_argument('--once', action='store_true', help='只处理一批')
    
    args = parser.parse_args()
    
    processor = CaseProcessor(
        quality_threshold=args.quality,
        batch_size=args.batch,
        test_ratio=args.test_ratio,
        llm_type=args.llm
    )
    
    if args.once:
        stats = processor.process_batch()
        print(f"\n处理完成:")
        print(f"  - 处理: {stats['total']}")
        print(f"  - 成功: {stats['success']}")
        print(f"  - 训练集: {stats['training']}")
        print(f"  - 测试集: {stats['test']}")
    else:
        processor.run(max_cases=args.max)


if __name__ == '__main__':
    main()