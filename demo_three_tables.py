#!/usr/bin/env python3
"""
三表结构演示脚本
展示完整的案例获取和处理流程
"""
import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
django.setup()

from cases.models import RawCase, TrainingCase, TestCase


def show_banner():
    """显示横幅"""
    print("\n" + "="*70)
    print(" "*20 + "Linux内核案例自动分析系统")
    print(" "*25 + "三表结构演示")
    print("="*70)


def show_database_status():
    """显示数据库状态"""
    print("\n" + "-"*70)
    print("数据库状态")
    print("-"*70)
    
    # RawCase统计
    raw_total = RawCase.objects.count()
    raw_pending = RawCase.objects.filter(status='pending').count()
    raw_processed = RawCase.objects.filter(status='processed').count()
    raw_low_quality = RawCase.objects.filter(status='low_quality').count()
    raw_failed = RawCase.objects.filter(status='failed').count()
    
    print(f"\n1. RawCase表（原始案例）:")
    print(f"   总数: {raw_total}")
    print(f"   ├─ 待处理: {raw_pending}")
    print(f"   ├─ 已处理: {raw_processed}")
    print(f"   ├─ 低质量: {raw_low_quality}")
    print(f"   └─ 失败: {raw_failed}")
    
    # TrainingCase统计
    training_total = TrainingCase.objects.count()
    print(f"\n2. TrainingCase表（训练数据）:")
    print(f"   总数: {training_total}")
    
    # TestCase统计
    test_total = TestCase.objects.count()
    print(f"\n3. TestCase表（测试数据）:")
    print(f"   总数: {test_total}")
    
    # 质量统计
    if training_total > 0:
        avg_quality = sum(c.quality_score for c in TrainingCase.objects.all()) / training_total
        print(f"\n训练数据平均质量分数: {avg_quality:.2f}")
    
    if test_total > 0:
        avg_quality = sum(c.quality_score for c in TestCase.objects.all()) / test_total
        print(f"测试数据平均质量分数: {avg_quality:.2f}")


def show_workflow():
    """显示工作流程"""
    print("\n" + "-"*70)
    print("工作流程")
    print("-"*70)
    
    print("\n步骤1: 获取原始案例")
    print("  命令: python3 fetch_raw_cases.py --count 10 --sources stackoverflow csdn")
    print("  说明: 从各数据源获取原始案例，存储到RawCase表")
    
    print("\n步骤2: 处理原始案例")
    print("  命令: python3 process_raw_cases.py --batch-size 10")
    print("  说明: 使用本地LLM解析案例，验证质量，分配到训练/测试表")
    
    print("\n步骤3: 查看结果")
    print("  命令: python3 test_three_tables.py")
    print("  说明: 查看数据库统计信息")


def show_quick_start():
    """显示快速开始指南"""
    print("\n" + "-"*70)
    print("快速开始")
    print("-"*70)
    
    print("\n1. 获取10个StackOverflow案例:")
    print("   $ python3 fetch_raw_cases.py --count 10 --sources stackoverflow")
    
    print("\n2. 处理5个原始案例:")
    print("   $ python3 process_raw_cases.py --batch-size 5")
    
    print("\n3. 查看结果:")
    print("   $ python3 test_three_tables.py")
    
    print("\n4. 启动管理界面:")
    print("   $ python3 manage.py createsuperuser")
    print("   $ python3 manage.py runserver")
    print("   访问: http://localhost:8000/admin/")


def show_advanced_usage():
    """显示高级用法"""
    print("\n" + "-"*70)
    print("高级用法")
    print("-"*70)
    
    print("\n1. 持续获取案例（每30分钟一轮）:")
    print("   $ python3 fetch_raw_cases.py --continuous --interval 30")
    
    print("\n2. 处理所有待处理案例:")
    print("   $ python3 process_raw_cases.py --all")
    
    print("\n3. 自定义关键词:")
    print("   $ python3 fetch_raw_cases.py --keywords 'kernel panic' 'kernel oops'")
    
    print("\n4. 指定多个数据源:")
    print("   $ python3 fetch_raw_cases.py --sources stackoverflow csdn zhihu juejin")


def show_sample_data():
    """显示样本数据"""
    print("\n" + "-"*70)
    print("样本数据预览")
    print("-"*70)
    
    # 显示最近的原始案例
    recent_raw = RawCase.objects.order_by('-fetch_time')[:3]
    if recent_raw:
        print("\n最近的原始案例:")
        for i, case in enumerate(recent_raw, 1):
            print(f"  {i}. [{case.get_source_display()}] {case.raw_title[:50]}")
            print(f"     状态: {case.get_status_display()}")
    
    # 显示高质量训练案例
    top_training = TrainingCase.objects.order_by('-quality_score')[:3]
    if top_training:
        print("\n高质量训练案例:")
        for i, case in enumerate(top_training, 1):
            print(f"  {i}. {case.case_id}: {case.title[:50]}")
            print(f"     质量分数: {case.quality_score:.1f}")


def main():
    """主函数"""
    show_banner()
    show_database_status()
    show_workflow()
    show_quick_start()
    show_advanced_usage()
    show_sample_data()
    
    print("\n" + "="*70)
    print("演示完成！")
    print("="*70)
    print()


if __name__ == '__main__':
    main()