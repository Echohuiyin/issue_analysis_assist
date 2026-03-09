import re
from typing import Dict, List, Optional, Tuple


class CaseValidator:
    """Validator for kernel case data with content quality checks
    
    高质量案例标准：
    1. 问题现象描述清晰准确（包含具体症状、错误信息）
    2. 有描述问题现象的关键日志提供
    3. 提供了问题分析思路或较为详细的问题分析过程
    """
    
    KERNEL_KEYWORDS = [
        "kernel", "linux", "内核", "驱动", "driver", "panic", "oops",
        "memory", "内存", "lock", "锁", "network", "网络", "scheduler",
        "调度", "interrupt", "中断", "crash", "崩溃", "bug", "error",
        "错误", "issue", "问题", "fault", "故障"
    ]
    
    PHENOMENON_KEYWORDS = [
        "现象", "症状", "问题", "错误", "失败", "异常", "崩溃", "死机",
        "panic", "error", "fail", "crash", "issue", "bug", "exception",
        "hang", "freeze", "timeout", "超时", "leak", "泄漏"
    ]
    
    ROOT_CAUSE_KEYWORDS = [
        "原因", "根因", "分析", "导致", "引起", "由于", "因为",
        "cause", "root", "analysis", "due to", "because", "issue",
        "problem", "bug", "缺陷", "漏洞", "错误"
    ]
    
    SOLUTION_KEYWORDS = [
        "解决", "修复", "方案", "方法", "补丁", "更新", "修改", "配置",
        "solution", "fix", "patch", "update", "modify", "config", "set",
        "change", "resolve", "workaround"
    ]
    
    # 关键日志关键词
    LOG_KEYWORDS = [
        "log", "日志", "error", "错误", "warning", "警告", "panic",
        "trace", "stack", "call trace", "backtrace", "dump", "crash",
        "kernel", "dmesg", "syslog", "message", "output", "输出",
        "printk", "console", "控制台"
    ]
    
    # 分析过程关键词
    ANALYSIS_KEYWORDS = [
        "分析", "排查", "定位", "调试", "调查", "检查", "追踪",
        "analysis", "debug", "investigate", "trace", "locate", "check",
        "发现", "找到", "确定", "确认", "验证", "测试", "test",
        "步骤", "step", "过程", "process", "方法", "method"
    ]
    
    FALLBACK_PATTERNS = [
        r"^See\s+(article|forum|StackOverflow)",
        r"^See\s+\w+\s+for\s+(details|solution)",
        r"^See\s+\w+\s+discussion",
    ]

    # Project-level quality gate: scores below this are considered invalid.
    QUALITY_PASS_SCORE = 80
    
    def __init__(self):
        self.required_fields = [
            "title",
            "phenomenon",
            "environment",
            "root_cause",
            "troubleshooting_steps",
            "solution"
        ]
        
        self.min_lengths = {
            "title": 10,
            "phenomenon": 20,
            "root_cause": 20,
            "solution": 20
        }
        
        self.max_lengths = {
            "title": 200,
            "phenomenon": 2000,
            "root_cause": 2000,
            "solution": 2000
        }
    
    def validate(self, case_data: Dict) -> Dict:
        """Validate case data and return validation result"""
        is_valid = True
        errors = []
        warnings = []
        
        for field in self.required_fields:
            if field not in case_data or not case_data[field]:
                is_valid = False
                errors.append(f"Required field '{field}' is missing or empty")
        
        if "troubleshooting_steps" in case_data:
            if not isinstance(case_data["troubleshooting_steps"], list):
                is_valid = False
                errors.append("'troubleshooting_steps' must be a list")
        
        quality_result = self.validate_content_quality(case_data)
        if not quality_result["is_valid"]:
            is_valid = False
            errors.extend(quality_result["errors"])
        warnings.extend(quality_result.get("warnings", []))
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "quality_score": quality_result.get("quality_score", 0),
            "is_high_quality": quality_result.get("is_high_quality", False),
            "quality_scores": quality_result.get("quality_scores", {}),
            "low_quality_flags": quality_result.get("low_quality_flags", []),
        }
    
    def validate_content_quality(self, case_data: Dict) -> Dict:
        """Validate content quality of parsed case data
        
        高质量案例标准：
        1. 问题现象描述清晰准确（包含具体症状、错误信息）
        2. 有描述问题现象的关键日志提供
        3. 提供了问题分析思路或较为详细的问题分析过程
        """
        errors = []
        warnings = []
        quality_scores = {}
        low_quality_flags = []
        
        # 1. 验证标题
        title_result = self._validate_title(case_data.get("title", ""))
        quality_scores["title"] = title_result["score"]
        if not title_result["is_valid"]:
            errors.extend(title_result["errors"])
        warnings.extend(title_result.get("warnings", []))
        
        # 2. 验证现象描述（重点：清晰准确）
        phenomenon_result = self._validate_phenomenon(case_data.get("phenomenon", ""))
        quality_scores["phenomenon"] = phenomenon_result["score"]
        if not phenomenon_result["is_valid"]:
            errors.extend(phenomenon_result["errors"])
        warnings.extend(phenomenon_result.get("warnings", []))
        
        # 3. 验证关键日志（新增）
        key_logs_result = self._validate_key_logs(case_data.get("key_logs", ""), case_data.get("phenomenon", ""))
        quality_scores["key_logs"] = key_logs_result["score"]
        if not key_logs_result["is_valid"]:
            warnings.extend(key_logs_result.get("warnings", []))
        
        # 4. 验证分析过程（新增）
        analysis_result = self._validate_analysis_process(
            case_data.get("analysis_process", ""),
            case_data.get("root_cause", "")
        )
        quality_scores["analysis_process"] = analysis_result["score"]
        if not analysis_result["is_valid"]:
            warnings.extend(analysis_result.get("warnings", []))
        
        # 5. 验证根因
        root_cause_result = self._validate_root_cause(case_data.get("root_cause", ""))
        quality_scores["root_cause"] = root_cause_result["score"]
        if not root_cause_result["is_valid"]:
            errors.extend(root_cause_result["errors"])
        warnings.extend(root_cause_result.get("warnings", []))
        
        # 6. 验证解决方案
        solution_result = self._validate_solution(case_data.get("solution", ""))
        quality_scores["solution"] = solution_result["score"]
        if not solution_result["is_valid"]:
            errors.extend(solution_result["errors"])
        warnings.extend(solution_result.get("warnings", []))

        # 7. 字段完整性严格检查（新增）
        completeness_result = self._validate_field_completeness(case_data)
        quality_scores["completeness"] = completeness_result["score"]
        if not completeness_result["is_valid"]:
            errors.extend(completeness_result.get("errors", []))
        warnings.extend(completeness_result.get("warnings", []))
        low_quality_flags.extend(completeness_result.get("flags", []))
        
        # 计算总体质量分数（加权平均）
        weights = {
            "title": 0.1,
            "phenomenon": 0.25,  # 现象描述权重提高
            "key_logs": 0.2,     # 关键日志权重
            "analysis_process": 0.2,  # 分析过程权重
            "root_cause": 0.15,
            "solution": 0.1
        }
        
        overall_score = sum(
            quality_scores.get(field, 0) * weight
            for field, weight in weights.items()
        ) + quality_scores.get("completeness", 0) * 0.1
        
        # 判断是否为高质量案例
        is_high_quality = (
            overall_score >= self.QUALITY_PASS_SCORE and
            quality_scores.get("phenomenon", 0) >= 60 and
            quality_scores.get("key_logs", 0) >= 50 and
            quality_scores.get("analysis_process", 0) >= 50
        )
        
        return {
            "is_valid": len(errors) == 0,
            "is_high_quality": is_high_quality,
            "errors": errors,
            "warnings": warnings,
            "quality_scores": quality_scores,
            "quality_score": min(100, overall_score),
            "low_quality_flags": sorted(list(dict.fromkeys(low_quality_flags))),
        }

    def _validate_field_completeness(self, case_data: Dict) -> Dict:
        """Strict field-level completeness checks with low-quality flags."""
        errors = []
        warnings = []
        flags = []

        required = {
            "phenomenon": 40,
            "key_logs": 30,
            "analysis_process": 40,
            "root_cause": 40,
            "solution": 40,
        }

        fulfilled = 0
        for field, min_len in required.items():
            value = str(case_data.get(field, "") or "").strip()
            if value and len(value) >= min_len and not self._is_fallback_content(value):
                fulfilled += 1
            else:
                flags.append(f"{field}_incomplete")
                if field in ("phenomenon", "root_cause", "solution"):
                    errors.append(f"Field '{field}' is incomplete (min {min_len} chars, non-fallback required)")
                else:
                    warnings.append(f"Field '{field}' is incomplete (min {min_len} chars recommended)")

        score = int((fulfilled / len(required)) * 100)
        is_valid = fulfilled >= 3 and not any(f in flags for f in ["phenomenon_incomplete", "root_cause_incomplete", "solution_incomplete"])
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "flags": flags,
            "score": score,
        }
    
    def _validate_title(self, title: str) -> Dict:
        """Validate title quality"""
        errors = []
        warnings = []
        score = 0
        
        if not title:
            errors.append("Title is empty")
            return {"is_valid": False, "errors": errors, "warnings": warnings, "score": 0}
        
        if len(title) < self.min_lengths["title"]:
            errors.append(f"Title too short (min {self.min_lengths['title']} chars): '{title}'")
            return {"is_valid": False, "errors": errors, "warnings": warnings, "score": 0}
        
        if len(title) > self.max_lengths["title"]:
            warnings.append(f"Title too long, will be truncated to {self.max_lengths['title']} chars")
        
        score += 20
        
        has_kernel_keyword = any(kw.lower() in title.lower() for kw in self.KERNEL_KEYWORDS)
        if has_kernel_keyword:
            score += 40
        else:
            warnings.append("Title doesn't contain kernel-related keywords")
        
        if not self._is_fallback_content(title):
            score += 40
        else:
            errors.append("Title appears to be a fallback value, not actual content")
            return {"is_valid": False, "errors": errors, "warnings": warnings, "score": 0}
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "score": min(score, 100)
        }
    
    def _validate_phenomenon(self, phenomenon: str) -> Dict:
        """Validate phenomenon quality
        
        高质量标准：问题现象描述清晰准确，包含具体症状、错误信息
        """
        errors = []
        warnings = []
        score = 0
        
        if not phenomenon:
            errors.append("Phenomenon is empty")
            return {"is_valid": False, "errors": errors, "warnings": warnings, "score": 0}
        
        if len(phenomenon) < self.min_lengths["phenomenon"]:
            errors.append(f"Phenomenon too short (min {self.min_lengths['phenomenon']} chars)")
            return {"is_valid": False, "errors": errors, "warnings": warnings, "score": 0}
        
        # 基础分数
        score += 20
        
        # 检查是否包含问题相关关键词
        has_phenomenon_keyword = any(kw.lower() in phenomenon.lower() for kw in self.PHENOMENON_KEYWORDS)
        if has_phenomenon_keyword:
            score += 30
        else:
            warnings.append("Phenomenon doesn't contain problem-related keywords")
        
        # 检查是否包含具体错误信息（新增）
        error_patterns = [
            r'error[:\s]', r'错误[:\s]', r'fail[s]?[ed]?', r'失败',
            r'panic', r'crash', r'崩溃', r'exception', r'异常',
            r'\[.*?\]',  # 方括号内容，如 [  123.456789]
            r'0x[0-9a-fA-F]+',  # 十六进制地址
            r'BUG:', r'WARNING:', r'Oops'
        ]
        
        has_error_info = any(re.search(pattern, phenomenon, re.IGNORECASE) for pattern in error_patterns)
        if has_error_info:
            score += 30
        else:
            warnings.append("Phenomenon doesn't contain specific error information")
        
        # 检查是否为fallback值
        if not self._is_fallback_content(phenomenon):
            score += 20
        else:
            errors.append("Phenomenon appears to be a fallback value")
            return {"is_valid": False, "errors": errors, "warnings": warnings, "score": 0}
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "score": min(score, 100)
        }
    
    def _validate_key_logs(self, key_logs: str, phenomenon: str = "") -> Dict:
        """Validate key logs quality
        
        高质量标准：有描述问题现象的关键日志提供
        """
        warnings = []
        score = 0
        
        # 如果没有单独的key_logs字段，检查phenomenon中是否包含日志
        combined_text = f"{key_logs}\n{phenomenon}" if key_logs and phenomenon else key_logs or phenomenon
        
        if not combined_text:
            warnings.append("No key logs provided")
            return {"is_valid": False, "warnings": warnings, "score": 0}
        
        # 基础分数
        score += 10
        
        # 检查是否包含日志关键词
        has_log_keyword = any(kw.lower() in combined_text.lower() for kw in self.LOG_KEYWORDS)
        if has_log_keyword:
            score += 30
        else:
            warnings.append("No log-related keywords found")
        
        # 检查是否包含典型的日志格式
        log_patterns = [
            r'\[\s*\d+\.\d+\]',  # [  123.456789] 时间戳格式
            r'kernel:', r'内核:',
            r'Call Trace:', r'调用栈:',
            r'RIP:', r'RSP:', r'RBP:',  # 寄存器信息
            r'Comm:', r'PID:',  # 进程信息
            r'\d{4}-\d{2}-\d{2}',  # 日期格式
            r'\d{2}:\d{2}:\d{2}',  # 时间格式
        ]
        
        has_log_format = any(re.search(pattern, combined_text, re.IGNORECASE) for pattern in log_patterns)
        if has_log_format:
            score += 40
        else:
            warnings.append("No typical log format found")
        
        # 检查日志长度
        if len(key_logs) >= 100:
            score += 20
        elif len(key_logs) >= 50:
            score += 10
        
        return {
            "is_valid": score >= 50,
            "warnings": warnings,
            "score": min(score, 100)
        }
    
    def _validate_analysis_process(self, analysis_process: str, root_cause: str = "") -> Dict:
        """Validate analysis process quality
        
        高质量标准：提供了问题分析思路或较为详细的问题分析过程
        """
        warnings = []
        score = 0
        
        # 合并analysis_process和root_cause进行分析
        combined_text = f"{analysis_process}\n{root_cause}" if analysis_process and root_cause else analysis_process or root_cause
        
        if not combined_text:
            warnings.append("No analysis process provided")
            return {"is_valid": False, "warnings": warnings, "score": 0}
        
        # 基础分数
        score += 10
        
        # 检查是否包含分析关键词
        has_analysis_keyword = any(kw.lower() in combined_text.lower() for kw in self.ANALYSIS_KEYWORDS)
        if has_analysis_keyword:
            score += 30
        else:
            warnings.append("No analysis-related keywords found")
        
        # 检查是否包含分析步骤
        step_patterns = [
            r'第一步', r'第二步', r'第三步',
            r'first', r'second', r'third',
            r'step\s*\d+', r'步骤\s*\d+',
            r'1\.', r'2\.', r'3\.',  # 列表格式
            r'首先', r'然后', r'接着', r'最后',
        ]
        
        has_steps = any(re.search(pattern, combined_text, re.IGNORECASE) for pattern in step_patterns)
        if has_steps:
            score += 30
        else:
            warnings.append("No clear analysis steps found")
        
        # 检查分析过程长度
        if len(analysis_process) >= 200:
            score += 30
        elif len(analysis_process) >= 100:
            score += 20
        elif len(analysis_process) >= 50:
            score += 10
        
        return {
            "is_valid": score >= 50,
            "warnings": warnings,
            "score": min(score, 100)
        }
    
    def _validate_root_cause(self, root_cause: str) -> Dict:
        """Validate root cause quality"""
        errors = []
        warnings = []
        score = 0
        
        if not root_cause:
            errors.append("Root cause is empty")
            return {"is_valid": False, "errors": errors, "warnings": warnings, "score": 0}
        
        if len(root_cause) < self.min_lengths["root_cause"]:
            errors.append(f"Root cause too short (min {self.min_lengths['root_cause']} chars)")
            return {"is_valid": False, "errors": errors, "warnings": warnings, "score": 0}
        
        score += 20
        
        has_cause_keyword = any(kw.lower() in root_cause.lower() for kw in self.ROOT_CAUSE_KEYWORDS)
        if has_cause_keyword:
            score += 40
        else:
            warnings.append("Root cause doesn't contain analysis-related keywords")
        
        if not self._is_fallback_content(root_cause):
            score += 40
        else:
            errors.append("Root cause appears to be a fallback value")
            return {"is_valid": False, "errors": errors, "warnings": warnings, "score": 0}
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "score": min(score, 100)
        }
    
    def _validate_solution(self, solution: str) -> Dict:
        """Validate solution quality"""
        errors = []
        warnings = []
        score = 0
        
        if not solution:
            errors.append("Solution is empty")
            return {"is_valid": False, "errors": errors, "warnings": warnings, "score": 0}
        
        if len(solution) < self.min_lengths["solution"]:
            errors.append(f"Solution too short (min {self.min_lengths['solution']} chars)")
            return {"is_valid": False, "errors": errors, "warnings": warnings, "score": 0}
        
        score += 20
        
        has_solution_keyword = any(kw.lower() in solution.lower() for kw in self.SOLUTION_KEYWORDS)
        if has_solution_keyword:
            score += 40
        else:
            warnings.append("Solution doesn't contain fix-related keywords")
        
        if not self._is_fallback_content(solution):
            score += 40
        else:
            errors.append("Solution appears to be a fallback value")
            return {"is_valid": False, "errors": errors, "warnings": warnings, "score": 0}
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "score": min(score, 100)
        }
    
    def _is_fallback_content(self, text: str) -> bool:
        """Check if text is a fallback value"""
        if not text:
            return True
        
        for pattern in self.FALLBACK_PATTERNS:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        return False


case_validator = CaseValidator()