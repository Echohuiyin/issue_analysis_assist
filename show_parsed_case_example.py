#!/usr/bin/env python3
"""Demonstration of what a parsed case looks like after local LLM processing"""

print("=" * 80)
print("Example: Parsed Kernel Case Structure After Local LLM Processing")
print("=" * 80)

# Example of what a parsed case would look like after LLM processing
parsed_case = {
    "title": "Linux内核NULL指针解引用导致panic",
    "phenomenon": "系统运行时突然崩溃，出现kernel panic错误，错误信息显示在驱动代码中发生了NULL指针解引用。",
    "key_logs": "[12345.678901] BUG: unable to handle kernel NULL pointer dereference at 0000000000000008\n[12345.678902] IP: [<ffffffffa0123456>] driver_probe+0x56/0x100\n[12345.678903] Oops: 0002 [#1] SMP",
    "analysis_process": "1. 检查内核日志，发现NULL指针解引用错误\n2. 分析调用栈，定位到driver_probe函数\n3. 使用gdb调试内核模块，发现指针未初始化\n4. 检查驱动代码，发现probe函数中缺少NULL检查",
    "root_cause": "驱动程序在probe函数中没有对device结构体指针进行NULL检查，直接访问了device->private_data成员，导致NULL指针解引用。",
    "solution": "在driver_probe函数中添加NULL指针检查：\nif (!device || !device->private_data) {\n    dev_err(dev, \"Invalid device pointer\\n\");\n    return -EINVAL;\n}",
    "confidence": 0.85,
    "environment": "Linux version 5.10.0-10-amd64 x86_64 GNU/Linux",
    "kernel_version": "5.10.0-10-amd64",
    "affected_components": "network driver",
    "severity": "High",
    "source": "test",
    "tags": ["kernel panic", "null pointer", "driver", "memory"]
}

# Display the parsed case structure
print("\nParsed Case Fields:")
print("-" * 40)
for key, value in parsed_case.items():
    if key == "solution":
        # Format code nicely
        print(f"{key}:\n{value}")
    elif key == "analysis_process":
        print(f"{key}:\n{value}")
    else:
        print(f"{key}: {value}")

print("\n" + "=" * 80)
print("Field Explanations:")
print("=" * 80)
print("- title: 问题标题（简洁明确）")
print("- phenomenon: 问题现象描述")
print("- key_logs: 关键错误日志")
print("- analysis_process: 问题分析思路和方法")
print("- root_cause: 根本原因分析")
print("- solution: 解决方案（可能包含代码修改）")
print("- confidence: LLM提取的置信度分数")
print("- environment: 运行环境信息")
print("- kernel_version: 内核版本")
print("- affected_components: 受影响的组件")
print("- severity: 问题严重程度")
print("- source: 数据来源")
print("- tags: 相关标签")

print("\n" + "=" * 80)
print("How Local LLM Parsing Works:")
print("=" * 80)
print("1. 输入原始文本内容（包含问题描述、日志等）")
print("2. 使用Ollama本地模型（qwen:1.8b）进行自然语言理解")
print("3. 提取结构化信息到上述字段")
print("4. 生成置信度分数")
print("5. 数据存储到数据库")