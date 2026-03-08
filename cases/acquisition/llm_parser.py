"""
基于LLM的智能内容解析器
使用大语言模型理解全文内容，提取结构化案例信息
"""

import json
import re
from typing import Dict, Optional, List
from bs4 import BeautifulSoup

from .llm_integration import get_llm


class LLMParser:
    """基于LLM的智能解析器"""
    
    # 提取案例信息的提示词模板
    EXTRACTION_PROMPT = """请仔细阅读以下技术文章内容，提取Linux内核问题的结构化案例信息。

文章内容：
{content}

请按照以下格式提取信息，以JSON格式返回：

{{
    "title": "问题标题（简洁明确，包含关键问题）",
    "module": "所属内核模块（memory/network/scheduler/lock/timer/storage/irq/driver/other）",
    "phenomenon": "问题现象描述（包括：具体症状、错误信息、关键日志片段）",
    "key_logs": "关键日志或错误信息（如果有）",
    "environment": "环境信息（内核版本、系统版本、硬件平台等）",
    "root_cause": "根本原因分析（详细说明导致问题的根本原因）",
    "analysis_process": "问题分析思路和过程（如何定位到问题）",
    "related_code": "关联内核代码（函数、调用链、关键代码片段）",
    "troubleshooting_steps": ["排查步骤1", "排查步骤2", "..."],
    "solution": "解决方案（具体的修复方法、代码修改或配置调整）",
    "fix_code": "修复代码（若文章中提供了补丁/代码修改，尽量完整摘录）",
    "prevention": "预防措施（如果文章中有提到）",
    "confidence": 0.8
}}

要求（必须严格执行）：
1. phenomenon字段必须包含具体的问题描述，不能只是"见文章"之类的占位符
2. key_logs字段要提取文章中提到的关键日志、错误信息或调用栈
3. root_cause要详细说明问题的根本原因，不能只说"见文章"
4. analysis_process要描述问题分析的思路和方法
5. troubleshooting_steps要列出具体的排查步骤
6. solution要提供具体的解决方案，不能只是"见文章"
7. 如果文章内容不足或无法提取有效信息，confidence设为0.3以下
8. 如果是高质量案例（问题清晰、分析详细、方案明确），confidence设为0.8以上
9. 若某字段缺失，请填写"Not specified"，禁止使用"见文章/see article/参考原文"
10. key_logs优先包含可定位问题的原始日志片段（如 panic/oops/Call Trace/寄存器或错误码）
11. related_code尽量提取函数名、调用链、关键代码，若无则填"Not specified"
12. fix_code仅在有明确修复片段时填写，否则填"Not specified"

请只返回JSON，不要添加其他说明文字。"""

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

    def __init__(self, llm_type: str = "auto"):
        """
        初始化LLM解析器
        
        Args:
            llm_type: LLM类型 ("openai", "deepseek", "mock", "auto")
        """
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
            "module": "other",
            "phenomenon": text_content[:500],
            "environment": "Not specified",
            "root_cause": "Not specified",
            "analysis_process": "Not specified",
            "related_code": "Not specified",
            "troubleshooting_steps": ["Not specified"],
            "solution": "Not specified",
            "fix_code": "Not specified",
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
        required_fields = ["title", "module", "phenomenon", "root_cause", "analysis_process", "solution"]
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

        # 规范文本、补齐关键日志，并输出字段完整性指标。
        text_fields = [
            "title", "module", "phenomenon", "key_logs", "environment",
            "root_cause", "analysis_process", "related_code", "solution", "fix_code", "prevention"
        ]
        for field in text_fields:
            if field in case_data and case_data[field] is not None:
                case_data[field] = self._normalize_text(str(case_data[field]))

        # Persist analysis alias for storage and downstream retrieval.
        case_data["problem_analysis"] = case_data.get("analysis_process", "Not specified")

        if not case_data.get("key_logs"):
            case_data["key_logs"] = self._extract_key_logs_from_text(
                f"{case_data.get('phenomenon', '')}\n{case_data.get('analysis_process', '')}\n{case_data.get('root_cause', '')}"
            )

        case_data["completeness_score"] = self._completeness_score(case_data)
        case_data["low_quality_flags"] = self._low_quality_flags(case_data)
        
        return case_data

    def _normalize_text(self, text: str) -> str:
        text = re.sub(r"\s+\n", "\n", text).strip()
        text = re.sub(r"\n{3,}", "\n\n", text)
        placeholders = [
            r"^see article.*$",
            r"^see .* for details.*$",
            r"^见文章.*$",
            r"^参考原文.*$",
        ]
        for pattern in placeholders:
            if re.match(pattern, text, re.IGNORECASE):
                return "Not specified"
        return text

    def _extract_key_logs_from_text(self, text: str) -> str:
        if not text:
            return ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        patterns = [
            r"panic", r"oops", r"call trace", r"bug:", r"warning:",
            r"null pointer", r"segfault", r"unable to handle", r"0x[0-9a-f]+",
            r"\[\s*\d+\.\d+\]",
        ]
        matched = []
        for line in lines:
            lowered = line.lower()
            if any(re.search(p, lowered, re.IGNORECASE) for p in patterns):
                matched.append(line)
            if len(matched) >= 6:
                break
        return "\n".join(matched)[:1200]

    def _completeness_score(self, case_data: Dict) -> float:
        weighted = {
            "phenomenon": 0.25,
            "key_logs": 0.2,
            "analysis_process": 0.2,
            "root_cause": 0.2,
            "solution": 0.15,
        }
        score = 0.0
        for field, weight in weighted.items():
            value = str(case_data.get(field, "") or "")
            if len(value) >= 40 and value != "Not specified":
                score += weight * 100
            elif len(value) >= 15 and value != "Not specified":
                score += weight * 60
        return round(score, 1)

    def _low_quality_flags(self, case_data: Dict) -> List[str]:
        flags = []
        for field in ["phenomenon", "root_cause", "solution"]:
            value = str(case_data.get(field, "") or "")
            if len(value) < 30 or value == "Not specified":
                flags.append(f"{field}_too_short_or_missing")

        if len(str(case_data.get("key_logs", "") or "")) < 30:
            flags.append("key_logs_missing")
        if len(str(case_data.get("analysis_process", "") or "")) < 40:
            flags.append("analysis_process_missing")

        confidence = float(case_data.get("confidence", 0.5) or 0.5)
        if confidence < 0.4:
            flags.append("low_confidence")

        return flags
    
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
            "suggestions": [],
            "completeness_score": case_data.get("completeness_score", self._completeness_score(case_data)),
            "low_quality_flags": case_data.get("low_quality_flags", self._low_quality_flags(case_data)),
        }


# 创建全局实例
llm_parser = LLMParser()