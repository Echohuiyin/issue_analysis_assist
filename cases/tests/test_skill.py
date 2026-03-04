import os
import json
import unittest
import tempfile
from unittest.mock import patch, MagicMock
from cases.analysis.skill_storage import SKILLStorage
from cases.analysis.skill_trainer import SKILLTrainer
from cases.models import KernelCase

class TestSKILLStorage(unittest.TestCase):
    """
    Test cases for the SKILLStorage class.
    """
    
    def setUp(self):
        """
        Set up test environment.
        """
        # Create a temporary directory for storage
        self.temp_dir = tempfile.mkdtemp()
        self.storage = SKILLStorage(storage_dir=self.temp_dir)
        
        # Sample SKILL data
        self.sample_skill = {
            "name": "test skill",  # Changed to match symptoms format
            "description": "Test SKILL for analysis",
            "prompt": "Analyze the following data:",
            "version": "1.0"
        }
    
    def tearDown(self):
        """
        Clean up test environment.
        """
        # Remove temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_skill(self):
        """
        Test that SKILL can be saved and loaded successfully.
        """
        # Save SKILL
        saved = self.storage.save_skill("test_skill", self.sample_skill)
        self.assertTrue(saved)
        
        # Check if file exists
        skill_path = os.path.join(self.temp_dir, "test_skill.json")
        self.assertTrue(os.path.exists(skill_path))
        
        # Load SKILL and verify content
        loaded_skill = self.storage.load_skill("test_skill")
        self.assertEqual(loaded_skill, self.sample_skill)
    
    def test_load_nonexistent_skill(self):
        """
        Test that loading a nonexistent SKILL returns None.
        """
        loaded_skill = self.storage.load_skill("nonexistent_skill")
        self.assertIsNone(loaded_skill)
    
    def test_save_and_load_model(self):
        """
        Test that a model can be saved and loaded successfully.
        """
        # Sample model (just a simple dictionary for testing)
        sample_model = {"weights": [0.1, 0.2, 0.3], "bias": 0.0}
        
        # Save model
        saved = self.storage.save_model("test_model", sample_model)
        self.assertTrue(saved)
        
        # Check if file exists
        model_path = os.path.join(self.temp_dir, "test_model.pkl")
        self.assertTrue(os.path.exists(model_path))
        
        # Load model and verify content
        loaded_model = self.storage.load_model("test_model")
        self.assertEqual(loaded_model, sample_model)
    
    def test_list_skills(self):
        """
        Test that list_skills returns all saved SKILLs.
        """
        # Save multiple SKILLs
        skills = [
            ("skill1", {"name": "skill1", "version": "1.0"}),
            ("skill2", {"name": "skill2", "version": "1.0"}),
            ("skill3", {"name": "skill3", "version": "1.0"})
        ]
        
        for skill_name, skill_data in skills:
            self.storage.save_skill(skill_name, skill_data)
        
        # List SKILLs
        listed_skills = self.storage.list_skills()
        
        # Verify all saved SKILLs are listed
        self.assertEqual(len(listed_skills), 3)
        for skill_name, _ in skills:
            self.assertIn(skill_name, listed_skills)
    
    def test_delete_skill(self):
        """
        Test that a SKILL can be deleted successfully.
        """
        # Save SKILL and model
        self.storage.save_skill("test_skill", self.sample_skill)
        self.storage.save_model("test_skill", {"weights": [0.1]})
        
        # Delete SKILL
        deleted = self.storage.delete_skill("test_skill")
        self.assertTrue(deleted)
        
        # Verify files are deleted
        skill_path = os.path.join(self.temp_dir, "test_skill.json")
        model_path = os.path.join(self.temp_dir, "test_skill.pkl")
        self.assertFalse(os.path.exists(skill_path))
        self.assertFalse(os.path.exists(model_path))
        
        # Verify SKILL is no longer listed
        listed_skills = self.storage.list_skills()
        self.assertNotIn("test_skill", listed_skills)

