"""
测试新增的数据库模型和脚本功能
"""

import os
import sys
import json
from unittest.mock import patch, MagicMock

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')

import django
django.setup()

from django.test import TestCase
from django.utils import timezone
from cases.models import RawCase, TrainingCase, TestCase, KernelCase


class TestRawCase(TestCase):
    """测试原始案例模型"""
    
    def test_create_raw_case(self):
        """测试创建原始案例"""
        raw_case = RawCase.objects.create(
            raw_content='<html>Test content</html>',
            source='stackoverflow',
            source_url='https://stackoverflow.com/questions/12345',
            source_id='12345'
        )
        
        self.assertEqual(raw_case.source, 'stackoverflow')
        self.assertEqual(raw_case.source_id, '12345')
        self.assertFalse(raw_case.processed)
        self.assertIsNotNone(raw_case.fetched_at)
    
    def test_raw_case_ordering(self):
        """测试原始案例按ID顺序排列"""
        RawCase.objects.create(raw_content='content1', source='test')
        RawCase.objects.create(raw_content='content2', source='test')
        RawCase.objects.create(raw_content='content3', source='test')
        
        cases = list(RawCase.objects.all())
        self.assertEqual(len(cases), 3)
        self.assertLess(cases[0].id, cases[1].id)
        self.assertLess(cases[1].id, cases[2].id)
    
    def test_mark_as_processed(self):
        """测试标记为已处理"""
        raw_case = RawCase.objects.create(
            raw_content='test',
            source='test'
        )
        
        self.assertFalse(raw_case.processed)
        
        raw_case.processed = True
        raw_case.processed_at = timezone.now()
        raw_case.save()
        
        raw_case.refresh_from_db()
        self.assertTrue(raw_case.processed)
        self.assertIsNotNone(raw_case.processed_at)


class TestTrainingCase(TestCase):
    """测试训练集模型"""
    
    def test_create_training_case(self):
        """测试创建训练集案例"""
        raw_case = RawCase.objects.create(
            raw_content='test content',
            source='test'
        )
        
        training_case = TrainingCase.objects.create(
            title='Linux kernel panic test',
            phenomenon='System crashes with kernel panic',
            key_logs='kernel panic - not syncing',
            environment='Linux 5.10.0',
            root_cause='Memory corruption in driver',
            analysis_process='Analyzed crash dump and found memory issue',
            solution='Update driver to fix memory allocation',
            module='memory',
            tags=['kernel', 'panic', 'memory'],
            source='stackoverflow',
            source_url='https://stackoverflow.com/questions/12345',
            raw_case=raw_case,
            quality_score=85.0,
            confidence=0.9
        )
        
        self.assertEqual(training_case.title, 'Linux kernel panic test')
        self.assertEqual(training_case.module, 'memory')
        self.assertEqual(training_case.quality_score, 85.0)
        self.assertEqual(training_case.raw_case, raw_case)
    
    def test_training_case_ordering(self):
        """测试训练集按ID顺序排列"""
        TrainingCase.objects.create(title='case1', module='memory')
        TrainingCase.objects.create(title='case2', module='network')
        TrainingCase.objects.create(title='case3', module='lock')
        
        cases = list(TrainingCase.objects.all())
        self.assertEqual(len(cases), 3)
        self.assertLess(cases[0].id, cases[1].id)
        self.assertLess(cases[1].id, cases[2].id)


