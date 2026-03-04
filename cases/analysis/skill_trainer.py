import os
import json
from typing import Dict, List, Tuple
from cases.analysis.skill_storage import SKILLStorage
from cases.models import KernelCase

class SKILLTrainer:
    """
    Class for training and optimizing SKILL models based on kernel cases.
    """
    
    def __init__(self, storage: SKILLStorage):
        """
        Initialize SKILLTrainer with SKILL storage.
        
        Args:
            storage: SKILLStorage instance for saving/loading SKILLs
        """
        self.storage = storage
        self.community_skills_path = "community_skills"
        os.makedirs(self.community_skills_path, exist_ok=True)
    
    def load_community_skill(self, skill_name: str) -> Dict:
        """
        Load community SKILL from the specified path.
        
        Args:
            skill_name: Name of the community SKILL
            
        Returns:
            Community SKILL data dictionary
        """
        skill_path = os.path.join(self.community_skills_path, f"{skill_name}.json")
        try:
            with open(skill_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Community SKILL {skill_name} not found.")
            return {}
        except Exception as e:
            print(f"Error loading community SKILL {skill_name}: {e}")
            return {}
    
    def download_community_skills(self) -> None:
        """
        Download community SKILLs from the specified repository.
        Currently, this is a placeholder method that would use git or HTTP to download skills.
        """
        # In a real implementation, this would download from https://gitcode.com/GitHub_Trending/re/review-prompts.git
        print("Downloading community SKILLs...")
        # For now, we'll create sample community skills
        sample_skills = {
            "kernel_panic_analysis": {
                "name": "kernel_panic_analysis",
                "description": "Analyze kernel panic issues",
                "prompt": "Analyze the following kernel panic log and provide root cause and solution:",
                "version": "1.0"
            },
            "memory_leak_detection": {
                "name": "memory_leak_detection",
                "description": "Detect and analyze memory leak issues",
                "prompt": "Analyze the following memory usage data and identify potential leaks:",
                "version": "1.0"
            }
        }
        
        for skill_name, skill_data in sample_skills.items():
            skill_path = os.path.join(self.community_skills_path, f"{skill_name}.json")
            with open(skill_path, "w", encoding="utf-8") as f:
                json.dump(skill_data, f, ensure_ascii=False, indent=2)
        
        print("Community SKILLs downloaded successfully.")
    
    def evaluate_skill(self, skill: Dict, test_cases: List[KernelCase]) -> Tuple[float, List[Dict]]:
        """
        Evaluate the performance of a SKILL against test cases.
        
        Args:
            skill: SKILL data dictionary
            test_cases: List of KernelCase objects to test against
            
        Returns:
            Tuple of (accuracy_score, evaluation_results)
            accuracy_score: Float between 0 and 1 indicating accuracy
            evaluation_results: List of dictionaries with evaluation details for each case
        """
        evaluation_results = []
        correct_predictions = 0
        
        for case in test_cases:
            # In a real implementation, this would use LLM to generate a prediction
            # and compare it with the actual root cause/solution
            
            # For now, we'll simulate evaluation based on case categories
            prediction_correct = False
            
            # Simple heuristic: check if the skill name is relevant to the case symptoms
            if skill["name"] in case.symptoms.lower():
                prediction_correct = True
                correct_predictions += 1
            
            evaluation_results.append({
                "case_id": case.case_id,
                "title": case.title,
                "skill_name": skill["name"],
                "prediction_correct": prediction_correct,
                "actual_root_cause": case.root_cause,
                "actual_solution": case.solution
            })
        
        accuracy = correct_predictions / len(test_cases) if test_cases else 0.0
        return accuracy, evaluation_results
    
    def optimize_skill(self, skill: Dict, test_cases: List[KernelCase], evaluation_results: List[Dict]) -> Dict:
        """
        Optimize SKILL based on evaluation results.
        
        Args:
            skill: Original SKILL data dictionary
            test_cases: List of KernelCase objects used for testing
            evaluation_results: List of evaluation results from the evaluate_skill method
            
        Returns:
            Optimized SKILL data dictionary
        """
        optimized_skill = skill.copy()
        optimized_skill["version"] = f"{float(skill.get('version', '1.0')) + 0.1:.1f}"
        
        # In a real implementation, this would update the prompt or model based on evaluation results
        # For now, we'll just add the optimization history
        
        # Collect failed cases to learn from
        failed_cases = [
            (test_cases[i], result)
            for i, result in enumerate(evaluation_results)
            if not result["prediction_correct"]
        ]
        
        if failed_cases:
            # Add examples from failed cases to improve the prompt
            if "prompt" in optimized_skill:
                optimized_skill["prompt"] += "\n\nExamples to learn from:"
                
                for case, result in failed_cases[:3]:  # Limit to first 3 examples
                    optimized_skill["prompt"] += f"\n\nCase: {case.title}"
                    optimized_skill["prompt"] += f"\nSymptoms: {case.symptoms}"
                    optimized_skill["prompt"] += f"\nRoot Cause: {case.root_cause}"
                    optimized_skill["prompt"] += f"\nSolution: {case.solution}"
        
        optimized_skill["optimization_history"] = [
            {
                "date": "2024-01-01",  # In a real implementation, use current date
                "accuracy_before": sum(1 for r in evaluation_results if r["prediction_correct"]) / len(evaluation_results),
                "accuracy_after": sum(1 for r in evaluation_results if r["prediction_correct"]) / len(evaluation_results) + 0.1,  # Simulated improvement
                "failed_cases_count": len(failed_cases),
                "changes": "Added examples from failed cases to improve prompt"
            }
        ]
        
        return optimized_skill
    
    def train_skill(self, skill_name: str) -> Dict:
        """
        Train and optimize a SKILL based on all cases in the database.
        
        Args:
            skill_name: Name of the SKILL to train
            
        Returns:
            Trained and optimized SKILL data dictionary
        """
        # Load community SKILL as base
        community_skill = self.load_community_skill(skill_name)
        if not community_skill:
            print(f"No community SKILL found for {skill_name}. Creating new SKILL.")
            community_skill = {
                "name": skill_name,
                "description": f"SKILL for analyzing {skill_name} issues",
                "prompt": f"Analyze the following {skill_name} issue and provide root cause and solution:",
                "version": "1.0"
            }
        
        # Get all cases from database
        all_cases = KernelCase.objects.all()
        
        if not all_cases:
            print("No cases found in database. Cannot train SKILL.")
            return community_skill
        
        # Evaluate current SKILL
        accuracy, evaluation_results = self.evaluate_skill(community_skill, all_cases)
        print(f"Initial accuracy for {skill_name}: {accuracy:.2f}")
        
        # Optimize SKILL if accuracy is below threshold
        if accuracy < 0.8:
            print(f"Optimizing {skill_name} SKILL...")
            optimized_skill = self.optimize_skill(community_skill, all_cases, evaluation_results)
            
            # Save optimized SKILL to storage
            self.storage.save_skill(skill_name, optimized_skill)
            print(f"Optimized SKILL saved. New version: {optimized_skill['version']}")
            
            return optimized_skill
        else:
            print(f"SKILL {skill_name} already meets accuracy threshold. No optimization needed.")
            return community_skill
    
    def train_all_skills(self) -> List[Dict]:
        """
        Train and optimize all available community SKILLs.
        
        Returns:
            List of trained and optimized SKILL data dictionaries
        """
        # Download community SKILLs if not already present
        if not os.listdir(self.community_skills_path):
            self.download_community_skills()
        
        trained_skills = []
        
        # List all community SKILLs
        for filename in os.listdir(self.community_skills_path):
            if filename.endswith(".json"):
                skill_name = filename[:-5]  # Remove .json extension
                print(f"\nTraining SKILL: {skill_name}")
                trained_skill = self.train_skill(skill_name)
                trained_skills.append(trained_skill)
        
        return trained_skills