class TestSKILLTrainer(unittest.TestCase):
    """
    Test cases for the SKILLTrainer class.
    """
    
    def setUp(self):
        """
        Set up test environment.
        """
        # Create a temporary directory for storage
        self.temp_dir = tempfile.mkdtemp()
        self.storage = SKILLStorage(storage_dir=self.temp_dir)
        self.trainer = SKILLTrainer(storage=self.storage)
        
        # Create sample community skills directory
        self.community_skills_path = os.path.join(self.temp_dir, "community_skills")
        os.makedirs(self.community_skills_path)
        self.trainer.community_skills_path = self.community_skills_path
        
        # Sample SKILL data
        self.sample_skill = {
            "name": "test skill",  # Changed to match symptoms format
            "description": "Test SKILL for analysis",
            "prompt": "Analyze the following data:",
            "version": "1.0"
        }
        
        # Save sample community skill
        skill_path = os.path.join(self.community_skills_path, "test_skill.json")
        with open(skill_path, "w", encoding="utf-8") as f:
            json.dump(self.sample_skill, f)
        
        # Create mock KernelCase objects
        self.mock_case1 = MagicMock(spec=KernelCase)
        self.mock_case1.case_id = "case1"
        self.mock_case1.title = "Test Case 1"
        self.mock_case1.symptoms = "Test skill issue detected"
        self.mock_case1.root_cause = "Root cause 1"
        self.mock_case1.solution = "Solution 1"
        
        self.mock_case2 = MagicMock(spec=KernelCase)
        self.mock_case2.case_id = "case2"
        self.mock_case2.title = "Test Case 2"
        self.mock_case2.symptoms = "Different issue detected"
        self.mock_case2.root_cause = "Root cause 2"
        self.mock_case2.solution = "Solution 2"
    
    def tearDown(self):
        """
        Clean up test environment.
        """
        # Remove temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_community_skill(self):
        """
        Test that community SKILL can be loaded successfully.
        """
        # Load community SKILL
        loaded_skill = self.trainer.load_community_skill("test_skill")
        self.assertEqual(loaded_skill, self.sample_skill)
    
    def test_load_nonexistent_community_skill(self):
        """
        Test that loading a nonexistent community SKILL returns an empty dict.
        """
        loaded_skill = self.trainer.load_community_skill("nonexistent_skill")
        self.assertEqual(loaded_skill, {})
    
    def test_evaluate_skill(self):
        """
        Test that SKILL can be evaluated against test cases.
        """
        test_cases = [self.mock_case1, self.mock_case2]
        
        # Evaluate SKILL
        accuracy, results = self.trainer.evaluate_skill(self.sample_skill, test_cases)
        
        # Check accuracy
        self.assertEqual(accuracy, 0.5)  # Only case1 should match
        
        # Check results
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]["prediction_correct"])
        self.assertFalse(results[1]["prediction_correct"])
    
    def test_optimize_skill(self):
        """
        Test that SKILL can be optimized based on evaluation results.
        """
        test_cases = [self.mock_case1, self.mock_case2]
        evaluation_results = [
            {"prediction_correct": True, "case_id": "case1"},
            {"prediction_correct": False, "case_id": "case2"}
        ]
        
        # Optimize SKILL
        optimized_skill = self.trainer.optimize_skill(self.sample_skill, test_cases, evaluation_results)
        
        # Check that skill was optimized
        self.assertEqual(optimized_skill["version"], "1.1")
        self.assertIn("Examples to learn from:", optimized_skill["prompt"])
    
    @patch.object(KernelCase.objects, 'all')
    def test_train_skill(self, mock_all):
        """
        Test that SKILL can be trained successfully.
        """
        # Mock database query
        mock_all.return_value = [self.mock_case1, self.mock_case2]
        
        # Train SKILL
        trained_skill = self.trainer.train_skill("test_skill")
        
        # Check that SKILL was optimized (accuracy should be 0.5 < 0.8)
        self.assertEqual(trained_skill["version"], "1.1")
        
        # Check that optimized SKILL was saved
        loaded_skill = self.storage.load_skill("test_skill")
        self.assertEqual(loaded_skill, trained_skill)
    
    def test_download_community_skills(self):
        """
        Test that community SKILLs can be downloaded.
        """
        # Clear existing community skills
        for filename in os.listdir(self.community_skills_path):
            os.remove(os.path.join(self.community_skills_path, filename))
        
        # Download community skills
        self.trainer.download_community_skills()
        
        # Check if skills were downloaded
        files = os.listdir(self.community_skills_path)
        self.assertGreater(len(files), 0)
        self.assertIn("kernel_panic_analysis.json", files)
        self.assertIn("memory_leak_detection.json", files)

if __name__ == '__main__':
    unittest.main()