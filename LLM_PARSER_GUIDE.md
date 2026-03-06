# LLM智能解析器使用指南

## 概述

本文档介绍如何使用基于大语言模型（LLM）的智能解析器，以及新的质量评估标准。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置LLM API

选择以下任一方式配置LLM：

#### 方式一：使用OpenAI API
```bash
export OPENAI_API_KEY='your-openai-api-key'
# 可选：自定义API端点
export OPENAI_BASE_URL='https://api.openai.com/v1'
```

#### 方式二：使用DeepSeek API
```bash
export DEEPSEEK_API_KEY='your-deepseek-api-key'
```

#### 方式三：不配置（使用Mock模式）
如果不配置API密钥，系统会自动使用Mock模式进行测试。

### 3. 使用LLM解析器

```python
from cases.acquisition.llm_parser import LLMParser

# 创建解析器实例
parser = LLMParser(llm_type="auto")  # 自动选择可用的LLM

# 解析内容
content = """
Linux内核panic问题分析

问题现象：
系统运行一段时间后出现kernel panic，错误信息如下：
[12345.678901] BUG: unable to handle kernel NULL pointer dereference
[12345.678902] IP: [<ffffffffa0123456>] driver_probe+0x56/0x100

问题分析过程：
1. 首先检查内核日志，发现空指针解引用错误
2. 分析调用栈，定位到driver_probe函数
3. 使用gdb调试内核模块，发现指针未初始化

根本原因：
驱动程序在probe函数中没有对device结构体指针进行NULL检查。

解决方案：
在driver_probe函数中添加NULL指针检查：
if (!device || !device->private_data) {
    return -EINVAL;
}
"""

# 使用LLM解析
case_data = parser.parse(content, use_llm=True)

print(f"标题: {case_data['title']}")
print(f"现象: {case_data['phenomenon']}")
print(f"关键日志: {case_data.get('key_logs', 'N/A')}")
print(f"分析过程: {case_data.get('analysis_process', 'N/A')}")
print(f"根因: {case_data['root_cause']}")
print(f"解决方案: {case_data['solution']}")
print(f"置信度: {case_data.get('confidence', 0):.2f}")
```

### 4. 使用质量验证器

```python
from cases.acquisition.validators import CaseValidator

validator = CaseValidator()

# 验证案例质量
validation_result = validator.validate(case_data)

print(f"验证通过: {validation_result['is_valid']}")
print(f"高质量案例: {validation_result.get('is_high_quality', False)}")
print(f"质量分数: {validation_result['quality_score']:.1f}/100")

# 查看各字段分数
for field, score in validation_result.get('quality_scores', {}).items():
    print(f"  {field}: {score:.1f}")

# 查看警告
if validation_result.get('warnings'):
    print("警告:")
    for warning in validation_result['warnings']:
        print(f"  - {warning}")
```

## 高质量案例标准

### 标准定义

高质量案例必须同时满足以下三个条件：

1. **问题现象描述清晰准确**
   - 包含具体症状（如：系统崩溃、死机、卡顿）
   - 包含错误信息（如：error, fail, crash, panic）
   - 包含错误模式（如：十六进制地址、调用栈）

2. **有描述问题现象的关键日志提供**
   - 包含日志关键词（log, error, trace, kernel等）
   - 包含典型日志格式（时间戳、寄存器信息等）
   - 日志长度足够（至少50字符）

3. **提供了问题分析思路或较为详细的问题分析过程**
   - 包含分析关键词（分析、排查、定位、调试等）
   - 包含分析步骤（第一步、首先、然后等）
   - 分析过程长度足够（至少100字符）

### 质量评分权重

```
标题 (title): 10%
现象描述 (phenomenon): 25%
关键日志 (key_logs): 20%
分析过程 (analysis_process): 20%
根本原因 (root_cause): 15%
解决方案 (solution): 10%
```

### 高质量案例判断

```python
is_high_quality = (
    overall_score >= 70 and
    quality_scores.get("phenomenon", 0) >= 60 and
    quality_scores.get("key_logs", 0) >= 50 and
    quality_scores.get("analysis_process", 0) >= 50
)
```

## 示例：高质量案例 vs 低质量案例

### 高质量案例示例

