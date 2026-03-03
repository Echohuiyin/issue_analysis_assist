from django.test import TestCase
from cases.forms import KernelCaseForm
from cases.models import KernelCase

class KernelCaseFormTest(TestCase):
    """Test KernelCaseForm functionality"""

    def test_form_fields(self):
        """Test form fields"""
        form = KernelCaseForm()
        expected_fields = ['case_id', 'title', 'description', 'symptoms', 'root_cause', 
                           'solution', 'kernel_version', 'affected_components', 'severity']
        # Verify form contains expected fields
        for field in expected_fields:
            self.assertIn(field, form.fields)

    def test_form_valid(self):
        """Test valid form data"""
        form_data = {
            'case_id': 'KERNEL-2023-027',
            'title': 'System Crash Issue',
            'description': 'Kernel panic when running specific workloads',
            'symptoms': 'System freezes and reboots',
            'root_cause': 'Memory management bug in page fault handler',
            'solution': 'Apply patch to fix page fault handling',
            'kernel_version': '5.10.0-1057',
            'affected_components': 'Memory Management Subsystem',
            'severity': 'Critical'
        }
        form = KernelCaseForm(data=form_data)
        # Verify form is valid
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        """Test invalid form data"""
        form_data = {
            'case_id': 'KERNEL-2023-027',  # Valid
            'title': '',  # Missing required field
            'description': 'Kernel panic when running specific workloads',
            'symptoms': 'System freezes and reboots',
            'root_cause': 'Memory management bug in page fault handler',
            'solution': 'Apply patch to fix page fault handling',
            'kernel_version': '5.10.0-1057',
            'affected_components': 'Memory Management Subsystem',
            'severity': 'Critical'
        }
        form = KernelCaseForm(data=form_data)
        # Verify form is invalid
        self.assertFalse(form.is_valid())
        # Verify error on title field
        self.assertIn('title', form.errors)

    def test_form_duplicate_case_id(self):
        """Test form with duplicate case ID"""
        # Create a case with specific case_id first
        KernelCase.objects.create(
            case_id='KERNEL-2023-028',
            title='Existing Case',
            description='Test description',
            symptoms='Test symptoms',
            root_cause='Test root cause',
            solution='Test solution',
            kernel_version='5.10.0-1057',
            affected_components='Test component',
            severity='Medium'
        )
        # Try to create another case with the same case_id
        form_data = {
            'case_id': 'KERNEL-2023-028',  # Duplicate
            'title': 'Another System Crash Issue',
            'description': 'Another kernel panic issue',
            'symptoms': 'System freezes',
            'root_cause': 'Different bug',
            'solution': 'Apply different patch',
            'kernel_version': '5.10.0-1057',
            'affected_components': 'Another component',
            'severity': 'High'
        }
        form = KernelCaseForm(data=form_data)
        # Verify form is invalid due to duplicate case_id
        self.assertFalse(form.is_valid())
        # Verify error on case_id field
        self.assertIn('case_id', form.errors)

    def test_form_severity_choices(self):
        """Test form severity choices"""
        form = KernelCaseForm()
        expected_choices = [('', '---------'), ('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'), ('Critical', 'Critical')]
        # Verify severity field has expected choices
        self.assertEqual(form.fields['severity'].choices, expected_choices)