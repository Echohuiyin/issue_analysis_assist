import os
import re
from typing import Dict, List, Optional
from .skill_storage import SKILLStorage

class IssueAnalyzer:
    """
    Class for automated kernel issue analysis using trained SKILL models.
    """
    
    def __init__(self, storage: SKILLStorage):
        """
        Initialize IssueAnalyzer with SKILL storage.
        
        Args:
            storage: SKILLStorage instance for loading trained SKILLs
        """
        self.storage = storage
        self.trained_skills = self._load_skills()
    
    def _load_skills(self) -> Dict[str, Dict]:
        """
        Load all trained SKILLs from storage.
        
        Returns:
            Dictionary of skill_name: skill_data
        """
        skills = {}
        for skill_name in self.storage.list_skills():
            skill_data = self.storage.load_skill(skill_name)
            if skill_data:
                skills[skill_name] = skill_data
        return skills
    
    def analyze_issue(self, issue_description: str, logs: Optional[str] = None) -> Dict:
        """
        Analyze a kernel issue based on description and logs.
        
        Args:
            issue_description: Text description of the issue
            logs: Optional log content related to the issue
            
        Returns:
            Dictionary containing analysis results
        """
        # Combine all input data
        input_data = issue_description
        if logs:
            input_data += "\n\nRelevant Logs:\n" + logs
        
        # Determine which SKILLs to use based on keywords in the issue description
        relevant_skills = self._find_relevant_skills(issue_description)
        
        # Analyze with each relevant SKILL
        analysis_results = []
        for skill_name, skill_data in relevant_skills.items():
            result = self._apply_skill(skill_name, skill_data, input_data)
            analysis_results.append(result)
        
        # Generate overall analysis summary
        summary = self._generate_summary(analysis_results)
        
        return {
            "issue_description": issue_description,
            "logs_provided": logs is not None,
            "relevant_skills_used": list(relevant_skills.keys()),
            "detailed_analysis": analysis_results,
            "summary": summary,
            "confidence_score": self._calculate_confidence(analysis_results)
        }
    
    def _find_relevant_skills(self, issue_description: str) -> Dict[str, Dict]:
        """
        Find relevant SKILLs based on keywords in the issue description.
        
        Args:
            issue_description: Text description of the issue
            
        Returns:
            Dictionary of relevant skill_name: skill_data
        """
        relevant_skills = {}
        
        # If no skills are trained, return empty dict
        if not self.trained_skills:
            return relevant_skills
        
        # Check each skill for relevance
        for skill_name, skill_data in self.trained_skills.items():
            # Check if skill name is in the issue description
            if skill_name in issue_description.lower():
                relevant_skills[skill_name] = skill_data
                continue
            
            # Check if any keywords from the skill prompt are in the issue description
            prompt = skill_data.get("prompt", "")
            # Extract potential keywords from prompt (simplified approach)
            keywords = re.findall(r'\b\w+\b', prompt.lower())
            # Filter out common words
            common_words = set(["analyze", "the", "following", "issue", "and", "provide", "root", "cause", "solution"])
            keywords = [k for k in keywords if k not in common_words and len(k) > 3]
            
            # Check if any keywords match
            for keyword in keywords:
                if keyword in issue_description.lower():
                    relevant_skills[skill_name] = skill_data
                    break
        
        # If no relevant skills found, use all skills as fallback
        if not relevant_skills:
            relevant_skills = self.trained_skills
        
        return relevant_skills
    
    def _apply_skill(self, skill_name: str, skill_data: Dict, input_data: str) -> Dict:
        """
        Apply a specific SKILL to analyze the issue.
        
        Args:
            skill_name: Name of the SKILL to apply
            skill_data: SKILL data dictionary
            input_data: Combined issue description and logs
            
        Returns:
            Dictionary containing analysis results for this SKILL
        """
        # In a real implementation, this would use an LLM to generate analysis
        # based on the skill's prompt and the input data
        
        # For now, we'll simulate the analysis
        prompt = skill_data.get("prompt", "")
        
        # Simple simulated analysis based on skill type
        if "panic" in skill_name:
            root_cause = "Potential kernel panic due to null pointer dereference or memory corruption"
            solution = "Check kernel logs for panic details, analyze crash dumps, and verify relevant drivers or kernel modules"
            troubleshooting_steps = [
                "Examine complete kernel panic log for stack trace",
                "Identify the specific kernel function where panic occurred",
                "Check for recent kernel updates or driver changes",
                "Test with different kernel versions if possible"
            ]
        elif "memory_leak" in skill_name:
            root_cause = "Potential memory leak in kernel subsystem or device driver"
            solution = "Use memory profiling tools like kmemleak to identify leaked objects and fix the memory management issue"
            troubleshooting_steps = [
                "Enable kmemleak in kernel configuration",
                "Monitor memory usage over time with 'free' and 'vmstat' commands",
                "Use 'cat /sys/kernel/debug/kmemleak' to see potential leaks",
                "Analyze code paths that allocate but don't free memory"
            ]
        else:
            root_cause = "Potential kernel issue requiring further analysis"
            solution = "Analyze kernel logs, reproduce the issue, and isolate the problematic component"
            troubleshooting_steps = [
                "Collect detailed kernel logs using 'dmesg' and 'journalctl'",
                "Try to reproduce the issue in a controlled environment",
                "Use debugging tools like GDB for kernel debugging if possible",
                "Check for known issues in the specific kernel version"
            ]
        
        return {
            "skill_name": skill_name,
            "skill_version": skill_data.get("version", "1.0"),
            "prompt_used": prompt,
            "root_cause_analysis": root_cause,
            "suggested_solution": solution,
            "troubleshooting_steps": troubleshooting_steps,
            "confidence": 0.75  # Simulated confidence score
        }
    
    def _generate_summary(self, analysis_results: List[Dict]) -> str:
        """
        Generate a summary of the analysis results from all SKILLs.
        
        Args:
            analysis_results: List of analysis results from each SKILL
            
        Returns:
            Summary text
        """
        if not analysis_results:
            return "No analysis results available. Please ensure SKILLs are properly trained."
        
        # Extract common themes from analysis results
        root_causes = set()
        solutions = set()
        
        for result in analysis_results:
            root_causes.add(result["root_cause_analysis"])
            solutions.add(result["suggested_solution"])
        
        # Generate summary text
        summary = "## Kernel Issue Analysis Summary\n\n"
        
        summary += "### Identified Root Causes\n"
        for i, cause in enumerate(root_causes, 1):
            summary += f"{i}. {cause}\n"
        
        summary += "\n### Recommended Solutions\n"
        for i, solution in enumerate(solutions, 1):
            summary += f"{i}. {solution}\n"
        
        summary += "\n### Key Troubleshooting Steps\n"
        # Combine unique troubleshooting steps
        all_steps = set()
        for result in analysis_results:
            for step in result["troubleshooting_steps"]:
                all_steps.add(step)
        
        for i, step in enumerate(all_steps, 1):
            summary += f"{i}. {step}\n"
        
        return summary
    
    def _calculate_confidence(self, analysis_results: List[Dict]) -> float:
        """
        Calculate overall confidence score based on individual SKILL confidences.
        
        Args:
            analysis_results: List of analysis results from each SKILL
            
        Returns:
            Overall confidence score (0-1)
        """
        if not analysis_results:
            return 0.0
        
        total_confidence = sum(result.get("confidence", 0.0) for result in analysis_results)
        return total_confidence / len(analysis_results)
    
    def upload_log_file(self, file_path: str) -> str:
        """
        Upload and parse a log file.
        
        Args:
            file_path: Path to the log file
            
        Returns:
            Parsed log content as string
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Log file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            raise IOError(f"Error reading log file: {str(e)}")
    
    def extract_relevant_logs(self, logs: str, issue_description: str) -> str:
        """
        Extract relevant log sections based on the issue description.
        
        Args:
            logs: Full log content
            issue_description: Issue description to find relevance
            
        Returns:
            Extracted relevant log sections
        """
        # Extract potential keywords from issue description
        keywords = re.findall(r'\b\w+\b', issue_description.lower())
        common_words = set(["the", "and", "or", "a", "an", "in", "on", "at", "to", "for"])
        keywords = [k for k in keywords if k not in common_words and len(k) > 3]
        
        # If no keywords found, return first 20 lines as sample
        if not keywords:
            return '\n'.join(logs.split('\n')[:20])
        
        # Extract lines containing any of the keywords
        relevant_lines = []
        lines = logs.split('\n')
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in keywords):
                # Include some context (2 lines before and after)
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                relevant_lines.extend(lines[start:end])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_lines = []
        for line in relevant_lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
        
        return '\n'.join(unique_lines)