#!/usr/bin/env python3
"""
测试本地LLM模型

验证：
1. Ollama服务是否可用
2. 本地模型是否能正常调用
3. 案例提取效果
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kernel_cases.settings")
import django
django.setup()

from cases.acquisition.llm_integration import (
    OllamaLLM, 
    QwenLocalLLM, 
    ChatGLMLocalLLM,
    LLMFactory
)
from cases.acquisition.llm_parser import LLMParser
from cases.acquisition.validators import CaseValidator


def _build_benchmark_cases():
    return [
        """
Linux内核panic问题分析
问题现象：
系统运行一段时间后出现kernel panic，错误信息如下：
[12345.678901] BUG: unable to handle kernel NULL pointer dereference at 0000000000000008
[12345.678902] IP: [<ffffffffa0123456>] driver_probe+0x56/0x100
[12345.678903] Oops: 0002 [#1] SMP
环境信息：
Linux version 5.10.0-10-amd64
问题分析过程：
1. 检查内核日志，发现空指针解引用错误
2. 分析调用栈，定位到driver_probe函数
3. 检查驱动代码，发现probe函数中缺少NULL检查
根本原因：
probe函数直接访问了未初始化的device->private_data指针。
解决方案：
在driver_probe函数中增加空指针保护并提前返回错误码。
""",
        """
内核OOM与内存泄漏排查
现象：
业务高峰期机器频繁触发OOM killer，dmesg显示大量page allocation failure。
[2203.12] Out of memory: Killed process 1024 (worker) total-vm:2097152kB
环境：
Linux 5.15.0，x86_64，容器部署
分析过程：
首先观察内存曲线，其次通过kmemleak定位泄漏对象，最后定位到驱动缓存未释放。
根因：
缓存生命周期管理错误导致对象长期无法回收。
方案：
修复引用计数，并在卸载路径补充kfree逻辑。
""",
    ]


def benchmark_local_llm(parser: LLMParser, validator: CaseValidator, iterations: int = 3) -> dict:
    cases = _build_benchmark_cases()
    latencies = []
    confidences = []
    completeness_scores = []
    quality_scores = []
    success = 0

    for i in range(iterations):
        for content in cases:
            started = time.perf_counter()
            case_data = parser.parse(content, use_llm=True)
            elapsed = time.perf_counter() - started
            latencies.append(elapsed)
            if not case_data:
                continue
            success += 1
            confidences.append(float(case_data.get("confidence", 0.0) or 0.0))
            completeness_scores.append(float(case_data.get("completeness_score", 0.0) or 0.0))
            validation = validator.validate(case_data)
            quality_scores.append(float(validation.get("quality_score", 0.0) or 0.0))

    total = iterations * len(cases)
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0.0
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "runtime_profile": os.getenv("LOCAL_LLM_PROFILE", "ollama_qwen"),
        "llm_backend": parser.llm.__class__.__name__,
        "total_cases": total,
        "parsed_cases": success,
        "success_rate": round((success / total) * 100 if total else 0.0, 2),
        "avg_latency_sec": round(avg_latency, 3),
        "avg_confidence": round(avg_confidence, 3),
        "avg_completeness": round(avg_completeness, 2),
        "avg_quality_score": round(avg_quality, 2),
    }


def write_benchmark_report(report: dict):
    output_dir = Path(__file__).resolve().parent / "benchmarks"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "local_llm_benchmark_latest.json"
    output_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n基准结果已写入: {output_file}")


def test_ollama():
    """测试Ollama服务"""
    print("\n" + "=" * 80)
    print("测试 Ollama 本地模型")
    print("=" * 80)
    
    llm = OllamaLLM(model="qwen:1.8b")
    
    if llm.is_available():
        print("[OK] Ollama服务可用")
        
        # 测试简单生成
        try:
            response = llm.generate("你好，请用一句话介绍Linux内核。", max_tokens=100)
            print(f"\n模型响应: {response[:200]}...")
            print("[OK] 模型调用成功")
            return True
        except Exception as e:
            print(f"[FAIL] 模型调用失败: {e}")
            return False
    else:
        print("[FAIL] Ollama服务不可用")
        print("\n安装步骤:")
        print("1. 访问 https://ollama.ai/ 下载安装Ollama")
        print("2. 运行: ollama pull qwen:1.8b")
        print("3. 运行: ollama serve")
        return False


def test_transformers():
    """测试Transformers本地模型"""
    print("\n" + "=" * 80)
    print("测试 Transformers 本地模型")
    print("=" * 80)
    
    # 测试Qwen
    print("\n测试 Qwen 模型...")
    qwen = QwenLocalLLM(model_name="Qwen/Qwen1.5-1.8B-Chat")
    
    if qwen.is_available():
        print("[OK] Transformers库已安装")
        print("提示: 首次运行会下载模型（约1.5GB），请耐心等待...")
        
        try:
            response = qwen.generate("你好，请用一句话介绍Linux内核。", max_tokens=100)
            print(f"\n模型响应: {response[:200]}...")
            print("[OK] Qwen模型调用成功")
            return True
        except Exception as e:
            print(f"[FAIL] Qwen模型调用失败: {e}")
            return False
    else:
        print("[FAIL] Transformers库未安装")
        print("安装命令: pip install transformers torch accelerate")
        return False


def test_case_extraction():
    """测试案例提取功能"""
    print("\n" + "=" * 80)
    print("测试案例提取功能")
    print("=" * 80)
    
    # 测试案例
    test_content = """
Linux内核panic问题分析

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
    
    # 使用自动选择的LLM
    parser = LLMParser(llm_type="auto")
    validator = CaseValidator()
    
    print(f"\n当前使用的LLM: {parser.llm.__class__.__name__}")
    
    if not parser.llm.is_available():
        print("[FAIL] 没有可用的LLM，跳过测试")
        return False
    
    try:
        # 解析案例
        case_data = parser.parse(test_content, use_llm=True)
        
        if not case_data:
            print("[FAIL] 解析失败")
            return False
        
        print("\n提取结果:")
        print(f"标题: {case_data.get('title', 'N/A')}")
        print(f"现象: {case_data.get('phenomenon', 'N/A')[:100]}...")
        print(f"关键日志: {case_data.get('key_logs', 'N/A')[:100]}...")
        print(f"分析过程: {case_data.get('analysis_process', 'N/A')[:100]}...")
        print(f"根因: {case_data.get('root_cause', 'N/A')[:100]}...")
        print(f"解决方案: {case_data.get('solution', 'N/A')[:100]}...")
        print(f"置信度: {case_data.get('confidence', 0):.2f}")
        
        # 验证质量
        validation_result = validator.validate(case_data)
        
        print("\n质量验证:")
        print(f"验证状态: {'[OK] 通过' if validation_result['is_valid'] else '[FAIL] 失败'}")
        print(f"高质量案例: {'[OK] 是' if validation_result.get('is_high_quality', False) else '[FAIL] 否'}")
        print(f"质量分数: {validation_result.get('quality_score', 0):.1f}/100")
        
        if validation_result.get('quality_scores'):
            print("各字段分数:")
            for field, score in validation_result['quality_scores'].items():
                print(f"  {field}: {score:.1f}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auto_selection():
    """测试自动选择LLM"""
    print("\n" + "=" * 80)
    print("测试自动选择LLM")
    print("=" * 80)
    
    llm = LLMFactory.create_llm("auto")
    
    print(f"\n自动选择的LLM: {llm.__class__.__name__}")
    
    if llm.is_available():
        print("[OK] LLM可用")
        
        try:
            response = llm.generate("测试：1+1等于几？", max_tokens=50)
            print(f"响应: {response[:100]}")
            return True
        except Exception as e:
            print(f"[FAIL] 调用失败: {e}")
            return False
    else:
        print("[FAIL] LLM不可用")
        return False


def main():
    """主函数"""
    print("=" * 80)
    print("本地LLM模型测试")
    print("=" * 80)
    
    results = {}
    
    # 测试自动选择
    results['auto_selection'] = test_auto_selection()
    
    # 测试Ollama
    results['ollama'] = test_ollama()
    
    # 测试Transformers（可选）
    # results['transformers'] = test_transformers()
    
    # 测试案例提取
    if any(results.values()):
        results['case_extraction'] = test_case_extraction()
    else:
        print("\n跳过案例提取测试（没有可用的LLM）")
        results['case_extraction'] = False

    benchmark_report = None
    if results.get('case_extraction'):
        print("\n" + "=" * 80)
        print("执行可复现基准测试")
        print("=" * 80)
        parser = LLMParser(llm_type="auto")
        validator = CaseValidator()
        benchmark_report = benchmark_local_llm(parser, validator, iterations=2)
        write_benchmark_report(benchmark_report)
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    for test_name, result in results.items():
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")
    if benchmark_report:
        print("\n基准摘要:")
        print(f"  运行路径: {benchmark_report['runtime_profile']}")
        print(f"  后端: {benchmark_report['llm_backend']}")
        print(f"  平均延迟: {benchmark_report['avg_latency_sec']}s/案例")
        print(f"  平均置信度: {benchmark_report['avg_confidence']}")
        print(f"  平均完整率: {benchmark_report['avg_completeness']}")
        print(f"  平均质量分: {benchmark_report['avg_quality_score']}")
    
    if passed == 0:
        print("\n" + "=" * 80)
        print("没有可用的LLM，请按照以下步骤安装：")
        print("=" * 80)
        print("\n推荐方式（Ollama）:")
        print("1. 访问 https://ollama.ai/ 下载安装Ollama")
        print("2. 运行: ollama pull qwen:1.8b")
        print("3. 运行: ollama serve")
        print("4. 重新运行此测试脚本")
        print("\n备选方式（Transformers）:")
        print("pip install transformers torch accelerate")
    else:
        print("\n可复现运行建议:")
        print("1. set LOCAL_LLM_PROFILE=ollama_qwen")
        print("2. set OLLAMA_MODEL=qwen:1.8b")
        print("3. ollama serve")
        print("4. python test_local_llm.py")


if __name__ == "__main__":
    main()