class TestTestCase(TestCase):
    """测试测试集模型"""
    
    def test_create_test_case(self):
        """测试创建测试集案例"""
        raw_case = RawCase.objects.create(
            raw_content='test content',
            source='test'
        )
        
        test_case = TestCase.objects.create(
            title='Test case for kernel deadlock',
            phenomenon='System hangs with deadlock',
            key_logs='spinlock stuck',
            environment='Linux 5.15.0',
            root_cause='Incorrect lock ordering',
            analysis_process='Analyzed lock traces',
            solution='Fix lock ordering in driver',
            module='lock',
            tags=['kernel', 'deadlock', 'lock'],
            source='csdn',
            source_url='https://blog.csdn.net/article/123',
            raw_case=raw_case,
            quality_score=80.0,
            confidence=0.85
        )
        
        self.assertEqual(test_case.title, 'Test case for kernel deadlock')
        self.assertEqual(test_case.module, 'lock')
        self.assertEqual(test_case.quality_score, 80.0)
        self.assertEqual(test_case.raw_case, raw_case)
    
    def test_test_case_ordering(self):
        """测试测试集按ID顺序排列"""
        TestCase.objects.create(title='test1', module='memory')
        TestCase.objects.create(title='test2', module='network')
        TestCase.objects.create(title='test3', module='scheduler')
        
        cases = list(TestCase.objects.all())
        self.assertEqual(len(cases), 3)
        self.assertLess(cases[0].id, cases[1].id)
        self.assertLess(cases[1].id, cases[2].id)


class TestBackgroundCrawler(TestCase):
    """测试后台爬取工具"""
    
    @patch('scripts.background_crawler.StackOverflowFetcher')
    @patch('scripts.background_crawler.RawCase')
    def test_save_raw_case(self, mock_raw_case, mock_fetcher):
        """测试保存原始案例"""
        from scripts.background_crawler import BackgroundCrawler
        
        crawler = BackgroundCrawler(target_count=10)
        
        mock_raw_case.objects.filter.return_value.exists.return_value = False
        mock_raw_case.objects.create.return_value = MagicMock()
        
        result = crawler.save_raw_case(
            content='test content with enough length',
            source='test',
            url='https://example.com/test'
        )
        
        self.assertTrue(result)
        mock_raw_case.objects.create.assert_called_once()
    
    @patch('scripts.background_crawler.StackOverflowFetcher')
    def test_save_duplicate_url(self, mock_fetcher):
        """测试跳过重复URL"""
        from scripts.background_crawler import BackgroundCrawler
        
        crawler = BackgroundCrawler(target_count=10)
        
        with patch('scripts.background_crawler.RawCase') as mock_raw_case:
            mock_raw_case.objects.filter.return_value.exists.return_value = True
            
            result = crawler.save_raw_case(
                content='test content',
                source='test',
                url='https://example.com/duplicate'
            )
            
            self.assertFalse(result)
    
    @patch('scripts.background_crawler.StackOverflowFetcher')
    def test_get_current_count(self, mock_fetcher):
        """测试获取当前数量"""
        from scripts.background_crawler import BackgroundCrawler
        
        crawler = BackgroundCrawler(target_count=10)
        
        with patch('scripts.background_crawler.RawCase') as mock_raw_case:
            mock_raw_case.objects.count.return_value = 5
            count = crawler.get_current_count()
            self.assertEqual(count, 5)


