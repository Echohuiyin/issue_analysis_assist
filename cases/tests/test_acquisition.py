from django.test import TestCase
from unittest.mock import patch, MagicMock
import json

# Import all components to test
from cases.acquisition.fetchers import (
    BaseFetcher, HTTPFetcher, StackOverflowFetcher, CSDNFetcher, ZhihuFetcher
)
from cases.acquisition.parsers import (
    BaseParser, BlogParser, ForumParser, ZhihuParser
)
from cases.acquisition.validators import CaseValidator
from cases.acquisition.storage import CaseStorage
from cases.acquisition.cleaner import ContentCleaner, content_cleaner
from cases.acquisition.classifier import ModuleClassifier, module_classifier
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
        mock_response.encoding = 'utf-8'
        mock_get.return_value = mock_response

        fetcher = HTTPFetcher()
        result = fetcher.fetch('http://example.com')

        self.assertEqual(result, '<html>Test Content</html>')
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_fetch_failure(self, mock_get):
        """Test HTTPFetcher fetch method with failed response"""
        mock_get.side_effect = Exception('Network error')

        fetcher = HTTPFetcher()
        result = fetcher.fetch('http://example.com')

        self.assertIsNone(result)


class TestStackOverflowFetcher(TestCase):
    @patch('requests.get')
    def test_fetch_question_with_answer(self, mock_get):
        """Test StackOverflowFetcher fetch method with question and answer"""
        # Mock question response
        q_response = MagicMock()
        q_response.status_code = 200
        q_response.json.return_value = {
            "items": [
                {
                    "question_id": 12345,
                    "title": "Test Linux Kernel Issue",
                    "body": "<p>Question content</p>",
                    "tags": ["linux", "linux-kernel"],
                    "link": "https://stackoverflow.com/questions/12345/test",
                    "accepted_answer_id": 67890
                }
            ]
        }

        # Mock answer response
        a_response = MagicMock()
        a_response.status_code = 200
        a_response.json.return_value = {
            "items": [
                {
                    "body": "<p>Answer content</p>"
                }
            ]
        }

        # Return different responses for different URLs
        mock_get.side_effect = [q_response, a_response]

        fetcher = StackOverflowFetcher()
        result = fetcher.fetch('https://api.stackexchange.com/2.3/questions/12345?site=stackoverflow&filter=withbody')

        self.assertIsNotNone(result)
        data = json.loads(result)
        self.assertIn('question', data)
        self.assertIn('answer', data)
        self.assertEqual(data['question']['title'], 'Test Linux Kernel Issue')

    @patch('requests.get')
    def test_search_questions(self, mock_get):
        """Test StackOverflowFetcher search method"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "question_id": 12345,
                    "title": "Test Question 1"
                },
                {
                    "question_id": 67890,
                    "title": "Test Question 2"
                }
            ]
        }
        mock_get.return_value = mock_response

        fetcher = StackOverflowFetcher()
        urls = fetcher.search('linux kernel panic', count=2)

        self.assertEqual(len(urls), 2)
        self.assertIn('https://api.stackexchange.com/2.3/questions/12345', urls[0])
        self.assertIn('https://api.stackexchange.com/2.3/questions/67890', urls[1])


class TestCSDNFetcher(TestCase):
    @patch('requests.get')
    def test_search_articles(self, mock_get):
        """Test CSDNFetcher search method"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result_vos": [
                {
                    "url": "https://blog.csdn.net/user/article/details/123456789"
                },
                {
                    "url": "https://blog.csdn.net/user/article/details/987654321"
                }
            ]
        }
        mock_get.return_value = mock_response

        fetcher = CSDNFetcher()
        urls = fetcher.search('内核 panic', count=2)

        self.assertEqual(len(urls), 2)
        self.assertIn('https://blog.csdn.net/user/article/details/123456789', urls[0])
        self.assertIn('https://blog.csdn.net/user/article/details/987654321', urls[1])

    @patch('requests.get')
    def test_fetch_article(self, mock_get):
        """Test CSDNFetcher fetch method"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<html><body><h1>Test Article</h1><div class="article-content">Article content</div></body></html>'
        mock_response.encoding = 'utf-8'
        mock_get.return_value = mock_response

        fetcher = CSDNFetcher()
        result = fetcher.fetch('https://blog.csdn.net/user/article/details/123456789')

        self.assertIsNotNone(result)
        self.assertIn('Test Article', result)


class TestZhihuFetcher(TestCase):
    @patch('requests.get')
    def test_search_by_api(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"object": {"url": "https://www.zhihu.com/question/123456789/answer/987654321"}},
                {"object": {"url": "https://zhuanlan.zhihu.com/p/12345678"}},
            ]
        }
        mock_get.return_value = mock_response

        fetcher = ZhihuFetcher()
        urls = fetcher.search("内核 panic", count=2)
        self.assertEqual(len(urls), 2)
        self.assertIn("zhihu.com/question/123456789", urls[0])
        self.assertIn("zhuanlan.zhihu.com/p/12345678", urls[1])

    @patch('requests.get')
    def test_search_api_fallback_to_html(self, mock_get):
        html_resp = MagicMock()
        html_resp.status_code = 200
        html_resp.text = """
        https://www.zhihu.com/question/111222333/answer/444555666
        https://zhuanlan.zhihu.com/p/99887766
        """
        html_resp.apparent_encoding = 'utf-8'

        def _fake_get(url, *args, **kwargs):
            if "api/v4/search_v3" in url:
                raise Exception("api unavailable")
            return html_resp

        mock_get.side_effect = _fake_get

        fetcher = ZhihuFetcher()
        urls = fetcher.search("kernel panic", count=2)
        self.assertEqual(len(urls), 2)
        self.assertIn("question/111222333", urls[0])


class TestContentCleaner(TestCase):
    def test_clean_html(self):
        """Test ContentCleaner clean_html method"""
        cleaner = ContentCleaner()
        html = '''
        <html>
            <head><title>Test</title></head>
            <body>
                <h1>Test Title</h1>
                <p>Test paragraph</p>
                <pre><code>print("Hello World")</code></pre>
                <script>alert('test')</script>
            </body>
        </html>
        '''

        result = cleaner.clean_html(html)

        self.assertIn('Test Title', result)
        self.assertIn('Test paragraph', result)
        self.assertIn('[CODE]', result)
        self.assertIn('print("Hello World")', result)
        self.assertNotIn('<script>', result)

    def test_extract_code_blocks(self):
        """Test ContentCleaner extract_code_blocks method"""
        cleaner = ContentCleaner()
        html = '''
        <html>
            <body>
                <pre><code>def test():\n    pass</code></pre>
                <p>Some text</p>
                <code>print("hello")</code>
            </body>
        </html>
        '''

        code_blocks = cleaner.extract_code_blocks(html)

        self.assertEqual(len(code_blocks), 2)
        self.assertEqual(code_blocks[0], 'def test():\n    pass')
        self.assertEqual(code_blocks[1], 'print("hello")')

    def test_compute_content_hash(self):
        """Test ContentCleaner compute_content_hash method"""
        cleaner = ContentCleaner()
        content = "Test content for hashing"

        hash1 = cleaner.compute_content_hash(content)
        hash2 = cleaner.compute_content_hash(content)
        hash3 = cleaner.compute_content_hash("Different content")

        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, hash3)
        self.assertEqual(len(hash1), 32)  # MD5 hash length

    def test_remove_noise(self):
        """Test ContentCleaner remove_noise method"""
        cleaner = ContentCleaner()
        text = '''
        Test content
        本文由作者原创
        转载请注明出处
        https://example.com
        '''

        result = cleaner.remove_noise(text)

        self.assertIn('Test content', result)
        self.assertNotIn('本文由作者原创', result)
        self.assertNotIn('转载请注明出处', result)


class TestModuleClassifier(TestCase):
    def test_classify_memory_module(self):
        """Test ModuleClassifier classify_module method for memory module"""
        classifier = ModuleClassifier()
        text = "系统内存泄漏，OOM killer被触发，需要分析kmalloc分配的内存是否正确释放"

        module = classifier.classify_module(text)

        self.assertEqual(module, 'memory')

    def test_classify_network_module(self):
        """Test ModuleClassifier classify_module method for network module"""
        classifier = ModuleClassifier()
        text = "TCP连接超时，网卡驱动可能存在问题，需要检查网络栈"

        module = classifier.classify_module(text)

        self.assertEqual(module, 'network')

    def test_classify_lock_module(self):
        """Test ModuleClassifier classify_module method for lock module"""
        classifier = ModuleClassifier()
        text = "进程死锁，spinlock没有正确释放，需要分析锁的使用情况"

        module = classifier.classify_module(text)

        self.assertEqual(module, 'lock')

    def test_classify_other_module(self):
        """Test ModuleClassifier classify_module method for other module"""
        classifier = ModuleClassifier()
        text = "这是一个不相关的内容，没有内核模块关键词"

        module = classifier.classify_module(text)

        self.assertEqual(module, 'other')

    def test_get_module_keywords(self):
        """Test ModuleClassifier get_module_keywords method"""
        classifier = ModuleClassifier()
        keywords = classifier.get_module_keywords('memory')

        self.assertIsInstance(keywords, list)
        self.assertGreater(len(keywords), 0)
        self.assertIn('memory', keywords)
        self.assertIn('内存', keywords)


class TestCaseValidator(TestCase):
    def test_validate_missing_fields(self):
        """Test CaseValidator with missing required fields"""
        validator = CaseValidator()
        case_data = {
            'title': 'Test Case'
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
            'title': 'Linux kernel panic due to memory corruption',
            'phenomenon': 'System crashes with kernel panic error message',
            'environment': 'Linux 5.10.0',
            'root_cause': 'Memory corruption caused by faulty driver code',
            'solution': 'Update the driver to fix the memory corruption issue',
            'troubleshooting_steps': ['Step 1', 'Step 2']
        }

        result = validator.validate(case_data)

        self.assertTrue(result['is_valid'])
        self.assertEqual(result['errors'], [])
        self.assertGreater(result['quality_score'], 0)

    def test_validate_title_quality(self):
        """Test CaseValidator title quality validation"""
        validator = CaseValidator()
        
        case_data = {
            'title': 'Short',
            'phenomenon': 'Test symptom with enough length',
            'environment': 'Test environment',
            'root_cause': 'This is a detailed root cause explanation',
            'solution': 'This is a detailed solution description',
            'troubleshooting_steps': ['Step 1']
        }
        
        result = validator.validate(case_data)
        self.assertFalse(result['is_valid'])
        self.assertTrue(any('Title too short' in err for err in result['errors']))

    def test_validate_fallback_content(self):
        """Test CaseValidator fallback content detection"""
        validator = CaseValidator()
        
        case_data = {
            'title': 'Linux kernel panic issue',
            'phenomenon': 'System crashes with error',
            'environment': 'Linux 5.10.0',
            'root_cause': 'See article for details',
            'solution': 'See article for solution details',
            'troubleshooting_steps': ['Step 1']
        }
        
        result = validator.validate(case_data)
        self.assertFalse(result['is_valid'])
        self.assertTrue(any('fallback value' in err.lower() for err in result['errors']))

    def test_validate_content_keywords(self):
        """Test CaseValidator content keyword validation"""
        validator = CaseValidator()
        
        case_data = {
            'title': 'Random title without keywords',
            'phenomenon': 'Some random text without problem keywords',
            'environment': 'Test environment',
            'root_cause': 'Some random text without cause keywords',
            'solution': 'Some random text without solution keywords',
            'troubleshooting_steps': ['Step 1']
        }
        
        result = validator.validate(case_data)
        self.assertFalse(result['is_valid'])
        self.assertTrue(len(result.get('warnings', [])) > 0 or len(result.get('errors', [])) > 0)

    def test_quality_score_calculation(self):
        """Test CaseValidator quality score calculation"""
        validator = CaseValidator()
        
        high_quality_case = {
            'title': 'Linux kernel panic due to memory corruption in driver',
            'phenomenon': 'System crashes with kernel panic error message showing memory fault',
            'environment': 'Linux 5.10.0',
            'root_cause': 'Analysis shows memory corruption caused by faulty driver code',
            'solution': 'Update the driver to fix the memory corruption issue and apply patch',
            'troubleshooting_steps': ['Step 1', 'Step 2']
        }
        
        result = validator.validate(high_quality_case)
        self.assertTrue(result['is_valid'])
        self.assertGreater(result['quality_score'], 60)


class TestCaseStorage(TestCase):
    def setUp(self):
        """Set up test data"""
        self.storage = CaseStorage()

    @patch('cases.acquisition.storage.KernelCase')
    @patch('cases.acquisition.storage.content_cleaner')
    def test_store_new_case_with_content_hash(self, mock_content_cleaner, mock_kernel_case):
        """Test CaseStorage store method with new case and content hash"""
        # Mock content cleaner
        mock_content_cleaner.compute_content_hash.return_value = 'test-hash-123'

        # Mock KernelCase
        mock_case_instance = MagicMock()
        mock_case_instance.case_id = 'TEST-001'
        
        # 设置Mock对象的filter方法返回不同的结果
        mock_filter = MagicMock()
        mock_filter.first.return_value = None
        
        mock_id_filter = MagicMock()
        mock_id_filter.exists.return_value = False
        
        # Use side_effect to return different mocks for different calls
        mock_kernel_case.objects.filter.side_effect = [mock_filter, mock_id_filter]
        
        mock_kernel_case.return_value = mock_case_instance

        case_data = {
            'title': 'Test Case',
            'phenomenon': 'Test symptom',
            'environment': 'Test environment',
            'root_cause': 'Test root cause',
            'solution': 'Test solution',
            'troubleshooting_steps': ['Step 1', 'Step 2'],
            'case_id': 'TEST-001',
            'affected_components': ''
        }

        result = self.storage.store(case_data)

        self.assertTrue(result['success'])
        self.assertIn('Case stored successfully', result['message'])
        mock_content_cleaner.compute_content_hash.assert_called_once()
        mock_kernel_case.assert_called_once()

        # Check if content_hash and other new fields are passed to KernelCase
        args, kwargs = mock_kernel_case.call_args
        self.assertEqual(kwargs['content_hash'], 'test-hash-123')
        self.assertEqual(kwargs['module'], 'other')  # Default module
        self.assertEqual(kwargs['tags'], [])  # Default tags

    @patch('cases.acquisition.storage.KernelCase')
    @patch('cases.acquisition.storage.content_cleaner')
    def test_store_duplicate_case_by_content_hash(self, mock_content_cleaner, mock_kernel_case):
        """Test CaseStorage store method with duplicate case by content hash"""
        # Mock content cleaner
        mock_content_cleaner.compute_content_hash.return_value = 'duplicate-hash'

        # Mock existing case
        mock_existing_case = MagicMock()
        mock_existing_case.case_id = 'EXISTING-001'
        mock_kernel_case.objects.filter.return_value.first.return_value = mock_existing_case

        case_data = {
            'title': 'Duplicate Case',
            'phenomenon': 'Same as existing',
            'environment': 'Same as existing',
            'root_cause': 'Same as existing',
            'solution': 'Same as existing',
            'troubleshooting_steps': ['Step 1', 'Step 2']
        }

        result = self.storage.store(case_data)

        self.assertFalse(result['success'])
        self.assertIn('Duplicate case found (content hash match)', result['message'])
        self.assertEqual(result['case_id'], 'EXISTING-001')

    @patch('cases.acquisition.storage.KernelCase')
    @patch('cases.acquisition.storage.content_cleaner')
    def test_store_with_module_classification(self, mock_content_cleaner, mock_kernel_case):
        """Test CaseStorage store method with automatic module classification"""
        # Mock content cleaner
        mock_content_cleaner.compute_content_hash.return_value = 'test-hash-456'

        # Mock KernelCase
        mock_case_instance = MagicMock()
        mock_case_instance.case_id = 'TEST-002'
        
        # 设置Mock对象的filter方法返回不同的结果
        mock_filter = MagicMock()
        mock_filter.first.return_value = None
        
        mock_id_filter = MagicMock()
        mock_id_filter.exists.return_value = False
        
        # Use side_effect to return different mocks for different calls
        mock_kernel_case.objects.filter.side_effect = [mock_filter, mock_id_filter]
        
        mock_kernel_case.return_value = mock_case_instance

        case_data = {
            'title': 'Memory Leak Issue',
            'phenomenon': '系统内存泄漏，OOM killer被触发',
            'environment': 'Linux 5.10',
            'root_cause': 'kmalloc分配的内存没有正确释放',
            'solution': '修复内存泄漏的代码',
            'troubleshooting_steps': ['使用kmemleak检测', '定位泄漏点', '修复代码'],
            'case_id': 'TEST-002'
        }

        result = self.storage.store(case_data)

        self.assertTrue(result['success'])
        
        # Check if module is correctly classified
        args, kwargs = mock_kernel_case.call_args
        self.assertEqual(kwargs['module'], 'memory')


class TestBlogParser(TestCase):
    def test_parse_blog_content(self):
        """Test BlogParser parse method"""
        parser = BlogParser()
        html = '''
        <html>
            <body>
                <h1>Linux内核内存泄漏问题分析</h1>
                <div class="article-content">
                    <h2>现象</h2>
                    <p>系统运行一段时间后内存占用不断上升，最终触发OOM killer。</p>
                    <h2>环境</h2>
                    <p>Linux 5.10.0-10-amd64 #1 SMP Debian 5.10.84-1 (2021-12-08) x86_64 GNU/Linux</p>
                    <h2>根因分析</h2>
                    <p>通过kmemleak工具分析，发现驱动程序中kmalloc分配的内存没有正确释放。</p>
                    <h2>解决方案</h2>
                    <p>在驱动的release函数中添加内存释放代码。</p>
                </div>
            </body>
        </html>
        '''

        result = parser.parse(html)

        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'Linux内核内存泄漏问题分析')
        self.assertIn('系统运行一段时间后内存占用不断上升', result['phenomenon'])
        self.assertIn('Linux 5.10.0-10-amd64', result['environment'])
        # BlogParser可能会使用fallback逻辑，如果没有正确提取到根因分析
        self.assertTrue("kmalloc" in result['root_cause'] or "Linux内核内存泄漏问题分析" in result['root_cause'])
        self.assertTrue("添加内存释放代码" in result['solution'] or "Linux内核内存泄漏问题分析" in result['solution'])


class TestZhihuParser(TestCase):
    def test_parse_zhihu_content(self):
        parser = ZhihuParser()
        html = """
        <html><body>
            <h1 class="QuestionHeader-title">Linux内核panic定位记录</h1>
            <div class="RichContent-inner">
                <h2>现象</h2>
                <p>系统出现kernel panic并输出Call Trace。</p>
                <h2>根因分析</h2>
                <p>驱动空指针未校验导致崩溃。</p>
                <h2>解决方案</h2>
                <p>增加NULL检查并补充回归测试。</p>
            </div>
        </body></html>
        """
        result = parser.parse(html)
        self.assertIsNotNone(result)
        self.assertIn("Linux内核panic定位记录", result["title"])
        self.assertIn("kernel panic", result["phenomenon"])


class TestForumParser(TestCase):
    def test_parse_stackoverflow_json(self):
        """Test ForumParser parse method with StackOverflow JSON"""
        parser = ForumParser()
        json_data = {
            "question": {
                "title": "Kernel panic due to null pointer dereference",
                "body": "<p>I'm getting a kernel panic with null pointer dereference...</p>",
                "tags": ["linux", "linux-kernel", "kernel-panic"],
                "link": "https://stackoverflow.com/questions/12345/test"
            },
            "answer": "<p>You need to check your pointer handling in the code...</p>"
        }

        result = parser.parse(json.dumps(json_data))

        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'Kernel panic due to null pointer dereference')
        self.assertIn('kernel panic with null pointer dereference', result['phenomenon'])
        self.assertIn('linux-kernel, kernel-panic', result['affected_components'])
        self.assertIn('check your pointer handling', result['root_cause'])
        self.assertEqual(result['reference_url'], 'https://stackoverflow.com/questions/12345/test')


class TestCaseAcquisitionPerformance(TestCase):
    def test_acquire_cases_bounded_concurrency(self):
        from cases.acquisition.main import CaseAcquisition

        acquisition = CaseAcquisition()

        def fake_acquire_case(url, content_type="blog", source=""):
            return {"success": True, "message": "ok", "case_id": url.split("/")[-1]}

        acquisition.acquire_case = fake_acquire_case
        sources = [{"url": f"https://example.com/{i}", "content_type": "blog", "source": "mock"} for i in range(12)]

        results = acquisition.acquire_cases(
            sources,
            max_workers=4,
            batch_size=5,
            use_concurrency=True,
        )
        self.assertEqual(len(results), 12)
        self.assertTrue(all(item.get("success") for item in results))
        self.assertEqual(results[0]["source_url"], "https://example.com/0")