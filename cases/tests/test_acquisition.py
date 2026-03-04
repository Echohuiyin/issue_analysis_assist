from django.test import TestCase
from unittest.mock import patch, MagicMock
from cases.acquisition.fetchers import BaseFetcher, HTTPFetcher
from cases.acquisition.parsers import BaseParser, BlogParser
from cases.acquisition.validators import CaseValidator
from cases.acquisition.storage import CaseStorage
from cases.models import KernelCase


class TestBaseFetcher(TestCase):
    def test_fetch_not_implemented(self):
        """Test that fetch method raises NotImplementedError in BaseFetcher"""
        # 创建一个没有实现fetch方法的子类
        class IncompleteFetcher(BaseFetcher):
            pass
        
        # 尝试实例化应该失败
        with self.assertRaises(TypeError):
            IncompleteFetcher()


class TestHTTPFetcher(TestCase):
    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        """Test HTTPFetcher fetch method with successful response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<html>Test Content</html>'
        mock_get.return_value = mock_response

        fetcher = HTTPFetcher()
        result = fetcher.fetch('http://example.com')

        self.assertEqual(result, '<html>Test Content</html>')
        mock_get.assert_called_once_with('http://example.com', timeout=10)

    @patch('requests.get')
    def test_fetch_failure(self, mock_get):
        """Test HTTPFetcher fetch method with failed response"""
        mock_get.side_effect = Exception('Network error')

        fetcher = HTTPFetcher()
        result = fetcher.fetch('http://example.com')

        self.assertIsNone(result)


class TestBaseParser(TestCase):
    def test_parse_not_implemented(self):
        """Test that parse method raises NotImplementedError in BaseParser"""
        # 创建一个没有实现parse方法的子类
        class IncompleteParser(BaseParser):
            pass
        
        # 尝试实例化应该失败
        with self.assertRaises(TypeError):
            IncompleteParser()


class TestCaseValidator(TestCase):
    def test_validate_missing_fields(self):
        """Test CaseValidator with missing required fields"""
        validator = CaseValidator()
        case_data = {
            'title': 'Test Case'
            # 缺少其他必填字段
        }

        result = validator.validate(case_data)

        self.assertFalse(result['is_valid'])
        self.assertIn("Required field 'phenomenon' is missing or empty", result['errors'])
        self.assertIn("Required field 'environment' is missing or empty", result['errors'])
        self.assertIn("Required field 'root_cause' is missing or empty", result['errors'])
        self.assertIn("Required field 'troubleshooting_steps' is missing or empty", result['errors'])
        self.assertIn("Required field 'solution' is missing or empty", result['errors'])

    def test_validate_valid_case(self):
        """Test CaseValidator with valid case data"""
        validator = CaseValidator()
        case_data = {
            'title': 'Test Case',
            'phenomenon': 'Test symptom',
            'environment': 'Test environment',
            'root_cause': 'This is a detailed root cause explanation',
            'solution': 'This is a detailed solution description',
            'troubleshooting_steps': ['Step 1', 'Step 2']
        }

        result = validator.validate(case_data)

        self.assertTrue(result['is_valid'])
        self.assertEqual(result['errors'], [])


class TestCaseStorage(TestCase):
    def setUp(self):
        """Set up test data"""
        self.storage = CaseStorage()

    @patch('cases.acquisition.storage.KernelCase')
    def test_store_new_case(self, mock_kernel_case):
        """Test CaseStorage store method with new case"""
        # 创建模拟的case实例
        mock_case_instance = MagicMock()
        mock_case_instance.case_id = 'TEST-001'
        
        # 设置模拟的KernelCase类和对象
        mock_kernel_case.objects.filter.return_value.first.return_value = None
        mock_kernel_case.return_value = mock_case_instance

        case_data = {
            'title': 'Test Case',
            'phenomenon': 'Test symptom',
            'environment': 'Test environment',
            'root_cause': 'Test root cause',
            'solution': 'Test solution',
            'troubleshooting_steps': ['Step 1', 'Step 2'],
            'case_id': 'TEST-001'
        }

        result = self.storage.store(case_data)

        self.assertTrue(result['success'])
        self.assertIn('Case stored successfully', result['message'])
        self.assertEqual(result['case_id'], 'TEST-001')
        mock_kernel_case.assert_called_once()

    @patch('cases.acquisition.storage.KernelCase')
    def test_store_existing_case(self, mock_kernel_case):
        """Test CaseStorage store method with existing case"""
        # 创建模拟的现有case
        mock_existing_case = MagicMock()
        mock_kernel_case.objects.filter.return_value.first.return_value = mock_existing_case

        case_data = {
            'title': 'Test Case',
            'phenomenon': 'Test symptom',
            'environment': 'Test environment',
            'root_cause': 'Test root cause',
            'solution': 'Test solution',
            'troubleshooting_steps': ['Step 1', 'Step 2'],
            'case_id': 'TEST-001'
        }

        result = self.storage.store(case_data)

        self.assertFalse(result['success'])
        self.assertIn('already exists', result['message'])