"""
基于LLM的智能内容解析器
使用大语言模型理解全文内容，提取结构化案例信息
"""

import json
import re
from typing import Dict, Optional
from bs4 import BeautifulSoup

from .llm_integration import get_llm


class LLMParser:
    """基于LLM的智能解析器"""
    
    # 提取案例信息的提示词模板
    EXTRACTION_PROMPT = """你是一名Linux内核专家，请阅读以下技术文章，提取结构化案例信息。

文章内容：
{content}

请按照以下格式返回JSON，确保所有字段都有内容，不要使用占位符：
{{
    "title": "直接使用文章标题",
    "phenomenon": "问题现象",
    "key_logs": "关键日志",
    "environment": "环境信息",
    "root_cause": "根本原因",
    "analysis_process": "分析过程",
    "troubleshooting_steps": ["排查步骤1", "步骤2"],
    "solution": "解决方案",
    "prevention": "预防措施",
    "confidence": 0.5
}}

返回要求：
1. 只返回纯JSON，不要包含其他文本
2. JSON必须是有效的
3. 每个字段都要填充实际内容
4. 如果文章中没有相关信息，填写"无"

请立即返回JSON。"""

    # 质量评估提示词
    QUALITY_CHECK_PROMPT = """请评估以下案例信息的质量：

案例信息：
{case_data}

评估标准：
1. 问题现象描述是否清晰准确（包含具体症状、错误信息、关键日志）
2. 是否提供了关键日志或错误信息
3. 是否提供了问题分析思路或较为详细的问题分析过程
4. 解决方案是否具体可行

请返回JSON格式的评估结果：
{{
    "is_high_quality": true/false,
    "quality_score": 0-100,
    "has_key_logs": true/false,
    "has_analysis_process": true/false,
    "phenomenon_quality": "good/medium/poor",
    "solution_quality": "good/medium/poor",
    "issues": ["问题1", "问题2", "..."],
    "suggestions": ["改进建议1", "改进建议2", "..."]
}}

请只返回JSON，不要添加其他说明文字。"""

    def __init__(self, llm_type: str = "auto", model: str = None):
        """
        初始化LLM解析器
        
        Args:
            llm_type: LLM类型 ("openai", "deepseek", "mock", "auto")
            model: 模型名称（如 "qwen:1.8b", "qwen2.5:0.5b"）
        """
        if model:
            self.llm = get_llm(llm_type, model=model)
        else:
            self.llm = get_llm(llm_type)
    
    def parse(self, content: str, use_llm: bool = True) -> Optional[Dict]:
        """
        解析内容，提取结构化案例信息
        
        Args:
            content: HTML或文本内容
            use_llm: 是否使用LLM（False则使用传统规则方法）
            
        Returns:
            结构化的案例数据字典
        """
        if not content:
            return None
        
        # 清理HTML，提取纯文本
        text_content = self._clean_html(content)
        
        if not text_content or len(text_content.strip()) < 100:
            return None
        
        if use_llm and self.llm.is_available():
            return self._parse_with_llm(text_content)
        else:
            return self._parse_with_rules(text_content)
    
    def _clean_html(self, content: str) -> str:
        """清理HTML，提取纯文本"""
        try:
            soup = BeautifulSoup(content, 'lxml')
            
            # 移除不需要的标签
            for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            
            # 尝试找到主要内容区域
            main_content = None
            for selector in ['article', '.article-content', '.post-content', '.blog-content',
                           '.markdown-body', '.content', '#content', 'main']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)
            
            # 清理多余的空行
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)
        
        except Exception as e:
            # 如果BeautifulSoup解析失败，尝试直接返回内容
            return content
    
    def _parse_with_llm(self, text_content: str) -> Optional[Dict]:
        """使用LLM解析内容"""
        try:
            # 限制内容长度，避免超过token限制
            max_chars = 8000
            if len(text_content) > max_chars:
                text_content = text_content[:max_chars] + "\n...(内容已截断)"
            
            # 调用LLM提取信息
            prompt = self.EXTRACTION_PROMPT.format(content=text_content)
            response = self.llm.generate(prompt, max_tokens=2000)
            
            # 解析JSON响应
            case_data = self._parse_json_response(response)
            
            if not case_data:
                return None
            
            # 验证和清理数据
            case_data = self._validate_and_clean(case_data)
            
            return case_data
        
        except Exception as e:
            print(f"LLM解析失败: {str(e)}")
            return None
    
    def _parse_with_rules(self, text_content: str) -> Optional[Dict]:
        """使用传统规则方法解析（作为fallback）"""
        # 提取标题
        lines = text_content.split('\n')
        title = lines[0] if lines else "Unknown"
        
        # 简单提取（这里可以使用原有的BlogParser逻辑）
        return {
            "title": title[:200],
            "phenomenon": text_content[:500],
            "environment": "Not specified",
            "root_cause": "See article for details",
            "troubleshooting_steps": ["See article for details"],
            "solution": "See article for details",
            "confidence": 0.3
        }
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """解析LLM返回的JSON响应"""
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            print(f"无法解析LLM响应为JSON: {response[:200]}...")
            return None
    
    def _validate_and_clean(self, case_data: Dict) -> Dict:
        """验证和清理案例数据"""
        # 确保必要字段存在
        required_fields = ["title", "phenomenon", "root_cause", "solution"]
        for field in required_fields:
            if field not in case_data:
                case_data[field] = f"Not specified"
        
        # 清理字段长度
        if len(case_data.get("title", "")) > 200:
            case_data["title"] = case_data["title"][:200]
        
        if len(case_data.get("phenomenon", "")) > 2000:
            case_data["phenomenon"] = case_data["phenomenon"][:2000]
        
        if len(case_data.get("root_cause", "")) > 2000:
            case_data["root_cause"] = case_data["root_cause"][:2000]
        
        if len(case_data.get("solution", "")) > 2000:
            case_data["solution"] = case_data["solution"][:2000]
        
        # 确保troubleshooting_steps是列表
        if "troubleshooting_steps" not in case_data:
            case_data["troubleshooting_steps"] = []
        elif not isinstance(case_data["troubleshooting_steps"], list):
            case_data["troubleshooting_steps"] = [str(case_data["troubleshooting_steps"])]
        
        # 设置默认confidence
        if "confidence" not in case_data:
            case_data["confidence"] = 0.5
        
        return case_data
    
    def check_quality(self, case_data: Dict) -> Dict:
        """
        使用LLM评估案例质量
        
        Args:
            case_data: 案例数据
            
        Returns:
            质量评估结果
        """
        if not self.llm.is_available():
            # 如果LLM不可用，使用简单规则评估
            return self._simple_quality_check(case_data)
        
        try:
            prompt = self.QUALITY_CHECK_PROMPT.format(case_data=json.dumps(case_data, ensure_ascii=False, indent=2))
            response = self.llm.generate(prompt, max_tokens=1000)
            quality_result = self._parse_json_response(response)
            
            if quality_result:
                return quality_result
            else:
                return self._simple_quality_check(case_data)
        
        except Exception as e:
            print(f"质量评估失败: {str(e)}")
            return self._simple_quality_check(case_data)
    
    def _simple_quality_check(self, case_data: Dict) -> Dict:
        """简单的质量检查（不使用LLM）"""
        issues = []
        quality_score = 0
        
        # 检查现象描述
        phenomenon = case_data.get("phenomenon", "")
        if len(phenomenon) < 50:
            issues.append("现象描述过短")
        elif "see article" in phenomenon.lower() or "见文章" in phenomenon:
            issues.append("现象描述是占位符")
        else:
            quality_score += 25
        
        # 检查关键日志
        key_logs = case_data.get("key_logs", "")
        has_key_logs = len(key_logs) > 20
        if has_key_logs:
            quality_score += 20
        else:
            issues.append("缺少关键日志")
        
        # 检查分析过程
        analysis_process = case_data.get("analysis_process", "")
        has_analysis_process = len(analysis_process) > 50
        if has_analysis_process:
            quality_score += 25
        else:
            issues.append("缺少分析过程")
        
        # 检查解决方案
        solution = case_data.get("solution", "")
        if len(solution) < 50:
            issues.append("解决方案过短")
        elif "see article" in solution.lower() or "见文章" in solution:
            issues.append("解决方案是占位符")
        else:
            quality_score += 30
        
        return {
            "is_high_quality": quality_score >= 70,
            "quality_score": quality_score,
            "has_key_logs": has_key_logs,
            "has_analysis_process": has_analysis_process,
            "phenomenon_quality": "good" if len(phenomenon) >= 100 else "medium" if len(phenomenon) >= 50 else "poor",
            "solution_quality": "good" if len(solution) >= 100 else "medium" if len(solution) >= 50 else "poor",
            "issues": issues,
            "suggestions": []
        }


# 创建全局实例
llm_parser = LLMParser()