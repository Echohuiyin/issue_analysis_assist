import os
import json
import pickle
from typing import Dict, Optional, List

class SKILLStorage:
    """
    Class for storing and retrieving SKILL models and related data.
    """
    
    def __init__(self, storage_dir: str = "skills"):
        """
        Initialize SKILLStorage with storage directory.
        
        Args:
            storage_dir: Directory to store SKILL models and data
        """
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def save_skill(self, skill_name: str, skill_data: Dict) -> bool:
        """
        Save SKILL data to storage.
        
        Args:
            skill_name: Name of the SKILL
            skill_data: Dictionary containing SKILL information and model
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            skill_path = os.path.join(self.storage_dir, f"{skill_name}.json")
            with open(skill_path, "w", encoding="utf-8") as f:
                json.dump(skill_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving SKILL {skill_name}: {e}")
            return False
    
    def load_skill(self, skill_name: str) -> Optional[Dict]:
        """
        Load SKILL data from storage.
        
        Args:
            skill_name: Name of the SKILL to load
            
        Returns:
            SKILL data dictionary if found, None otherwise
        """
        try:
            skill_path = os.path.join(self.storage_dir, f"{skill_name}.json")
            if not os.path.exists(skill_path):
                return None
                
            with open(skill_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading SKILL {skill_name}: {e}")
            return None
    
    def save_model(self, model_name: str, model) -> bool:
        """
        Save machine learning model using pickle.
        
        Args:
            model_name: Name of the model
            model: The model object to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            model_path = os.path.join(self.storage_dir, f"{model_name}.pkl")
            with open(model_path, "wb") as f:
                pickle.dump(model, f)
            return True
        except Exception as e:
            print(f"Error saving model {model_name}: {e}")
            return False
    
    def load_model(self, model_name: str):
        """
        Load machine learning model from pickle file.
        
        Args:
            model_name: Name of the model to load
            
        Returns:
            The model object if found, None otherwise
        """
        try:
            model_path = os.path.join(self.storage_dir, f"{model_name}.pkl")
            if not os.path.exists(model_path):
                return None
                
            with open(model_path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            return None
    
    def list_skills(self) -> List[str]:
        """
        List all available SKILLs in storage.
        
        Returns:
            List of SKILL names
        """
        skills = []
        try:
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    skill_name = filename[:-5]  # Remove .json extension
                    skills.append(skill_name)
        except Exception as e:
            print(f"Error listing SKILLs: {e}")
        return skills
    
    def delete_skill(self, skill_name: str) -> bool:
        """
        Delete SKILL and associated model.
        
        Args:
            skill_name: Name of the SKILL to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Delete SKILL data file
            skill_path = os.path.join(self.storage_dir, f"{skill_name}.json")
            if os.path.exists(skill_path):
                os.remove(skill_path)
            
            # Delete associated model if exists
            model_path = os.path.join(self.storage_dir, f"{skill_name}.pkl")
            if os.path.exists(model_path):
                os.remove(model_path)
            
            return True
        except Exception as e:
            print(f"Error deleting SKILL {skill_name}: {e}")
            return False