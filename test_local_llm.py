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


def test_ollama():
    """测试Ollama服务"""
    print("\n" + "=" * 80)
    print("测试 Ollama 本地模型")
    print("=" * 80)
    
    llm = OllamaLLM(model="qwen:1.8b")
    
    if llm.is_available():
        print("✓ Ollama服务可用")
        
        # 测试简单生成
        try:
            response = llm.generate("你好，请用一句话介绍Linux内核。", max_tokens=100)
            print(f"\n模型响应: {response[:200]}...")
            print("✓ 模型调用成功")
            return True
        except Exception as e:
            print(f"✗ 模型调用失败: {e}")
            return False
    else:
        print("✗ Ollama服务不可用")
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
        print("✓ Transformers库已安装")
        print("提示: 首次运行会下载模型（约1.5GB），请耐心等待...")
        
        try:
            response = qwen.generate("你好，请用一句话介绍Linux内核。", max_tokens=100)
            print(f"\n模型响应: {response[:200]}...")
            print("✓ Qwen模型调用成功")
            return True
        except Exception as e:
            print(f"✗ Qwen模型调用失败: {e}")
            return False
    else:
        print("✗ Transformers库未安装")
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
        print("✗ 没有可用的LLM，跳过测试")
        return False
    
    try:
        # 解析案例
        case_data = parser.parse(test_content, use_llm=True)
        
        if not case_data:
            print("✗ 解析失败")
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
        print(f"验证状态: {'✓ 通过' if validation_result['is_valid'] else '✗ 失败'}")
        print(f"高质量案例: {'✓ 是' if validation_result.get('is_high_quality', False) else '✗ 否'}")
        print(f"质量分数: {validation_result.get('quality_score', 0):.1f}/100")
        
        if validation_result.get('quality_scores'):
            print("各字段分数:")
            for field, score in validation_result['quality_scores'].items():
                print(f"  {field}: {score:.1f}")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
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
        print("✓ LLM可用")
        
        try:
            response = llm.generate("测试：1+1等于几？", max_tokens=50)
            print(f"响应: {response[:100]}")
            return True
        except Exception as e:
            print(f"✗ 调用失败: {e}")
            return False
    else:
        print("✗ LLM不可用")
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
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")
    
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


if __name__ == "__main__":
    main()