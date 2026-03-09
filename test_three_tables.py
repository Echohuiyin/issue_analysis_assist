#!/usr/bin/env python3
"""
测试三表结构的完整流程
"""
import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
django.setup()

from cases.models import RawCase, TrainingCase, TestCase


def test_database_structure():
    """测试数据库结构"""
    print("="*60)
    print("测试数据库结构")
    print("="*60)
    
    # 测试RawCase表
    print("\n1. RawCase表:")
    print(f"   - 总数: {RawCase.objects.count()}")
    print(f"   - 待处理: {RawCase.objects.filter(status='pending').count()}")
    print(f"   - 已处理: {RawCase.objects.filter(status='processed').count()}")
    print(f"   - 低质量: {RawCase.objects.filter(status='low_quality').count()}")
    print(f"   - 失败: {RawCase.objects.filter(status='failed').count()}")
    
    # 测试TrainingCase表
    print("\n2. TrainingCase表:")
    print(f"   - 总数: {TrainingCase.objects.count()}")
    if TrainingCase.objects.exists():
        avg_quality = sum(c.quality_score for c in TrainingCase.objects.all()) / TrainingCase.objects.count()
        print(f"   - 平均质量分数: {avg_quality:.2f}")
    
    # 测试TestCase表
    print("\n3. TestCase表:")
    print(f"   - 总数: {TestCase.objects.count()}")
    if TestCase.objects.exists():
        avg_quality = sum(c.quality_score for c in TestCase.objects.all()) / TestCase.objects.count()
        print(f"   - 平均质量分数: {avg_quality:.2f}")
    
    print("\n✓ 数据库结构测试完成")


def test_raw_case_creation():
    """测试创建原始案例"""
    print("\n" + "="*60)
    print("测试创建原始案例")
    print("="*60)
    
    import hashlib
    
    # 创建测试数据
    test_content = "这是一个测试的内核案例内容"
    content_hash = hashlib.sha256(test_content.encode()).hexdigest()
    
    # 检查是否已存在
    if RawCase.objects.filter(content_hash=content_hash).exists():
        print("测试案例已存在，跳过创建")
        existing = RawCase.objects.get(content_hash=content_hash)
        print(f"现有案例 ID: {existing.raw_id}")
        return existing
    
    # 创建新案例
    raw_case = RawCase.objects.create(
        source='stackoverflow',
        source_id='12345',
        url='https://stackoverflow.com/questions/12345/test',
        raw_title='Test kernel panic case',
        raw_content=test_content,
        raw_html='<p>Test kernel panic case</p>',
        content_hash=content_hash,
        status='pending',
    )
    
    print(f"✓ 创建成功，ID: {raw_case.raw_id}")
    print(f"  - 来源: {raw_case.get_source_display()}")
    print(f"  - 标题: {raw_case.raw_title}")
    print(f"  - 状态: {raw_case.get_status_display()}")
    
    return raw_case


def test_workflow():
    """测试完整工作流程"""
    print("\n" + "="*60)
    print("测试完整工作流程")
    print("="*60)
    
    print("\n步骤1: 获取原始案例")
    print("  运行命令: python3 fetch_raw_cases.py --count 5")
    
    print("\n步骤2: 处理原始案例")
    print("  运行命令: python3 process_raw_cases.py --batch-size 5")
    
    print("\n步骤3: 查看结果")
    print("  - 原始案例: RawCase表")
    print("  - 训练数据: TrainingCase表")
    print("  - 测试数据: TestCase表")
    
    print("\n✓ 工作流程说明完成")


def show_usage():
    """显示使用说明"""
    print("\n" + "="*60)
    print("使用说明")
    print("="*60)
    
    print("\n1. 获取原始案例:")
    print("   python3 fetch_raw_cases.py --count 10 --sources stackoverflow csdn")
    print("   python3 fetch_raw_cases.py --continuous --interval 30  # 持续运行")
    
    print("\n2. 处理原始案例:")
    print("   python3 process_raw_cases.py --batch-size 10")
    print("   python3 process_raw_cases.py --all  # 处理所有待处理案例")
    
    print("\n3. 查看统计:")
    print("   python3 test_three_tables.py")
    
    print("\n4. Django管理界面:")
    print("   python3 manage.py createsuperuser  # 创建管理员")
    print("   python3 manage.py runserver        # 启动服务")
    print("   访问: http://localhost:8000/admin/")


def main():
    """主函数"""
    print("\n" + "#"*60)
    print("# 三表结构测试")
    print("#"*60)
    
    # 测试数据库结构
    test_database_structure()
    
    # 测试创建原始案例
    test_raw_case_creation()
    
    # 显示工作流程
    test_workflow()
    
    # 显示使用说明
    show_usage()
    
    print("\n" + "#"*60)
    print("# 测试完成")
    print("#"*60)


if __name__ == '__main__':
    main()