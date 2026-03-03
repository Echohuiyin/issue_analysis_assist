from django.test import TestCase
from django.utils import timezone
from cases.models import KernelCase

class KernelCaseModelTest(TestCase):
    """Test KernelCase model functionality"""

    def setUp(self):
        """Create test data before each test method"""
        self.test_case = KernelCase.objects.create(
            case_id="KERNEL-2023-001",
            title="Memory Leak Issue",
            description="System memory usage keeps growing over time",
            symptoms="Memory usage continues to rise, system response slows down, eventually OOM",
            root_cause="Driver did not properly release memory resources",
            solution="Fix the memory management code in the driver",
            kernel_version="5.10.0-1057",
            affected_components="Memory management subsystem, driver",
            severity="High"
        )

    def test_model_creation(self):
        """Test if the model can be created correctly"""
        self.assertEqual(self.test_case.case_id, "KERNEL-2023-001")
        self.assertEqual(self.test_case.title, "Memory Leak Issue")
        self.assertEqual(self.test_case.severity, "High")
        self.assertTrue(isinstance(self.test_case.created_date, timezone.datetime))

    def test_model_string_representation(self):
        """Test if the model's string representation is correct"""
        expected_str = "KERNEL-2023-001: Memory Leak Issue"
        self.assertEqual(str(self.test_case), expected_str)

    def test_unique_case_id(self):
        """Test the unique constraint of case_id"""
        with self.assertRaises(Exception):
            KernelCase.objects.create(
                case_id="KERNEL-2023-001",  # Use an existing case_id
                title="Another Issue",
                description="Test description",
                symptoms="Test symptoms",
                root_cause="Test cause",
                solution="Test solution",
                kernel_version="5.10.0-1057",
                affected_components="Test component",
                severity="Medium"
            )

    def test_update_date(self):
        """测试更新时间是否自动更新"""
        initial_update_date = self.test_case.updated_date
        # 修改案例
        self.test_case.title = "更新后的标题"
        self.test_case.save()
        # 重新获取案例
        updated_case = KernelCase.objects.get(id=self.test_case.id)
        # 验证更新时间已变化
        self.assertNotEqual(initial_update_date, updated_case.updated_date)
        self.assertTrue(updated_case.updated_date > initial_update_date or initial_update_date is None)

    def test_severity_choices(self):
        """测试严重程度的选择值"""
        # 测试有效严重程度
        valid_severities = ["Low", "Medium", "High", "Critical"]
        for severity in valid_severities:
            case = KernelCase.objects.create(
                case_id=f"TEST-{severity}",
                title=f"测试{severity}",
                description="测试描述",
                symptoms="测试症状",
                root_cause="测试原因",
                solution="测试解决方案",
                kernel_version="5.10.0-1057",
                affected_components="测试组件",
                severity=severity
            )
            self.assertEqual(case.severity, severity)
        # 注意：Django的CharField没有内置的choices验证，所以测试会通过任何字符串值