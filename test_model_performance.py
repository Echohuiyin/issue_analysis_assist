#!/usr/bin/env python3
"""
性能优化测试脚本
测试不同LLM模型的处理速度和质量
"""
import os
import sys
import time
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
django.setup()

from cases.models import RawCase
from cases.acquisition.llm_parser import LLMParser


MODELS_TO_TEST = [
    'qwen:0.5b',
    'qwen:1.8b',
    'qwen2.5:0.5b',
    'qwen2.5:1.5b',
]

TEST_CASE_COUNT = 3


def test_model_speed(model_name: str, test_cases: list) -> dict:
    """测试单个模型的处理速度"""
    print(f"\n{'='*70}")
    print(f"测试模型: {model_name}")
    print(f"{'='*70}")
    
    try:
        parser = LLMParser(llm_type='ollama', model=model_name)
        
        total_time = 0
        success_count = 0
        results = []
        
        for i, raw_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] 处理案例: {raw_case.raw_title[:50]}...")
            
            start_time = time.time()
            try:
                result = parser.parse_case(raw_case.raw_content)
                end_time = time.time()
                
                process_time = end_time - start_time
                total_time += process_time
                success_count += 1
                
                quality_score = result.get('quality_score', 0)
                
                print(f"  ✓ 处理成功")
                print(f"    耗时: {process_time:.2f}秒")
                print(f"    质量分数: {quality_score:.1f}")
                
                results.append({
                    'case_id': raw_case.raw_id,
                    'process_time': process_time,
                    'quality_score': quality_score,
                    'success': True
                })
                
            except Exception as e:
                end_time = time.time()
                process_time = end_time - start_time
                total_time += process_time
                
                print(f"  ✗ 处理失败: {e}")
                print(f"    耗时: {process_time:.2f}秒")
                
                results.append({
                    'case_id': raw_case.raw_id,
                    'process_time': process_time,
                    'success': False,
                    'error': str(e)
                })
        
        avg_time = total_time / len(test_cases) if test_cases else 0
        success_rate = success_count / len(test_cases) * 100 if test_cases else 0
        
        avg_quality = 0
        if success_count > 0:
            quality_scores = [r['quality_score'] for r in results if r.get('success')]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        print(f"\n模型 {model_name} 测试结果:")
        print(f"  平均处理时间: {avg_time:.2f}秒")
        print(f"  成功率: {success_rate:.1f}%")
        print(f"  平均质量分数: {avg_quality:.1f}")
        
        return {
            'model': model_name,
            'avg_time': avg_time,
            'success_rate': success_rate,
            'avg_quality': avg_quality,
            'total_time': total_time,
            'success_count': success_count,
            'results': results
        }
        
    except Exception as e:
        print(f"\n✗ 模型 {model_name} 初始化失败: {e}")
        return {
            'model': model_name,
            'error': str(e),
            'success': False
        }


def main():
    """主函数"""
    print("\n" + "="*70)
    print(" "*20 + "LLM模型性能测试")
    print("="*70)
    
    print(f"\n将测试以下模型: {', '.join(MODELS_TO_TEST)}")
    print(f"每个模型测试 {TEST_CASE_COUNT} 个案例")
    
    print("\n获取测试案例...")
    test_cases = list(RawCase.objects.filter(status='pending')[:TEST_CASE_COUNT])
    
    if not test_cases:
        print("✗ 没有找到待处理的案例")
        return
    
    print(f"✓ 获取到 {len(test_cases)} 个测试案例")
    
    all_results = []
    
    for model_name in MODELS_TO_TEST:
        result = test_model_speed(model_name, test_cases)
        all_results.append(result)
        
        time.sleep(5)
    
    print("\n" + "="*70)
    print(" "*25 + "性能对比总结")
    print("="*70)
    
    print("\n模型性能排名（按平均处理时间）:")
    print("-" * 70)
    print(f"{'模型':<20} {'平均时间(秒)':<15} {'成功率(%)':<12} {'平均质量':<12}")
    print("-" * 70)
    
    successful_results = [r for r in all_results if r.get('success_count', 0) > 0]
    successful_results.sort(key=lambda x: x['avg_time'])
    
    for i, result in enumerate(successful_results, 1):
        print(f"{i}. {result['model']:<18} {result['avg_time']:<15.2f} "
              f"{result['success_rate']:<12.1f} {result['avg_quality']:<12.1f}")
    
    if successful_results:
        best_model = successful_results[0]
        print(f"\n推荐模型: {best_model['model']}")
        print(f"  平均处理时间: {best_model['avg_time']:.2f}秒")
        print(f"  成功率: {best_model['success_rate']:.1f}%")
        print(f"  平均质量分数: {best_model['avg_quality']:.1f}")
        
        if best_model['avg_time'] < 60:
            speedup = 180 / best_model['avg_time']
            print(f"\n相比当前模型(qwen:1.8b, ~180秒), 速度提升: {speedup:.1f}倍")
    
    print("\n" + "="*70)
    print("测试完成！")
    print("="*70)


if __name__ == '__main__':
    main()