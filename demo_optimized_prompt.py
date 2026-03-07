#!/usr/bin/env python3
"""Demonstration of the optimized extraction prompt"""

print("=" * 80)
print("Optimized LLM Extraction Prompt Demonstration")
print("=" * 80)

# Original test content from test_local_llm.py
test_content = """Linux内核panic问题分析

问题现象：
系统运行一段时间后出现kernel panic，错误信息如下：
[12345.678901] BUG: unable to handle kernel NULL pointer dereference at 0000000000000008
[12345.678902] IP: [<ffffffffa0123456>] driver_probe+0x56/0x100
[12345.678903] Oops: 0002 [#1] SMP 

环境信息：
Linux version 5.10.0-10-amd64
x86_64 GNU/Linux

问题分析过程：
1. 首先检查内核日志，发现空指针解引用错误
2. 分析调用栈，定位到driver_probe函数
3. 使用gdb调试内核模块，发现指针未初始化
4. 检查驱动代码，发现probe函数中缺少NULL检查

根本原因：
驱动程序在probe函数中没有对device结构体指针进行NULL检查，直接访问了device->private_data成员，导致空指针解引用。

解决方案：
在driver_probe函数中添加NULL指针检查：
if (!device || !device->private_data) {
    dev_err(dev, "Invalid device pointer\n");
    return -EINVAL;
}

预防措施：
1. 所有指针使用前必须进行NULL检查
2. 使用静态分析工具检查代码
3. 添加单元测试覆盖异常路径
"""

print("\nOriginal Test Content:")
print("-" * 40)
print(test_content[:300] + "...")

print("\n" + "=" * 80)
print("Optimized Extraction Prompt:")
print("=" * 80)

optimized_prompt = """你是一名Linux内核专家，请阅读以下技术文章，提取结构化案例信息。

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

print(optimized_prompt)

print("\n" + "=" * 80)
print("Expected Improved Output:")
print("=" * 80)

# Example of what the improved output should look like
expected_output = {
    "title": "Linux内核panic问题分析",
    "phenomenon": "系统运行一段时间后出现kernel panic，发生空指针解引用错误",
    "key_logs": "[12345.678901] BUG: unable to handle kernel NULL pointer dereference at 0000000000000008\n[12345.678902] IP: [<ffffffffa0123456>] driver_probe+0x56/0x100\n[12345.678903] Oops: 0002 [#1] SMP",
    "environment": "Linux version 5.10.0-10-amd64 x86_64 GNU/Linux",
    "root_cause": "驱动程序在probe函数中没有对device结构体指针进行NULL检查，直接访问了device->private_data成员，导致空指针解引用",
    "analysis_process": "1. 首先检查内核日志，发现空指针解引用错误\n2. 分析调用栈，定位到driver_probe函数\n3. 使用gdb调试内核模块，发现指针未初始化\n4. 检查驱动代码，发现probe函数中缺少NULL检查",
    "troubleshooting_steps": ["检查内核日志，发现空指针解引用错误", "分析调用栈，定位到driver_probe函数", "使用gdb调试内核模块，发现指针未初始化", "检查驱动代码，发现probe函数中缺少NULL检查"],
    "solution": "在driver_probe函数中添加NULL指针检查：if (!device || !device->private_data) { dev_err(dev, \"Invalid device pointer\\n\"); return -EINVAL; }",
    "prevention": "1. 所有指针使用前必须进行NULL检查\n2. 使用静态分析工具检查代码\n3. 添加单元测试覆盖异常路径",
    "confidence": 0.9
}

import json
print(json.dumps(expected_output, indent=2, ensure_ascii=False))

print("\n" + "=" * 80)
print("Improvements from Optimized Prompt:")
print("=" * 80)
print("1. Simplified prompt structure for better JSON generation")
print("2. Clearer instructions on field requirements")
print("3. Focus on valid JSON output")
print("4. Explicit handling for missing information")
print("5. More direct language to avoid confusion")
print("6. Improved formatting to guide proper JSON structure")