```python
{
    "title": "Linux内核panic - 空指针解引用问题分析",
    "phenomenon": "系统运行一段时间后出现kernel panic，错误信息如下：\n[12345.678901] BUG: unable to handle kernel NULL pointer dereference at 0000000000000008\n[12345.678902] IP: [<ffffffffa0123456>] driver_probe+0x56/0x100\n[12345.678903] Oops: 0002 [#1] SMP",
    "key_logs": "[12345.678901] BUG: unable to handle kernel NULL pointer dereference\n[12345.678902] IP: [<ffffffffa0123456>] driver_probe+0x56/0x100\n[12345.678903] Oops: 0002 [#1] SMP",
    "analysis_process": "1. 首先检查内核日志，发现空指针解引用错误\n2. 分析调用栈，定位到driver_probe函数\n3. 使用gdb调试内核模块，发现指针未初始化\n4. 检查驱动代码，发现probe函数中缺少NULL检查",
    "root_cause": "驱动程序在probe函数中没有对device结构体指针进行NULL检查，直接访问了device->private_data成员，导致空指针解引用。",
    "solution": "在driver_probe函数中添加NULL指针检查：\nif (!device || !device->private_data) {\n    dev_err(dev, \"Invalid device pointer\\n\");\n    return -EINVAL;\n}",
    "confidence": 0.9
}
```

**质量评估结果**：
- 验证状态: ✓ 通过
- 高质量案例: ✓ 是
- 质量分数: 85.0/100
- 现象描述: 80分（包含具体错误信息）
- 关键日志: 90分（包含典型日志格式）
- 分析过程: 85分（包含清晰的分析步骤）

### 低质量案例示例

```python
{
    "title": "Linux内核问题",
    "phenomenon": "系统有问题。",
    "key_logs": "",
    "analysis_process": "",
    "root_cause": "见文章详情。",
    "solution": "见文章详情。",
    "confidence": 0.3
}
```

**质量评估结果**：
- 验证状态: ✗ 失败
- 高质量案例: ✗ 否
- 质量分数: 15.0/100
- 错误: 现象过短、缺少关键日志、缺少分析过程、根因是fallback值、解决方案是fallback值

## 运行测试

### 测试LLM解析器

```bash
python test_llm_parser.py
```

### 测试质量验证器

```bash
python manage.py test cases.tests.test_acquisition -v 2
```

## 最佳实践

### 1. 提示词优化

LLM解析器的效果很大程度上取决于提示词质量。建议：

- 明确指定提取字段的要求
- 提供示例说明什么是高质量内容
- 要求LLM评估内容质量并设置confidence分数

### 2. 内容预处理

在调用LLM之前，建议对内容进行预处理：

- 清理HTML标签，保留纯文本
- 提取主要内容区域（article, .content等）
- 限制内容长度（建议8000字符以内）

### 3. 质量过滤

使用质量评估结果进行过滤：

```python
# 只保留高质量案例
if validation_result['is_valid'] and validation_result.get('is_high_quality'):
    # 存储到数据库
    storage.store(case_data)
else:
    # 记录低质量案例，用于后续分析
    logger.warning(f"Low quality case: {case_data['title']}")
```

### 4. 成本控制

LLM API调用有成本，建议：

- 使用缓存避免重复解析相同内容
- 批量处理案例，减少API调用次数
- 选择性价比高的LLM（如DeepSeek）

## 故障排查

### 问题1：LLM API调用失败

**症状**：提示"OpenAI API调用失败"或"DeepSeek API调用失败"

**解决方案**：
1. 检查API密钥是否正确设置
2. 检查网络连接
3. 检查API配额是否用尽
4. 尝试使用Mock模式测试

### 问题2：解析结果为空

**症状**：`parser.parse()` 返回 None

**解决方案**：
1. 检查输入内容是否为空
2. 检查内容长度是否过短（<100字符）
3. 查看错误日志

### 问题3：质量分数过低

**症状**：高质量案例被标记为低质量

**解决方案**：
1. 检查内容是否缺少关键日志或分析过程
2. 调整质量评估标准的阈值
3. 优化LLM提示词，提高提取质量

## 参考资料

- [OpenAI API文档](https://platform.openai.com/docs)
- [DeepSeek API文档](https://platform.deepseek.com/docs)
- [项目需求设计文档](./需求设计文档.md)
- [项目开发设计文档](./开发设计文档.md)
- [项目测试设计文档](./测试设计文档.md)