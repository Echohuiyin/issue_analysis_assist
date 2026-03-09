#!/usr/bin/env python3
"""
原始案例处理程序
从RawCase表读取原始案例，使用本地LLM解析成结构化格式，
根据质量分数选择高质量案例插入到TrainingCase或TestCase表
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

from cases.models import RawCase, TrainingCase, TestCase
from cases.acquisition.llm_parser import LLMParser
from cases.acquisition.validators import CaseValidator
from cases.acquisition.vector_service import get_vector_service
from cases.acquisition.classifier import module_classifier


class RawCaseProcessor:
    """原始案例处理器"""
    
    # 质量阈值
    QUALITY_THRESHOLD = 70.0  # 最低质量分数
    CONFIDENCE_THRESHOLD = 0.7  # 最低置信度
    
    # 训练/测试数据分配比例
    TRAINING_RATIO = 0.8  # 80%用于训练，20%用于测试
    
    def __init__(self, llm_type: str = 'ollama', model: str = 'qwen2.5:0.5b'):
        self.llm_parser = LLMParser(llm_type=llm_type, model=model)
        self.validator = CaseValidator()
        self.vector_service = get_vector_service(model=model, llm_type=llm_type)
        
        self.stats = {
            'total_processed': 0,
            'total_success': 0,
            'total_low_quality': 0,
            'total_failed': 0,
            'total_training': 0,
            'total_test': 0,
        }
    
    def _compute_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _classify_to_training_or_test(self) -> str:
        """随机分配到训练集或测试集"""
        return 'training' if random.random() < self.TRAINING_RATIO else 'test'
    
    def _save_structured_case(self, parsed_data: dict, raw_case: RawCase,
                               quality_score: float, confidence: float,
                               target_table: str = 'training') -> bool:
        """保存结构化案例到训练表或测试表"""
        try:
            # 计算内容哈希
            content_parts = [
                parsed_data.get('title', ''),
                parsed_data.get('phenomenon', ''),
                parsed_data.get('root_cause', ''),
                parsed_data.get('solution', '')
            ]
            combined_content = " ".join(filter(None, content_parts))
            content_hash = self._compute_hash(combined_content)
            
            # 生成案例ID
            case_id = f"CASE-{raw_case.raw_id:08d}"
            
            # 生成向量嵌入
            embedding = self.vector_service.generate_embedding(combined_content)
            
            # 分类内核模块
            classification_text = " ".join([
                parsed_data.get('title', ''),
                parsed_data.get('phenomenon', ''),
                parsed_data.get('root_cause', ''),
                parsed_data.get('solution', '')
            ])
            module = module_classifier.classify_module(classification_text)
            
            # 提取内核版本
            import re
            kernel_version = ''
            env_str = parsed_data.get('environment', '')
            match = re.search(r'(?:Linux|kernel)\s*(\d+\.\d+[\.\d]*(?:-[\w.]+)?)', 
                             env_str, re.IGNORECASE)
            if match:
                kernel_version = match.group(1)
            
            # 准备通用字段
            common_fields = {
                'case_id': case_id,
                'raw_case': raw_case,
                'title': parsed_data.get('title', '')[:200],
                'phenomenon': parsed_data.get('phenomenon', ''),
                'key_logs': parsed_data.get('key_logs', ''),
                'environment': parsed_data.get('environment', ''),
                'root_cause': parsed_data.get('root_cause', ''),
                'analysis_process': parsed_data.get('analysis_process', ''),
                'troubleshooting_steps': parsed_data.get('troubleshooting_steps', []),
                'solution': parsed_data.get('solution', ''),
                'prevention': parsed_data.get('prevention', ''),
                'kernel_version': kernel_version[:50],
                'affected_components': parsed_data.get('affected_components', '')[:200],
                'module': module,
                'severity': parsed_data.get('severity', 'Medium'),
                'source': raw_case.source,
                'source_id': raw_case.source_id,
                'url': raw_case.url,
                'tags': parsed_data.get('tags', []),
                'votes': parsed_data.get('votes', 0),
                'answers_count': parsed_data.get('answers_count', 0),
                'quality_score': quality_score,
                'confidence': confidence,
                'embedding': embedding,
                'content_hash': content_hash,
            }
            
            # 根据目标表保存
            if target_table == 'training':
                case = TrainingCase(**common_fields)
                case.save()
                self.stats['total_training'] += 1
                print(f"  [训练集] {case_id}: {common_fields['title'][:50]}")
            else:
                case = TestCase(**common_fields)
                case.save()
                self.stats['total_test'] += 1
                print(f"  [测试集] {case_id}: {common_fields['title'][:50]}")
            
            return True
            
        except Exception as e:
            print(f"  [错误] 保存失败: {e}")
            return False
    
    def process_raw_case(self, raw_case: RawCase) -> dict:
        """处理单个原始案例"""
        result = {
            'success': False,
            'quality_score': 0.0,
            'confidence': 0.0,
            'error': None,
        }
        
        try:
            # 更新状态为处理中
            raw_case.status = 'processing'
            raw_case.save()
            
            print(f"\n处理案例 ID={raw_case.raw_id}: {raw_case.raw_title[:50]}")
            
            # 使用LLM解析
            print(f"  [LLM解析中...]")
            parsed_data = self.llm_parser.parse(
                raw_case.raw_content,
                use_llm=True
            )
            
            if not parsed_data:
                raise ValueError("LLM解析返回空结果")
            
            # 验证质量
            print(f"  [质量验证中...]")
            validation_result = self.validator.validate(parsed_data)
            quality_score = validation_result.get('quality_score', 0)
            
            print(f"  质量分数: {quality_score:.1f}")
            
            # 检查质量阈值
            if quality_score < self.QUALITY_THRESHOLD:
                print(f"  [低质量] 质量分数 {quality_score:.1f} < {self.QUALITY_THRESHOLD}")
                raw_case.status = 'low_quality'
                raw_case.process_error = f"Quality score too low: {quality_score:.1f}"
                raw_case.save()
                
                result['quality_score'] = quality_score
                result['error'] = 'low_quality'
                self.stats['total_low_quality'] += 1
                return result
            
            # 获取置信度
            confidence = parsed_data.get('confidence', 0.5)
            
            # 分配到训练集或测试集
            target_table = self._classify_to_training_or_test()
            
            # 保存结构化案例
            success = self._save_structured_case(
                parsed_data, raw_case, quality_score, confidence, target_table
            )
            
            if success:
                # 更新原始案例状态
                raw_case.status = 'processed'
                raw_case.process_time = datetime.now()
                raw_case.save()
                
                result['success'] = True
                result['quality_score'] = quality_score
                result['confidence'] = confidence
                self.stats['total_success'] += 1
            else:
                raise ValueError("保存结构化案例失败")
            
        except Exception as e:
            error_msg = str(e)
            print(f"  [错误] {error_msg}")
            
            raw_case.status = 'failed'
            raw_case.process_error = error_msg[:500]
            raw_case.save()
            
            result['error'] = error_msg
            self.stats['total_failed'] += 1
        
        return result
    
    def process_batch(self, batch_size: int = 10, delay: float = 2.0):
        """批量处理待处理的原始案例"""
        # 获取待处理的案例
        pending_cases = RawCase.objects.filter(status='pending')[:batch_size]
        
        if not pending_cases.exists():
            print("没有待处理的原始案例")
            return
        
        print(f"\n{'='*60}")
        print(f"开始批量处理 {pending_cases.count()} 个原始案例")
        print(f"{'='*60}")
        
        for i, raw_case in enumerate(pending_cases, 1):
            print(f"\n[{i}/{pending_cases.count()}]")
            
            self.process_raw_case(raw_case)
            self.stats['total_processed'] += 1
            
            # 延迟，避免LLM过载
            if i < pending_cases.count():
                time.sleep(delay)
        
        # 打印统计
        self._print_stats()
    
    def process_all(self, batch_size: int = 10, delay: float = 2.0):
        """处理所有待处理的原始案例"""
        total_pending = RawCase.objects.filter(status='pending').count()
        
        print(f"\n{'#'*60}")
        print(f"# 开始处理所有待处理案例")
        print(f"# 待处理总数: {total_pending}")
        print(f"{'#'*60}")
        
        while True:
            pending_count = RawCase.objects.filter(status='pending').count()
            
            if pending_count == 0:
                print("\n所有案例处理完成！")
                break
            
            print(f"\n剩余待处理: {pending_count}")
            self.process_batch(batch_size, delay)
    
    def _print_stats(self):
        """打印统计信息"""
        print(f"\n{'='*60}")
        print("处理统计:")
        print(f"  - 已处理: {self.stats['total_processed']}")
        print(f"  - 成功: {self.stats['total_success']}")
        print(f"  - 低质量: {self.stats['total_low_quality']}")
        print(f"  - 失败: {self.stats['total_failed']}")
        print(f"  - 训练集: {self.stats['total_training']}")
        print(f"  - 测试集: {self.stats['total_test']}")
        print(f"{'='*60}")
        
        # 数据库统计
        print(f"\n数据库统计:")
        print(f"  - 原始案例总数: {RawCase.objects.count()}")
        print(f"  - 待处理: {RawCase.objects.filter(status='pending').count()}")
        print(f"  - 已处理: {RawCase.objects.filter(status='processed').count()}")
        print(f"  - 低质量: {RawCase.objects.filter(status='low_quality').count()}")
        print(f"  - 失败: {RawCase.objects.filter(status='failed').count()}")
        print(f"  - 训练案例: {TrainingCase.objects.count()}")
        print(f"  - 测试案例: {TestCase.objects.count()}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='原始案例处理程序')
    parser.add_argument('--batch-size', type=int, default=10, 
                        help='每批处理数量')
    parser.add_argument('--delay', type=float, default=2.0,
                        help='处理间隔（秒）')
    parser.add_argument('--all', action='store_true',
                        help='处理所有待处理案例')
    parser.add_argument('--llm-type', default='ollama',
                        choices=['ollama', 'mock'],
                        help='LLM类型')
    parser.add_argument('--model', default='qwen:1.8b',
                        help='模型名称')
    
    args = parser.parse_args()
    
    processor = RawCaseProcessor(llm_type=args.llm_type, model=args.model)
    
    if args.all:
        processor.process_all(batch_size=args.batch_size, delay=args.delay)
    else:
        processor.process_batch(batch_size=args.batch_size, delay=args.delay)


if __name__ == '__main__':
    main()