class TestCaseProcessor(TestCase):
    """测试案例处理器"""
    
    @patch('scripts.process_cases.LLMParser')
    def test_parse_raw_case(self, mock_llm_parser_class):
        """测试解析原始案例"""
        from scripts.process_cases import CaseProcessor
        
        mock_parser = MagicMock()
        mock_parser.parse.return_value = {
            'title': 'Test Case',
            'phenomenon': 'Test phenomenon',
            'root_cause': 'Test root cause',
            'solution': 'Test solution',
            'module': 'memory',
            'confidence': 0.8
        }
        mock_llm_parser_class.return_value = mock_parser
        
        processor = CaseProcessor()
        
        raw_case = RawCase.objects.create(
            raw_content='test content',
            source='test',
            source_url='https://example.com/test'
        )
        
        result = processor.parse_raw_case(raw_case)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'Test Case')
        self.assertEqual(result['source'], 'test')
    
    @patch('scripts.process_cases.LLMParser')
    def test_validate_case(self, mock_llm_parser_class):
        """测试验证案例质量"""
        from scripts.process_cases import CaseProcessor
        
        mock_parser = MagicMock()
        mock_llm_parser_class.return_value = mock_parser
        
        processor = CaseProcessor()
        
        case_data = {
            'title': 'Linux kernel panic due to memory corruption',
            'phenomenon': 'System crashes with kernel panic error',
            'environment': 'Linux 5.10.0',
            'root_cause': 'Memory corruption in driver code',
            'solution': 'Update driver to fix memory allocation',
            'troubleshooting_steps': ['Step 1', 'Step 2']
        }
        
        result = processor.validate_case(case_data)
        
        self.assertIn('is_valid', result)
        self.assertIn('quality_score', result)
    
    @patch('scripts.process_cases.LLMParser')
    def test_save_to_training_set(self, mock_llm_parser_class):
        """测试保存到训练集"""
        from scripts.process_cases import CaseProcessor
        
        mock_parser = MagicMock()
        mock_llm_parser_class.return_value = mock_parser
        
        processor = CaseProcessor(test_ratio=0.0)
        
        raw_case = RawCase.objects.create(
            raw_content='test',
            source='test'
        )
        
        parsed_data = {
            'title': 'Test Training Case',
            'phenomenon': 'Test phenomenon',
            'key_logs': 'Test logs',
            'environment': 'Linux 5.10',
            'root_cause': 'Test root cause',
            'analysis_process': 'Test analysis',
            'solution': 'Test solution',
            'module': 'memory',
            'tags': ['test'],
            'source': 'test',
            'source_url': 'https://example.com',
            'quality_score': 85.0,
            'confidence': 0.9
        }
        
        result = processor.save_to_dataset(parsed_data, raw_case, is_test=False)
        
        self.assertTrue(result)
        self.assertEqual(TrainingCase.objects.count(), 1)
    
    @patch('scripts.process_cases.LLMParser')
    def test_save_to_test_set(self, mock_llm_parser_class):
        """测试保存到测试集"""
        from scripts.process_cases import CaseProcessor
        
        mock_parser = MagicMock()
        mock_llm_parser_class.return_value = mock_parser
        
        processor = CaseProcessor(test_ratio=1.0)
        
        raw_case = RawCase.objects.create(
            raw_content='test',
            source='test'
        )
        
        parsed_data = {
            'title': 'Test Case',
            'phenomenon': 'Test phenomenon',
            'key_logs': 'Test logs',
            'environment': 'Linux 5.10',
            'root_cause': 'Test root cause',
            'analysis_process': 'Test analysis',
            'solution': 'Test solution',
            'module': 'network',
            'tags': ['test'],
            'source': 'test',
            'source_url': 'https://example.com',
            'quality_score': 80.0,
            'confidence': 0.85
        }
        
        result = processor.save_to_dataset(parsed_data, raw_case, is_test=True)
        
        self.assertTrue(result)
        self.assertEqual(TestCase.objects.count(), 1)


class TestIntegration(TestCase):
    """集成测试"""
    
    def test_full_pipeline(self):
        """测试完整流程：创建原始案例 -> 处理 -> 存入训练集"""
        raw_case = RawCase.objects.create(
            raw_content='<html><body>Kernel panic test content</body></html>',
            source='stackoverflow',
            source_url='https://stackoverflow.com/questions/99999',
            source_id='99999'
        )
        
        self.assertIsNotNone(raw_case.id)
        self.assertFalse(raw_case.processed)
        
        training_case = TrainingCase.objects.create(
            title='Kernel panic test case',
            phenomenon='System panic',
            key_logs='panic log',
            environment='Linux 5.10',
            root_cause='Test cause',
            analysis_process='Test analysis',
            solution='Test solution',
            module='memory',
            source='stackoverflow',
            source_url='https://stackoverflow.com/questions/99999',
            raw_case=raw_case,
            quality_score=85.0,
            confidence=0.9
        )
        
        raw_case.processed = True
        raw_case.processed_at = timezone.now()
        raw_case.save()
        
        raw_case.refresh_from_db()
        self.assertTrue(raw_case.processed)
        
        self.assertEqual(TrainingCase.objects.count(), 1)
        saved_case = TrainingCase.objects.first()
        self.assertEqual(saved_case.raw_case, raw_case)
        self.assertEqual(saved_case.quality_score, 85.0)