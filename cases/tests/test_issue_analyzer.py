import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import the class to test
from cases.analysis.issue_analyzer import IssueAnalyzer

class TestIssueAnalyzer(unittest.TestCase):
    """Test the IssueAnalyzer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a mock SKILLStorage
        self.mock_storage = MagicMock()
        
        # Mock skill data
        self.mock_skills = {
            "kernel_panic_analysis": {
                "name": "kernel_panic_analysis",
                "version": "1.0",
                "prompt": "Analyze the following kernel panic issue and provide root cause analysis, solution, and troubleshooting steps.",
                "training_cases": [],
                "evaluation_metrics": {"accuracy": 0.85},
                "model_path": None
            },
            "memory_leak_detection": {
                "name": "memory_leak_detection",
                "version": "1.0",
                "prompt": "Analyze the following memory leak issue and provide root cause analysis, solution, and troubleshooting steps.",
                "training_cases": [],
                "evaluation_metrics": {"accuracy": 0.80},
                "model_path": None
            }
        }
        
        # Configure the mock storage
        self.mock_storage.list_skills.return_value = list(self.mock_skills.keys())
        self.mock_storage.load_skill.side_effect = lambda name: self.mock_skills.get(name)
        
        # Create the analyzer instance
        self.analyzer = IssueAnalyzer(self.mock_storage)
    
    def test_initialization(self):
        """Test that the analyzer initializes correctly"""
        self.assertEqual(len(self.analyzer.trained_skills), 2)
        self.assertIn("kernel_panic_analysis", self.analyzer.trained_skills)
        self.assertIn("memory_leak_detection", self.analyzer.trained_skills)
    
    def test_find_relevant_skills(self):
        """Test that relevant skills are found based on issue description"""
        # Test with kernel panic issue
        panic_issue = "System crashes with kernel panic due to null pointer dereference"
        relevant_skills = self.analyzer._find_relevant_skills(panic_issue)
        self.assertIn("kernel_panic_analysis", relevant_skills)
        
        # Test with memory leak issue
        leak_issue = "System memory usage keeps increasing over time"
        relevant_skills = self.analyzer._find_relevant_skills(leak_issue)
        self.assertIn("memory_leak_detection", relevant_skills)
    
    def test_analyze_issue_without_logs(self):
        """Test issue analysis without logs"""
        issue_description = "Kernel panic due to null pointer dereference"
        result = self.analyzer.analyze_issue(issue_description)
        
        self.assertEqual(result["issue_description"], issue_description)
        self.assertFalse(result["logs_provided"])
        self.assertIn("kernel_panic_analysis", result["relevant_skills_used"])
        self.assertIsInstance(result["detailed_analysis"], list)
        self.assertGreater(len(result["detailed_analysis"]), 0)
        self.assertIsInstance(result["summary"], str)
        self.assertGreater(len(result["summary"]), 0)
        self.assertGreaterEqual(result["confidence_score"], 0.0)
        self.assertLessEqual(result["confidence_score"], 1.0)
    
    def test_analyze_issue_with_logs(self):
        """Test issue analysis with logs"""
        issue_description = "Kernel panic due to null pointer dereference"
        logs = "[12345.678901] BUG: kernel NULL pointer dereference, address: 0000000000000008"
        
        result = self.analyzer.analyze_issue(issue_description, logs)
        
        self.assertEqual(result["issue_description"], issue_description)
        self.assertTrue(result["logs_provided"])
        self.assertIn("kernel_panic_analysis", result["relevant_skills_used"])
        self.assertIsInstance(result["detailed_analysis"], list)
        self.assertGreater(len(result["detailed_analysis"]), 0)
        self.assertIsInstance(result["summary"], str)
        self.assertGreater(len(result["summary"]), 0)
    
    def test_upload_log_file(self):
        """Test log file upload functionality"""
        # Create a temporary log file
        test_log_content = "Test log content\nLine 2\nLine 3"
        test_file_path = "test_log.txt"
        
        try:
            with open(test_file_path, 'w') as f:
                f.write(test_log_content)
            
            # Test upload
            uploaded_content = self.analyzer.upload_log_file(test_file_path)
            self.assertEqual(uploaded_content, test_log_content)
            
        finally:
            # Clean up
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
    
    def test_upload_log_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent files"""
        with self.assertRaises(FileNotFoundError):
            self.analyzer.upload_log_file("non_existent_file.txt")
    
    def test_extract_relevant_logs(self):
        """Test that relevant logs are extracted based on issue description"""
        full_logs = """[12345.678901] Normal log line
[12345.678902] BUG: kernel NULL pointer dereference, address: 0000000000000008
[12345.678903] Another normal log line
[12345.678904] #PF: supervisor read access in kernel mode
[12345.678905] Final normal log line"""
        
        issue_description = "Kernel panic due to null pointer dereference"
        relevant_logs = self.analyzer.extract_relevant_logs(full_logs, issue_description)
        
        # Check that relevant lines are included
        self.assertIn("NULL pointer dereference", relevant_logs)
        self.assertIn("#PF: supervisor read access", relevant_logs)
        
        # Check that the result is a string
        self.assertIsInstance(relevant_logs, str)
    
    def test_apply_skill(self):
        """Test that skills are applied correctly"""
        skill_name = "kernel_panic_analysis"
        skill_data = self.mock_skills[skill_name]
        input_data = "Kernel panic issue description"
        
        result = self.analyzer._apply_skill(skill_name, skill_data, input_data)
        
        self.assertEqual(result["skill_name"], skill_name)
        self.assertEqual(result["skill_version"], "1.0")
        self.assertEqual(result["prompt_used"], skill_data["prompt"])
        self.assertIsInstance(result["root_cause_analysis"], str)
        self.assertIsInstance(result["suggested_solution"], str)
        self.assertIsInstance(result["troubleshooting_steps"], list)
        self.assertGreater(len(result["troubleshooting_steps"]), 0)
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)
    
    def test_generate_summary(self):
        """Test that analysis summary is generated correctly"""
        # Create mock analysis results
        analysis_results = [
            {
                "skill_name": "kernel_panic_analysis",
                "skill_version": "1.0",
                "prompt_used": "Test prompt",
                "root_cause_analysis": "Test root cause 1",
                "suggested_solution": "Test solution 1",
                "troubleshooting_steps": ["Step 1", "Step 2"],
                "confidence": 0.85
            },
            {
                "skill_name": "memory_leak_detection",
                "skill_version": "1.0",
                "prompt_used": "Test prompt",
                "root_cause_analysis": "Test root cause 2",
                "suggested_solution": "Test solution 2",
                "troubleshooting_steps": ["Step 3", "Step 4"],
                "confidence": 0.80
            }
        ]
        
        summary = self.analyzer._generate_summary(analysis_results)
        
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)
        self.assertIn("Test root cause 1", summary)
        self.assertIn("Test root cause 2", summary)
        self.assertIn("Test solution 1", summary)
        self.assertIn("Test solution 2", summary)
        self.assertIn("Step 1", summary)
        self.assertIn("Step 3", summary)
    
    def test_calculate_confidence(self):
        """Test that confidence score is calculated correctly"""
        # Test with multiple results
        analysis_results = [
            {"confidence": 0.85},
            {"confidence": 0.80},
            {"confidence": 0.90}
        ]
        
        confidence = self.analyzer._calculate_confidence(analysis_results)
        self.assertEqual(confidence, (0.85 + 0.80 + 0.90) / 3)
        
        # Test with empty results
        confidence = self.analyzer._calculate_confidence([])
        self.assertEqual(confidence, 0.0)

if __name__ == '__main__':
    unittest.main()