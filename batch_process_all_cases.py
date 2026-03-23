#!/usr/bin/env python3
"""
批量处理所有待处理的原始案例
使用本地LLM (qwen2.5:0.5b) 进行解析
"""
import os
import sys
import time

# 设置环境变量
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')

# 导入必要的模块
import django
django.setup()

from cases.models import RawCase
from process_raw_cases import RawCaseProcessor

def main():
    print("=" * 70)
    print("批量处理原始案例 - 使用本地LLM (qwen2.5:0.5b)")
    print("=" * 70)
    print()
    
    # 获取待处理案例数量
    pending_count = RawCase.objects.filter(status='pending').count()
    print(f"待处理案例数量: {pending_count}")
    print()
    
    if pending_count == 0:
        print("✓ 没有待处理的案例")
        return
    
    # 初始化处理器
    processor = RawCaseProcessor(llm_type='ollama', model='qwen2.5:0.5b')
    
    # 批量处理大小
    batch_size = 20
    total_processed = 0
    total_success = 0
    total_failed = 0
    total_low_quality = 0
    
    start_time = time.time()
    
    # 分批处理
    while True:
        # 获取一批待处理案例
        pending_cases = RawCase.objects.filter(status='pending')[:batch_size]
        
        if not pending_cases.exists():
            break
        
        batch_count = pending_cases.count()
        print(f"\n处理批次: {total_processed + 1} - {total_processed + batch_count} / {pending_count}")
        
        # 处理这批案例
        for i, raw_case in enumerate(pending_cases, 1):
            print(f"\n[{i}/{batch_count}] 处理案例 ID={raw_case.raw_id}: {raw_case.raw_title[:50]}...")
            
            try:
                result = processor.process_single_case(raw_case)
                
                if result['success']:
                    if result.get('is_high_quality'):
                        total_success += 1
                        print(f"  ✓ 处理成功 (质量分数: {result.get('quality_score', 0):.1f})")
                    else:
                        total_low_quality += 1
                        print(f"  ⚠ 低质量 (质量分数: {result.get('quality_score', 0):.1f})")
                else:
                    total_failed += 1
                    print(f"  ✗ 处理失败: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                total_failed += 1
                print(f"  ✗ 处理异常: {e}")
        
        total_processed += batch_count
        
        # 更新待处理数量
        pending_count = RawCase.objects.filter(status='pending').count()
        
        # 显示进度
        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / total_processed if total_processed > 0 else 0
        remaining = pending_count
        estimated_time = remaining * avg_time
        
        print(f"\n进度统计:")
        print(f"  - 已处理: {total_processed}")
        print(f"  - 成功: {total_success}")
        print(f"  - 低质量: {total_low_quality}")
        print(f"  - 失败: {total_failed}")
        print(f"  - 平均处理时间: {avg_time:.2f}秒/案例")
        print(f"  - 剩余案例: {remaining}")
        print(f"  - 预计剩余时间: {estimated_time/60:.1f}分钟")
        
        # 短暂延迟，避免过度占用资源
        time.sleep(2)
    
    # 最终统计
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 70)
    print("批量处理完成！")
    print("=" * 70)
    print(f"总处理案例: {total_processed}")
    print(f"成功案例: {total_success}")
    print(f"低质量案例: {total_low_quality}")
    print(f"失败案例: {total_failed}")
    print(f"总耗时: {elapsed_time/60:.1f}分钟")
    print(f"平均处理时间: {elapsed_time/total_processed:.2f}秒/案例" if total_processed > 0 else "N/A")
    print("=" * 70)

if __name__ == "__main__":
    main()