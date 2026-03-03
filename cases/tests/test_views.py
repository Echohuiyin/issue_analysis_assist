from django.test import TestCase, Client
from django.urls import reverse
from cases.models import KernelCase

class KernelCaseViewsTest(TestCase):
    """Test KernelCase views functionality"""

    def setUp(self):
        """Create test data and client before each test method"""
        self.client = Client()
        # Create test cases
        for i in range(25):
            KernelCase.objects.create(
                case_id=f'KERNEL-2023-{i+1:03d}',
                title=f'Test Case {i+1}',
                description=f'This is the description of test case {i+1}',
                symptoms=f'Symptoms of test case {i+1}',
                root_cause=f'Root cause of test case {i+1}',
                solution=f'Solution of test case {i+1}',
                kernel_version='5.10.0-1057',
                affected_components=f'Test Component {i+1}',
                severity='Medium'
            )
        # Create a high severity case for search testing
        self.high_severity_case = KernelCase.objects.create(
            case_id='KERNEL-2023-026',
            title='High Priority Test Case',
            description='This is a high priority test case',
            symptoms='Severe symptoms',
            root_cause='Severe root cause',
            solution='Complex solution',
            kernel_version='5.10.0-1057',
            affected_components='Core Component',
            severity='Critical'
        )

    def test_index_view(self):
        """Test index page view"""
        response = self.client.get(reverse('index'))
        # Verify response status code
        self.assertEqual(response.status_code, 200)
        # Verify correct template is used
        self.assertTemplateUsed(response, 'cases/index.html')
        # Verify pagination functionality (20 items per page by default)
        self.assertEqual(len(response.context['cases']), 20)
        # Verify content of first page - latest case is the high priority test case
        self.assertEqual(response.context['cases'][0].title, 'High Priority Test Case')  # Latest case
        self.assertEqual(response.context['cases'][1].title, 'Test Case 25')

    def test_index_view_pagination(self):
        """Test index page pagination"""
        # Access page 2
        response = self.client.get(reverse('index') + '?page=2')
        self.assertEqual(response.status_code, 200)
        # Verify page 2 has 5 records (26 total)
        self.assertEqual(len(response.context['cases']), 6)
        # Verify first record on page 2
        self.assertEqual(response.context['cases'][0].title, 'Test Case 6')

    def test_case_detail_view(self):
        """Test case detail view"""
        # Use an existing test case ID
        case = KernelCase.objects.first()
        response = self.client.get(reverse('case_detail', args=[case.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cases/case_detail.html')
        self.assertEqual(response.context['case'].id, case.id)
        self.assertEqual(response.context['case'].title, case.title)

    def test_case_detail_view_nonexistent(self):
        """Test accessing non-existent case"""
        # Use a non-existent ID
        response = self.client.get(reverse('case_detail', args=[999]))
        # Verify 404 status code is returned
        self.assertEqual(response.status_code, 404)

    def test_add_case_view_get(self):
        """Test GET request to add case page"""
        response = self.client.get(reverse('add_case'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cases/add_case.html')
        self.assertIsInstance(response.context['form'], KernelCaseForm)

    def test_add_case_view_post_valid(self):
        """Test POST request with valid case data"""
        form_data = {
            'case_id': 'KERNEL-2023-999',  # Use a unique case ID
            'title': 'New Test Case',
            'description': 'Description of new test case',
            'symptoms': 'Symptoms of new test case',
            'root_cause': 'Root cause of new test case',
            'solution': 'Solution of new test case',
            'kernel_version': '5.10.0-1057',
            'affected_components': 'New Test Component',
            'severity': 'High'
        }
        response = self.client.post(reverse('add_case'), data=form_data)
        # Verify redirect to index page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('index'))
        # Verify case was created
        self.assertTrue(KernelCase.objects.filter(case_id='KERNEL-2023-999').exists())

    def test_add_case_view_post_invalid(self):
        """Test POST request with invalid case data"""
        form_data = {
            'case_id': 'KERNEL-2023-028',
            # Missing required fields
        }
        response = self.client.post(reverse('add_case'), data=form_data)
        # Verify 200 status code (form is re-displayed)
        self.assertEqual(response.status_code, 200)
        # Verify form is invalid
        self.assertFalse(response.context['form'].is_valid())
        # Verify case was not created
        self.assertFalse(KernelCase.objects.filter(case_id='KERNEL-2023-028').exists())

    def test_search_view(self):
        """Test search view"""
        # Search for keyword "High Priority"
        response = self.client.get(reverse('search') + '?query=High Priority')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cases/index.html')
        # Verify only matching cases are returned
        self.assertEqual(len(response.context['cases']), 1)
        self.assertEqual(response.context['cases'][0].title, 'High Priority Test Case')

    def test_search_view_multiple_results(self):
        """Test search returning multiple results"""
        # Search for keyword "Test Case", which should return all cases
        response = self.client.get(reverse('search') + '?query=Test Case')
        self.assertEqual(response.status_code, 200)
        # Verify pagination functionality
        self.assertEqual(len(response.context['cases']), 20)

    def test_search_view_no_results(self):
        """Test search with no results"""
        # Search for non-existent keyword
        response = self.client.get(reverse('search') + '?query=Non-existent keyword')
        self.assertEqual(response.status_code, 200)
        # Verify no results
        self.assertEqual(len(response.context['cases']), 0)

    def test_stats_view(self):
        """Test statistics view"""
        response = self.client.get(reverse('stats'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cases/stats.html')
        # Verify statistics data
        self.assertEqual(response.context['total_cases'], 26)
        # Verify severity statistics
        severity_stats = {stat['severity']: stat['count'] for stat in response.context['severity_stats']}
        self.assertEqual(severity_stats['Medium'], 25)
        self.assertEqual(severity_stats['Critical'], 1)

# 导入表单类用于测试
from cases.forms import KernelCaseForm